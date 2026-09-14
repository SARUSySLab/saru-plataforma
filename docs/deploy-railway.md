# Deploy no Railway

Runbook pra subir a PoC do SARU no Railway. Cobre topologia, variaveis, volume
de dado e o passo a passo via CLI. Nao cobre CI/CD automatico: aqui e deploy
manual, `railway up` na mao.

## Topologia: dois servicos, uma origem HTTP

O projeto tem **dois** servicos no Railway:

1. **Postgres** (plugin gerenciado do Railway).
2. **app**: um unico container (o `Dockerfile` na raiz) que serve a API
   (`/api/*`) e o front estatico (`web/dist`) na **mesma origem**.

Nao existe um terceiro servico so pra frontend. A razao e o cookie de sessao:
a auth da PoC usa cookie `httpOnly` (ver `src/saru_poc/auth.py`), e cookie
httpOnly em setup cross-origin exige CORS com credenciais, `SameSite`
ajustado e dominio compartilhado, tudo isso pra resolver um problema que some
sozinho se API e front saem do mesmo host. `src/saru_poc/api.py` ja monta o
`web/dist` como estatico (linha ~427) exatamente pra isso: o Dockerfile builda
o front no stage 1 e copia o resultado pro lugar que a API espera. Um servico
so, uma origem, zero CORS pra configurar.

## O filesystem do Railway e efemero: por isso o Volume

Todo container do Railway perde o disco local a cada redeploy (novo deploy,
restart, scale). A PoC guarda a serie de telemetria (o que vira Parquet) fora
do Postgres de proposito, ver `SARU_DATA_ROOT` em `src/saru_poc/config.py`.
Sem um Volume persistente montado nesse caminho, toda amostra enviada some no
proximo `railway up`, silenciosamente, o piloto so descobre quando for olhar
o grafico de novo.

Por isso: cria um **Railway Volume** montado em `/data` no servico `app`, e
`SARU_DATA_ROOT=/data` aponta pra ele. O Postgres continua guardando so
metadado e o ponteiro pro Parquet (`serie_amostral`), o volume guarda o dado
colunar em si.

## Pre-requisitos

- Railway CLI instalado e logado: `npm i -g @railway/cli` (ou `brew install railway`).
- Conta Railway com um projeto ja criado ou pronto pra criar.
- `SARU_OPENROUTER_KEY` valida (chave do Sarue, o assistente de IA), se o
  assistente for ficar ativo em producao.

## Passo a passo

### 1. Login e vinculo do projeto

```bash
railway login
railway init          # cria um projeto novo, ou
railway link          # vincula a um projeto Railway ja existente
```

### 2. Sobe o Postgres

```bash
railway add --plugin postgresql
```

Isso cria o servico `Postgres` no projeto e expoe as variaveis de referencia
padrao dele (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, e o
`DATABASE_URL` pronto). A API da PoC nao le essas variaveis direto, ela le as
proprias (`SARU_PG_*`, ver `src/saru_poc/config.py`), entao o proximo passo
mapeia uma na outra.

### 3. Cria o Volume pro dado colunar

```bash
railway volume add --mount-path /data
```

Confirma que o volume ficou associado ao servico `app` (nao ao Postgres: o
Postgres tem o proprio volume interno, gerenciado pelo plugin). Se o CLI
perguntar o servico alvo, escolhe `app`.

### 4. Variaveis de ambiente do servico `app`

Lista completa, lida de `src/saru_poc/config.py` e `.env.example`. Roda no
diretorio do servico `app` (ou passa `--service app`):

```bash
# Postgres: mapeia a referencia do plugin pras variaveis que a API le.
railway variables --set "SARU_PG_HOST=\${{Postgres.PGHOST}}"
railway variables --set "SARU_PG_PORT=\${{Postgres.PGPORT}}"
railway variables --set "SARU_PG_DB=\${{Postgres.PGDATABASE}}"
railway variables --set "SARU_PG_USER=\${{Postgres.PGUSER}}"
railway variables --set "SARU_PG_PASSWORD=\${{Postgres.PGPASSWORD}}"

# Dado colunar: o volume montado no passo 3.
railway variables --set "SARU_DATA_ROOT=/data"

# Segredo do JWT de sessao. NUNCA usa o default do repo em producao, gera um de verdade:
railway variables --set "SARU_JWT_SECRET=$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"

# Cookie so viaja em HTTPS (o dominio do Railway ja e HTTPS por padrao).
railway variables --set "SARU_COOKIE_SEGURO=1"

# Liga a checagem de "estamos em producao" (ver abaixo o porque disso importar).
railway variables --set "SARU_AMBIENTE=producao"

# Validacao de contrato de resposta (relatorio.montar/amostras vs contract.ts)
# e barata mas ainda e trabalho por request. Decisao: desliga em producao,
# fica so em dev/CI onde diverge de contrato tem que travar build.
railway variables --set "SARU_VALIDA_CONTRATO=0"

# Sarue (assistente de IA via OpenRouter).
railway variables --set "SARU_OPENROUTER_KEY=<chave real, pegar em https://openrouter.ai/keys>"
railway variables --set "SARU_OPENROUTER_MODELO=anthropic/claude-sonnet-4.5"
```

**Sobre `SARU_JWT_SECRET`: a API recusa subir sem um valor real em
producao.** `src/saru_poc/api.py` checa no import: se `SARU_AMBIENTE=producao`
e o segredo comeca com `dev-inseguro` (o default de dev), levanta
`RuntimeError` e o processo nem chega a escutar porta. Isso e proposital
(decisao do Lucas, comentada no proprio `api.py` e `config.py`): segredo de
assinatura com valor conhecido e publico no repo e o mesmo que nao ter
assinatura nenhuma, e falhar no boot avisa na hora, em vez de alguem forjar
um token de sessao meses depois. Se o deploy cair em crash loop logo no
start, confere `SARU_JWT_SECRET` e `SARU_AMBIENTE` primeiro.

### 5. Deploy

```bash
railway up
```

Isso builda o `Dockerfile` da raiz (dois stages: front node depois API
python) e sobe o container. O `CMD` do Dockerfile roda `saru-poc migrate`
antes do `uvicorn`: as migrations pendentes aplicam a cada boot, e sao no-op
quando o schema ja esta em dia (ver `src/saru_poc/migrate.py`, o sha256 de
cada arquivo fica gravado em `_migrations`). Isso evita o cenario de subir
codigo novo contra schema velho.

### 6. Dominio publico

```bash
railway domain
```

Gera (ou mostra) o dominio `*.up.railway.app` do servico `app`. Se for usar
dominio proprio, configura o CNAME depois com o mesmo comando.

### 7. Smoke test

```bash
curl -s https://<dominio-do-app>/api/saude
# espera: {"ok":true, ...}

curl -s -o /dev/null -w "%{http_code}\n" https://<dominio-do-app>/
# espera: 200, servindo o index.html do front
```

Se `/api/saude` responder mas `/` der 404 ou branco: confere se o stage do
front rodou (`web/dist` populado) e se o `COPY --from=front` no Dockerfile
achou o `dist` no lugar certo. Se `/api/saude` nem responder: `railway logs`
pra ver se o crash foi no `migrate` (schema/conexao Postgres) ou no boot da
API (`SARU_JWT_SECRET`, variavel faltando).

## Checklist rapido

- [ ] Postgres provisionado (`railway add --plugin postgresql`)
- [ ] Volume em `/data` no servico `app`
- [ ] `SARU_PG_*` mapeadas do plugin Postgres
- [ ] `SARU_DATA_ROOT=/data`
- [ ] `SARU_JWT_SECRET` gerado (nao o default do repo)
- [ ] `SARU_COOKIE_SEGURO=1`
- [ ] `SARU_AMBIENTE=producao`
- [ ] `SARU_VALIDA_CONTRATO=0`
- [ ] `SARU_OPENROUTER_KEY` e `SARU_OPENROUTER_MODELO`
- [ ] `railway up` sem crash loop
- [ ] `GET /api/saude` volta `{"ok":true,...}`
- [ ] `GET /` serve o front
