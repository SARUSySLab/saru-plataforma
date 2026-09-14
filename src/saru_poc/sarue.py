"""Sarue, o assistente de IA do SARU (fases 9 e 12 do plano de integracao).

Nome definido pelo Lucas em 29/08, pra nao confundir com SARU, que e o sistema.

**Decisao (Lucas delegou, 29/08): a saida e TEXTO LIVRE, nao JSON nem tool
use.** O que o Sarue emite e prosa pra um humano ler no box, entre uma bateria
e outra. Exigir JSON acrescentaria um modo de falha (parse) sem entregar nada:
ninguem consome esse texto por programa.

A estrutura fica do outro lado da chamada. **O modelo nunca produz numero.** Ele
recebe os numeros ja calculados pelo pipeline (a base de fatos) e narra. E a
mesma doutrina que tirou o placar de 0 a 100 do produto: numero sem regua e
numero inventado, e um LLM inventa com fluencia. `conferir_numeros` abaixo
transforma isso de intencao em verificacao.

O que o Sarue NAO faz:

- **Nao le o Parquet.** A base de fatos vem do relatorio da etapa 7, que ja e o
  recorte curado. Dar a serie bruta pro modelo seria pedir pra ele agregar, que
  e exatamente o que ele faz mal.
- **Nao inventa contexto ausente.** Campo faltando entra na base como
  "não informado", nunca some. Sumir vira default silencioso, o B2 no prompt.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

import httpx

from .config import CONFIG

URL = "https://openrouter.ai/api/v1/chat/completions"

SISTEMA = """Você é o Saruê, assistente de engenharia de pista do sistema SARU.

Fala com piloto amador e engenheiro de pista, em português do Brasil, direto e
curto. Sem floreio, sem motivação, sem "parabéns pelo progresso".

REGRAS DURAS:

1. Você NUNCA inventa número. Todo tempo, temperatura, pressão, distância e
   velocidade que aparecer na sua resposta tem que estar na BASE DE FATOS que
   veio junto. Se o número não está lá, você não tem esse número, e diz isso.
2. Quando um dado está marcado como indisponível ou não informado, você diz que
   falta, e diz o que ele mudaria. Não preenche com suposição.
3. Você fala de trecho de pista pelo nome que está na base. Não cita curva que
   não aparece na base, mesmo que conheça a pista.
4. Máximo de 5 frases. Isso é lido no box, entre duas baterias.
5. Não usa travessão em nenhuma hipótese. Use vírgula, dois-pontos ou ponto.
"""


class SarueIndisponivel(RuntimeError):
    """Sem chave configurada, ou a chamada falhou. Quem chama decide o que dizer."""


def _numeros(texto: str) -> set[str]:
    """Numeros com significado, normalizados. Ignora inteiro de 1 ou 2 digitos.

    Ordinal ("3 pontos", "volta 7", "5 frases") e contagem, nao medida, e
    barrar isso encheria de falso positivo. O que importa conferir e medida:
    1:12.340, 27.5, 3220.
    """
    achados = re.findall(r"\d+(?:[:.,]\d+)+|\d{3,}", texto)
    return {a.replace(",", ".") for a in achados}


def conferir_numeros(resposta: str, base: dict[str, Any]) -> list[str]:
    """Numeros que a resposta afirma e a base nao sustenta.

    Guardrail em CODIGO, nao no prompt: instrucao de sistema e pedido, e um
    pedido nao e uma garantia. Comparacao por substring no JSON da base, que e
    grosseira de proposito, porque o objetivo e pegar alucinacao de ordem de
    grandeza ("você perdeu 4.2s na Curva 3" numa sessao onde a maior perda foi
    0.4s), nao auditar arredondamento.
    """
    achatada = json.dumps(base, ensure_ascii=False, default=str)
    da_base = _numeros(achatada)
    suspeitos = []
    for n in _numeros(resposta):
        if n in da_base:
            continue
        # tolera arredondamento: 27.53 na base sustenta 27.5 na resposta
        if any(b.startswith(n) or n.startswith(b) for b in da_base):
            continue
        suspeitos.append(n)
    return suspeitos


def montar_base(relatorio: dict[str, Any], contextos: list[dict[str, Any]]) -> dict[str, Any]:
    """A base de fatos: o recorte do relatorio que cabe num prompt.

    Nao e o relatorio inteiro. `n3.canais` e as series de amostra ficam de fora
    porque sao milhares de pontos que o modelo nao consegue agregar e nos ja
    agregamos. Entra o que responde as tres perguntas do funil, mais o contexto
    atual e o anterior, que e o que a fase 9 pede pro aviso periodico.
    """

    def talvez(bloco: Any, chave: str) -> Any:
        if isinstance(bloco, dict) and bloco.get("disponivel") is False:
            return {"indisponivel": True, "motivo": bloco.get("motivo"), "explicacao": bloco.get("texto")}
        return bloco.get(chave) if isinstance(bloco, dict) else None

    def sem_nan(x: Any) -> Any:
        # float nao-finito (NaN/inf) passa pelo json.dumps do Python mas o
        # Postgres rejeita no jsonb, e o insert do turno vira 500 na cara do
        # piloto (medido em producao em 29/08, NaN vindo de canal cru). Na
        # base de fatos, nao-finito significa "nao medido": vira None aqui,
        # na borda, pra classe inteira de erro deixar de existir.
        if isinstance(x, float) and not math.isfinite(x):
            return None
        if isinstance(x, dict):
            return {k: sem_nan(v) for k, v in x.items()}
        if isinstance(x, list):
            return [sem_nan(v) for v in x]
        return x

    melhor = relatorio.get("n0", {}).get("melhor_volta", {})
    atual = contextos[0] if contextos else None
    anterior = contextos[1] if len(contextos) > 1 else None

    return sem_nan({
        "pista": relatorio.get("layout"),
        "como_a_pista_foi_resolvida": relatorio.get("resolucao_pista"),
        "melhor_volta": melhor,
        "maiores_perdas": talvez(relatorio.get("n0", {}).get("perdas_top3", {}), "itens"),
        "voltas": relatorio.get("n1", {}).get("voltas"),
        "consumo": relatorio.get("n1", {}).get("consumo"),
        "perdas_por_curva": talvez(relatorio.get("n2", {}).get("por_curva", {}), "itens"),
        "contexto_atual": atual or "não informado",
        "contexto_anterior": anterior or "não há registro anterior",
        "setup": relatorio.get("contexto", {}).get("setup") or "não informado",
    })


def _chamar(mensagens: list[dict[str, str]]) -> str:
    if not CONFIG.openrouter_key:
        raise SarueIndisponivel("SARU_OPENROUTER_KEY não está configurada")
    try:
        r = httpx.post(
            URL,
            headers={
                "Authorization": f"Bearer {CONFIG.openrouter_key}",
                "Content-Type": "application/json",
                # o OpenRouter usa isto pra atribuir a chamada; nao e obrigatorio.
                # Sem acento de proposito: header HTTP e ASCII, e "Saruê" aqui
                # derrubava a chamada inteira com UnicodeEncodeError no httpx.
                "X-Title": "SARU PoC, Sarue",
            },
            json={"model": CONFIG.openrouter_modelo, "messages": mensagens, "temperature": 0.3},
            timeout=60.0,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except httpx.HTTPError as e:
        raise SarueIndisponivel(f"OpenRouter não respondeu: {e}") from e
    except (KeyError, IndexError) as e:
        raise SarueIndisponivel(f"resposta do OpenRouter fora do formato esperado: {e}") from e


def _com_guardrail(mensagens: list[dict[str, str]], base: dict[str, Any]) -> tuple[str, list[str]]:
    """Chama, confere, e da UMA segunda chance apontando o erro.

    Uma so: se errar duas vezes com o problema nomeado, o texto sai com a
    ressalva em vez de entrar em loop. Devolver texto marcado como
    nao-conferido e melhor do que nao devolver nada, e muito melhor do que
    devolver numero inventado sem marca.
    """
    resposta = _chamar(mensagens)
    suspeitos = conferir_numeros(resposta, base)
    if not suspeitos:
        return resposta, []
    segunda = [
        *mensagens,
        {"role": "assistant", "content": resposta},
        {
            "role": "user",
            "content": (
                f"Estes números não estão na base de fatos: {', '.join(suspeitos)}. "
                "Reescreva usando apenas números que estão na base, ou diga que o dado falta."
            ),
        },
    ]
    resposta = _chamar(segunda)
    return resposta, conferir_numeros(resposta, base)


def responder(pergunta: str, base: dict[str, Any]) -> tuple[str, list[str]]:
    """Um turno de conversa. Devolve (texto, numeros_nao_conferidos)."""
    return _com_guardrail(
        [
            {"role": "system", "content": SISTEMA},
            {
                "role": "user",
                "content": (
                    f"BASE DE FATOS (JSON):\n{json.dumps(base, ensure_ascii=False, default=str)}\n\n"
                    f"PERGUNTA DO PILOTO: {pergunta}"
                ),
            },
        ],
        base,
    )


def gerar_aviso(base: dict[str, Any]) -> tuple[str, list[str]]:
    """O aviso do ciclo periodico: ninguem perguntou nada.

    A instrucao e diferente da conversa de proposito. Sem pergunta, o modelo
    tende a resumir tudo; o que serve no box e UMA coisa acionavel antes da
    proxima bateria.
    """
    return _com_guardrail(
        [
            {"role": "system", "content": SISTEMA},
            {
                "role": "user",
                "content": (
                    f"BASE DE FATOS (JSON):\n{json.dumps(base, ensure_ascii=False, default=str)}\n\n"
                    "Ninguém perguntou nada. Você está olhando a sessão e vai falar sozinho, "
                    "uma vez, antes da próxima bateria. Diga UMA coisa acionável: onde há tempo "
                    "para pegar, ou o que mudou no contexto desde o registro anterior e o que "
                    "isso implica. Se o que mais importa é um dado que está faltando, diga isso "
                    "e por que ele muda a leitura."
                ),
            },
        ],
        base,
    )
