/**
 * Data e hora em dois campos, com a data SEMPRE em dia/mes/ano.
 *
 * Por que nao `<input type="date">` puro: ele exibe no formato do idioma do
 * NAVEGADOR, entao numa maquina em ingles a mesma tela mostra mes/dia/ano e o
 * engenheiro le 03/09 como 9 de marco. Pedido do Lucas em 30/08: formato
 * brasileiro garantido, e hora em campo proprio.
 *
 * O visivel e um campo de texto com mascara, que nao depende de locale. O
 * calendario nativo continua alcancavel pelo botao ao lado, que abre um
 * `<input type="date">` escondido e sincronizado: quem prefere digitar digita,
 * quem prefere clicar clica.
 *
 * FUSO: o formulario continua enviando o mesmo `YYYY-MM-DDTHH:mm` que o
 * `datetime-local` enviava, em horario LOCAL, sem sufixo de zona. Quem
 * converte para UTC e o backend, como ja fazia. Montar aqui um `Date` e
 * chamar `toISOString` mudaria o dia perto da meia-noite, e uma bateria de
 * sabado nasceria na sexta.
 */

import { useEffect, useRef, useState } from "react";

interface Props {
  /** Mesmo `name` que o `datetime-local` tinha: o submit nao muda. */
  name: string;
  /** Valor inicial em `YYYY-MM-DDTHH:mm` (o que `paraInputDatetime` devolve). */
  defaultValue?: string;
  required?: boolean;
  /** Rotulo da data. O da hora e derivado dele. */
  rotulo?: string;
}

const soDigitos = (t: string) => t.replace(/\D/g, "");

/** Mascara dd/mm/aaaa aplicada enquanto digita, sem brigar com o apagar. */
function mascararData(bruto: string): string {
  const d = soDigitos(bruto).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
}

function mascararHora(bruto: string): string {
  const d = soDigitos(bruto).slice(0, 4);
  if (d.length <= 2) return d;
  return `${d.slice(0, 2)}:${d.slice(2)}`;
}

/** `YYYY-MM-DD` vira `dd/mm/aaaa`. Sem `Date` no meio, para nao passear por fuso. */
const isoParaBr = (iso: string) => {
  const [a, m, d] = iso.split("-");
  return a && m && d ? `${d}/${m}/${a}` : "";
};

/** `dd/mm/aaaa` vira `YYYY-MM-DD`, ou vazio se ainda esta incompleto. */
function brParaIso(br: string): string {
  const d = soDigitos(br);
  if (d.length !== 8) return "";
  const dia = d.slice(0, 2);
  const mes = d.slice(2, 4);
  const ano = d.slice(4);
  return `${ano}-${mes}-${dia}`;
}

/** Data existe de verdade? Recusa 31/02 e mes 13, que a mascara aceitaria. */
function dataPlausivel(iso: string): boolean {
  if (!iso) return false;
  const [a, m, d] = iso.split("-").map(Number);
  if (m < 1 || m > 12 || d < 1) return false;
  // dia zero do mes seguinte e o ultimo dia do mes atual, sem tabela de meses
  return d <= new Date(a, m, 0).getDate();
}

export function CampoDataHora({ name, defaultValue = "", required, rotulo = "Data" }: Props) {
  const [iso, hhmm] = defaultValue.includes("T") ? defaultValue.split("T") : ["", ""];
  const [data, setData] = useState(isoParaBr(iso));
  const [hora, setHora] = useState(hhmm.slice(0, 5));
  const calendario = useRef<HTMLInputElement>(null);

  const isoData = brParaIso(data);
  const valido = !data || dataPlausivel(isoData);
  // O campo oculto e quem o formulario le: mantem o contrato do submit.
  const valor = isoData && hora ? `${isoData}T${hora}` : "";

  useEffect(() => {
    if (calendario.current) calendario.current.value = isoData;
  }, [isoData]);

  return (
    <span className="campo-data-hora">
      <span className="cdh-parte">
        <span className="cdh-rotulo">{rotulo}</span>
        <span className="cdh-entrada">
          <input
            type="text"
            inputMode="numeric"
            placeholder="dd/mm/aaaa"
            value={data}
            aria-invalid={!valido}
            onChange={(e) => setData(mascararData(e.target.value))}
          />
          <button
            type="button"
            className="cdh-calendario"
            aria-label="abrir calendário"
            onClick={() => calendario.current?.showPicker?.()}
          >
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"
              strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="3" y="5" width="18" height="16" rx="2" />
              <path d="M3 10h18M8 3v4M16 3v4" />
            </svg>
          </button>
          {/* nativo escondido: existe so pelo calendario, nunca pelo texto */}
          <input
            ref={calendario}
            type="date"
            className="cdh-oculto"
            tabIndex={-1}
            aria-hidden="true"
            onChange={(e) => setData(isoParaBr(e.target.value))}
          />
        </span>
      </span>
      <span className="cdh-parte cdh-hora">
        <span className="cdh-rotulo">Hora</span>
        <input
          type="text"
          inputMode="numeric"
          placeholder="hh:mm"
          value={hora}
          onChange={(e) => setHora(mascararHora(e.target.value))}
        />
      </span>
      <input type="hidden" name={name} value={valor} required={required} />
      {!valido && <span className="cdh-erro">data inexistente</span>}
    </span>
  );
}
