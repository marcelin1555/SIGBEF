# Spec: API REST somente leitura (v1)

Data: 2026-07-10 · Aprovado por: Marcello (abordagem A) · Branch: melhorias-v1.6

## Objetivo

Permitir que outros sistemas da escola (secretaria, sistema acadêmico,
futuro app móvel em modo consulta) leiam dados da biblioteca sem tocar
no banco diretamente. Primeira versão é estritamente somente leitura.

## Restrições de produto (invioláveis)

1. **Zero dependência externa**: implementação 100% biblioteca padrão
   (`http.server`, `json`, `secrets`, `hmac`).
2. **Offline-first opt-in**: nasce desligada (`API_ATIVA=0`); liga em
   Configurações → Integrações, seguindo o padrão de `ISBN_LOOKUP` e
   `EMAIL_AVISOS`. Desligada, o sistema não abre porta nenhuma.
3. Nenhuma rota de escrita nesta versão.

## Arquitetura

- Módulo novo `sigbef/api.py` (~250 linhas):
  - `ThreadingHTTPServer` + handler roteando somente GET.
  - Reusa a camada de negócio existente (`servicos.py`, `reservas.py`);
    a API não contém SQL próprio além do que os serviços oferecem.
  - Concorrência: cada requisição abre conexão própria via `db_cursor`;
    o modo WAL (v1.6) garante leitura simultânea ao balcão/kiosk.
- Configs novas em `CONFIG_PADRAO`:
  - `API_ATIVA` = "0"
  - `API_PORTA` = "8765"
  - `API_TOKEN` = "" (gerado com `secrets.token_urlsafe(32)` na
    primeira ativação; recriável pelo botão "Gerar novo token")

## Autenticação

- Header `Authorization: Bearer <API_TOKEN>`, comparação em tempo
  constante (`hmac.compare_digest`).
- Sem/errado → `401 {"erro": "..."}`.
- Exceção: `/api/v1/ping` responde sem token (healthcheck).
- Servidor escuta em `0.0.0.0` (rede local da escola é o caso de uso);
  a proteção é o token. Cada requisição confere `api_ativa()`: se o
  admin desligar com o servidor de pé, as rotas passam a responder 403.

## Execução (dois modos, um servidor)

1. **Dentro do app**: com `API_ATIVA=1`, o painel sobe a API numa
   thread daemon no boot; o toggle em Configurações liga/desliga na
   hora (start/shutdown do servidor) além de persistir a config.
2. **Headless**: `python sigbef.py --api` roda só o servidor (pra
   deixar num computador-servidor). Exige `API_ATIVA=1`; caso
   contrário orienta a ativar e sai.

## Endpoints v1 (todos GET, JSON UTF-8)

| Rota | Auth | Retorna |
|---|---|---|
| `/api/v1/ping` | não | `{"ok": true, "servico": "SIGBEF", "versao": ...}` |
| `/api/v1/estatisticas` | sim | contagens do painel (livros, exemplares, disponíveis, abertos, atrasados, usuários) |
| `/api/v1/livros?q=&disponiveis=1` | sim | lista do acervo com agregados de disponibilidade |
| `/api/v1/livros/{id}` | sim | detalhes + exemplares (tombo, status) |
| `/api/v1/usuarios/{matricula}/emprestimos` | sim | nome/matrícula/turma, status (pode pegar? multas), empréstimos e reservas ativas |
| `/api/v1/emprestimos/abertos` | sim | circulação atual (com flag de atraso) |

Nunca expostos: senha_hash, e-mail/telefone de usuários, token.

## Erros

- 401 sem/mau token · 403 API desligada · 404 rota ou recurso
  inexistente · 405 método diferente de GET · corpo sempre
  `{"erro": "mensagem em português"}`.
- Logs de acesso do `http.server` silenciados (não poluir console);
  ativação/desativação e regeneração de token entram na auditoria.

## Testes

`tests/test_api.py`: sobe o servidor real em porta efêmera numa thread
e consome com `http.client` (~14 testes): ping sem token, 401/403,
busca de livros, detalhes, 404s, empréstimos por matrícula com multa e
reserva, estatísticas, 405 para POST.

## Documentação

`docs/API.md`: como ativar, exemplos `curl` de cada rota, avisos de
segurança (token = senha; rede local apenas).

## Fora de escopo (v2)

Escrita (renovação/empréstimo), autenticação por usuário final,
paginação, HTTPS nativo (mitigação: rede local + token).
