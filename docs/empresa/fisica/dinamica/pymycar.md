---
titulo: "pyMyCar"
data: "2026-07-07"
origem: "_arquivo/saru-KB/90_tools/pyMyCar.md"
status: "vigente"
area: "dinamica_veicular"
---

# pyMyCar

Pacote Python open-source para análise de dinâmica veicular.

## O que é

Framework aberto e extensível para análise de dinâmica veicular, voltado a engenheiros, pesquisadores, estudantes e entusiastas.

## Capacidades atuais (v0.1)

| Módulo | Estado |
|---|---|
| Cinemática de suspensão double wishbone | ✅ |
| Cinemática de suspensão multi-link | ✅ |
| Simulações dinâmicas post-rig | ✅ |
| Ferramentas de cinemática de moto (inicial) | ✅ |

## Estrutura da documentação

- **Getting Started** → Authors & Citation, Repository Structure, Installation
- **Theory** → base teórica dos modelos
- **Examples** → CAD-style car/motorbike viz, suspension kinematics, vertical models, motorcycle kinematics
- **API Reference** → referência completa
- **Extras** → notas de desenvolvedor, contributing guidelines

## Detalhes técnicos

- Versão atual: `0.1`
- Docs: Sphinx 8.1.3 + PyData Sphinx Theme 0.18.0
- Hospedagem docs: ReadTheDocs
- Linguagem: Python
- Repositório: público, open-source

## Relevância para SARU

- Overlap direto com `SARU_SUSP` (cinemática de suspensão) e `SARU_Chassis_Python`
- Pode servir como referência de arquitetura para módulos de suspensão
- Abordagem open/extensível alinhada com visão SARU
- Ponto de comparação/benchmark para implementações próprias

## Links

- GitHub: https://github.com/CastillonMiguel/pymycar
- Docs: https://pymycar.readthedocs.io/en/latest/
- Contributing: https://github.com/CastillonMiguel/pymycar/blob/main/CONTRIBUTING.rst

## Notas

- Projeto ainda em estágio inicial (v0.1), desenvolvimento ativo
- Aceita contribuições, potencial para colaboração futura
- Descoberto via LinkedIn post (2026-06-15)
