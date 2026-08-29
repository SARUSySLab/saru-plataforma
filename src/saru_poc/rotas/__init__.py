"""Rotas HTTP, uma por area.

Ficam separadas de `api.py` porque a camada HTTP cresceu de 6 pra ~30 rotas na
integracao do front, e um arquivo so viraria o `SaDashboard.tsx` do backend.
`api.py` continua sendo o unico lugar que monta o app e decide o que e publico.
"""
