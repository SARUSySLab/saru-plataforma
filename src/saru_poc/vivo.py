"""Ingestao ao vivo: o carro na pista alimentando o pit wall.

DESENHO, decidido pelo Lucas em 30/08 depois de ver as opcoes:

- Transporte HTTP em lote curto (cerca de 250 ms de amostras por POST), e nao
  WebSocket nem MQTT. Motivo: 4G de autodromo cai o tempo todo, e num lote HTTP
  reenviar e simplesmente repetir o POST. Conexao longa exigiria reconexao,
  backpressure e ordenacao escritos por nos.
- Deduplicacao por (veiculo, sessao, seq): o gateway repete quando nao ve
  resposta, e repetir nao pode duplicar amostra nem furar contagem.
- ARQUIVO VENCE RADIO. O mesmo trecho chega ate tres vezes: ao vivo, pelo
  cartao do gateway e por upload manual. O ao vivo e provisorio por natureza
  (tem buraco de cobertura, pode vir decimado), entao ele fica marcado como tal
  e o reprocessamento futuro sabe o que pode descartar.
- Amostra NAO entra em tabela do Postgres. A regra do projeto (migration 005) e
  que amostra vive em Parquet e o banco guarda ponteiro. Aqui o que sobrevive a
  restart e so o registro do lote; a amostra em si fica num buffer em memoria,
  que e o que o painel le.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

# Janela do buffer quente. O pit wall mostra a volta em curso e os ultimos
# segundos de canal; guardar mais do que isto seria pagar memoria por dado que
# ninguem olha e que o Parquet vai guardar direito no fim da sessao.
JANELA_S = 300.0

# Acima disto o dado para de ser "ao vivo" e vira historico: a tela declara a
# idade em vez de mostrar numero velho como se fosse agora.
SILENCIO_S = 15.0


def _sha256(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def gerar_token() -> tuple[str, str]:
    """Token do gateway em claro e o hash que vai pro banco.

    O claro so existe nesta resposta, igual ao token de maquina: dump de banco
    vazado nao pode virar credencial de ingestao.
    """
    token = secrets.token_urlsafe(32)
    return token, _sha256(token)


@dataclass
class _Amostra:
    t_s: float
    canais: dict[str, float]


@dataclass
class _Estado:
    """O que o painel precisa saber de um carro, sem tocar o banco."""

    amostras: list[_Amostra] = field(default_factory=list)
    ultimo_recebido: float = 0.0
    ultima_seq: int | None = None
    fora_de_ordem: int = 0


class BufferVivo:
    """Ultimos minutos de cada carro, em memoria, com trava.

    Uvicorn atende requisicao concorrente: dois lotes do mesmo carro podem
    chegar ao mesmo tempo quando a rede engasga e o gateway reenvia. Sem trava,
    a lista seria mutada por dois lados e a leitura do painel pegaria estado
    pela metade.
    """

    def __init__(self, janela_s: float = JANELA_S) -> None:
        self._janela_s = janela_s
        self._por_veiculo: dict[str, _Estado] = {}
        self._trava = threading.Lock()

    def registrar(self, veiculo_id: str, seq: int, amostras: list[dict[str, Any]]) -> dict[str, Any]:
        agora = time.monotonic()
        with self._trava:
            estado = self._por_veiculo.setdefault(veiculo_id, _Estado())
            # Sequencia fora de ordem NAO e descartada: em rede ruim o pacote
            # atrasado ainda carrega amostra boa, e jogar fora abriria buraco no
            # traco por um problema de transporte. Ela e contada e declarada, e
            # a ordenacao por t_s resolve a apresentacao.
            if estado.ultima_seq is not None and seq < estado.ultima_seq:
                estado.fora_de_ordem += 1
            estado.ultima_seq = max(seq, estado.ultima_seq or seq)
            estado.ultimo_recebido = agora
            for a in amostras:
                estado.amostras.append(_Amostra(float(a["t_s"]), dict(a.get("canais") or {})))
            estado.amostras.sort(key=lambda x: x.t_s)
            self._podar(estado)
            return {"amostras_no_buffer": len(estado.amostras), "fora_de_ordem": estado.fora_de_ordem}

    def _podar(self, estado: _Estado) -> None:
        if not estado.amostras:
            return
        corte = estado.amostras[-1].t_s - self._janela_s
        if corte > 0:
            estado.amostras = [a for a in estado.amostras if a.t_s >= corte]

    def estado(self, veiculo_id: str) -> dict[str, Any] | None:
        with self._trava:
            e = self._por_veiculo.get(veiculo_id)
            if e is None:
                return None
            idade = time.monotonic() - e.ultimo_recebido
            canais = sorted({c for a in e.amostras[-50:] for c in a.canais})
            return {
                # Idade declarada em vez de "parado": quem le decide o que
                # fazer. Carro sem pacote pode estar no box, sem cobertura ou
                # com gateway morto, e a tela nao tem como saber qual dos tres.
                "idade_s": round(idade, 1),
                "ao_vivo": idade <= SILENCIO_S,
                "amostras": len(e.amostras),
                "canais": canais,
                "ultima_seq": e.ultima_seq,
                "fora_de_ordem": e.fora_de_ordem,
                "t_ultimo_s": e.amostras[-1].t_s if e.amostras else None,
            }

    def limpar(self) -> None:
        """So para teste: zera o estado entre casos."""
        with self._trava:
            self._por_veiculo.clear()


BUFFER = BufferVivo()


def autenticar_gateway(conn, token: str) -> dict[str, Any] | None:
    """Gateway dono do token, ou None. Compara por hash, nunca pelo claro."""
    linha = conn.execute(
        """select g.id, g.veiculo_id, v.dono_id, v.apelido
             from gateway g join veiculo v on v.id = g.veiculo_id
            where g.token_sha256 = %s""",
        (_sha256(token),),
    ).fetchone()
    if linha is None:
        return None
    return {
        "gateway_id": linha[0],
        "veiculo_id": linha[1],
        "dono_id": linha[2],
        "apelido": linha[3],
    }


def receber_lote(
    conn, veiculo_id: UUID, gateway_id: UUID, sessao: str | None, seq: int,
    amostras: list[dict[str, Any]],
) -> dict[str, Any]:
    """Registra o lote e devolve o efeito. Reenvio responde sucesso, nao erro.

    Idempotencia real: o unique de (veiculo, sessao, seq) recusa o duplicado no
    banco, e nesse caso o buffer NAO recebe as amostras de novo. Se a checagem
    ficasse so em memoria, um restart faria o mesmo lote entrar duas vezes.
    """
    ts = [float(a["t_s"]) for a in amostras] if amostras else []
    linha = conn.execute(
        """insert into vivo_lote (veiculo_id, sessao_txt, seq, amostras, t_inicio_s, t_fim_s)
           values (%s, %s, %s, %s, %s, %s)
           on conflict (veiculo_id, sessao_txt, seq) do nothing
           returning id""",
        (veiculo_id, sessao or "", seq, len(amostras), min(ts) if ts else None, max(ts) if ts else None),
    ).fetchone()
    if linha is None:
        return {"aceito": True, "novo": False, "motivo": "lote repetido, ja recebido antes"}

    conn.execute("update gateway set ultimo_pacote_em = now() where id = %s", (gateway_id,))
    efeito = BUFFER.registrar(str(veiculo_id), seq, amostras)
    return {"aceito": True, "novo": True, **efeito}


def painel_do_dono(conn, dono_id: UUID) -> list[dict[str, Any]]:
    """Um item por veiculo do dono, com a idade do dado ao vivo.

    Veiculo sem nenhum pacote aparece assim mesmo, com `ao_vivo` falso: sumir
    da lista esconderia justamente o carro que precisa de atencao.
    """
    linhas = conn.execute(
        """select v.id, v.numero, v.apelido, v.modelo_txt, g.ultimo_pacote_em
             from veiculo v left join gateway g on g.veiculo_id = v.id
            where v.dono_id = %s order by v.apelido""",
        (dono_id,),
    ).fetchall()
    saida = []
    for vid, numero, apelido, modelo, ultimo in linhas:
        estado = BUFFER.estado(str(vid)) or {
            "idade_s": None,
            "ao_vivo": False,
            "amostras": 0,
            "canais": [],
            "ultima_seq": None,
            "fora_de_ordem": 0,
            "t_ultimo_s": None,
        }
        saida.append({
            "veiculo_id": str(vid),
            "numero": numero,
            "apelido": apelido,
            "modelo": modelo,
            "ultimo_pacote_em": ultimo.isoformat() if ultimo else None,
            **estado,
        })
    return saida
