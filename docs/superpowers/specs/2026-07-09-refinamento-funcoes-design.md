# Design: Refinamento geral das funções do SIGBEF (v1.6.0)

Data: 2026-07-09 · Aprovado por: Marcello ("pode começar") · Branch: `melhorias-v1.6`

## Objetivo

Elevar robustez, experiência de uso, performance e qualidade de código de todo
o `sigbef/` (15 módulos, ~5.500 linhas), sem quebrar o uso em produção no CEFE.
Abordagem escolhida: **fundação primeiro** (testes antes de mexer).

## Invariantes

1. O banco SQLite existente continua funcionando: migrações apenas aditivas
   (`_migrar_schema`), nunca destrutivas.
2. Zero dependência externa nova em runtime (só stdlib: sqlite3, tkinter,
   hashlib, urllib). Testes usam `unittest` da stdlib pelo mesmo motivo.
3. Offline-first preservado: nenhuma função nova pode exigir internet.
4. Nada entra no `main` antes da release automática v1.5.1 (10/07 09:00)
   disparar; o trabalho vive em `melhorias-v1.6` até lá.
5. Commits sem trailer Co-Authored-By.

## Fase 0: Rede de testes

- Diretório `tests/` na raiz, padrão `unittest`, executado com
  `python -m unittest discover -s tests`.
- `tests/base.py` define `SigbefTestCase`: aponta `SIGBEF_DB_PATH` para um
  banco temporário (setado antes de importar `sigbef.database`) e recria o
  banco zerado em cada `setUp` (apaga o arquivo + `init_database()`).
- Módulos cobertos e focos:
  - `test_servicos.py`: cadastrar/editar/excluir livro e usuário, empréstimo
    (limites por perfil, bloqueio por multa/atraso, trava atômica), devolução
    (cálculo de multa com teto), renovação, importação CSV (delimitador,
    encoding, duplicidade de ISBN, linhas inválidas), etiquetas.
  - `test_auth.py`: hash/verificação de senha (formato, senha errada, hash
    corrompido), autenticação por matrícula e por cartão, usuário inativo.
  - `test_database.py`: criação de schema, migração em banco antigo (sem a
    coluna `turma`), get/set de config, auditoria.
  - `test_formato.py`: datas BR (ISO com/sem hora, date, datetime, lixo,
    vazio), reais, status legível.
  - `test_barcode_util.py`: unicidade dos geradores, checksum Code 128
    (valores conhecidos), SVG bem formado, HTML de etiquetas/cartões escapado.
  - `test_isbn_lookup.py`: limpeza de ISBN, extração de ano, fluxo de fontes
    com `_http_json` substituído por stub (sem rede).
- CI: passo `python -m unittest discover -s tests` no
  `.github/workflows/build.yml` antes do PyInstaller, nas 3 plataformas.

## Fase 1: Robustez, performance e qualidade (por módulo)

Subagentes em paralelo apenas em módulos disjuntos; cada lote roda a suíte
completa antes do commit.

- `auth.py`: `hmac.compare_digest` na comparação de hash (tempo constante).
- `database.py`: `PRAGMA journal_mode=WAL` e `busy_timeout` na conexão
  (balcão + kiosk simultâneos sem "database is locked").
- `servicos.py`: validações de entrada faltantes (ano plausível no cadastro
  unitário, quantidade máxima, strings gigantes), mensagens de erro sempre
  acionáveis.
- `ui_selfservice.py`: remover o parâmetro `refoca_apos_erro` (achado do
  ponytail-review): o campo sempre refoca após erro.
- `isbn_lookup.py`: timeout/retry já ok; revisar mensagens.
- Varredura de consistência: todo `except` genérico vira específico onde
  possível; nenhum erro engolido silenciosamente sem auditoria.

## Fase 2: Experiência de uso (por fluxo, liberdade total autorizada)

Percorrer como usuária e melhorar: balcão de empréstimo/devolução, cadastro
de livro/usuário, kiosk, painel e configurações.

- Atalhos: F5 recarrega a lista da seção atual; Ctrl+F foca a busca; Enter
  conclui os diálogos; Esc fecha diálogos.
- Mensagens: erro sempre diz o que fazer em seguida; sucesso sem exclamações.
- Fluxo do balcão: menos cliques entre empréstimos consecutivos (campo limpo
  e refocado após sucesso).
- Kiosk: aviso visual de tempo de sessão prestes a expirar.
- Cada mudança de UX passa pela suíte e pelo smoke test de construção de
  telas (instanciação headless dos builders, como validado em 08/07).

## Critérios de aceite

- `python -m unittest discover -s tests` verde no Windows local e no CI das
  3 plataformas.
- `python -m compileall sigbef` limpo.
- Fluxos de empréstimo/devolução/cadastro reproduzem os mesmos resultados de
  antes (validados por teste, não por inspeção).
- Versão alvo: v1.6.0 (tag só depois do merge no main, após a v1.5.1 sair).

## Riscos

- App em produção: mitigado por branch + testes antes de cada mudança.
- Subagentes em paralelo: restritos a arquivos disjuntos; integração e
  execução da suíte sempre no agente principal.
- Tkinter sem display no CI: os testes cobrem regra de negócio (sem UI);
  smoke de UI roda só localmente.
