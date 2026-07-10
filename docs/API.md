# API REST do SIGBEF (somente leitura)

Permite que outros sistemas da escola (secretaria, sistema acadêmico)
consultem o acervo e a situação de empréstimos pela rede local, sem
acesso direto ao banco de dados. **Nenhuma rota altera dados.**

Desligada por padrão: com a API desativada, o SIGBEF não abre porta
nenhuma e continua 100% offline.

## Como ativar

1. Entre no SIGBEF como administrador
2. Configurações → Integrações (online) → marque **"API REST somente
   leitura"**
3. Copie o **token de acesso** (botão "Copiar token") e entregue ao
   responsável pelo sistema que vai consumir a API
4. A API sobe junto com o aplicativo. Para rodar num servidor sem
   interface: `python sigbef.py --api` (ou `SIGBEF.exe --api`)

Porta padrão: **8765** (ajustável na mesma tela).

## Autenticação

Toda rota (exceto `/api/v1/ping`) exige o header:

```
Authorization: Bearer SEU_TOKEN_AQUI
```

Trate o token como uma senha. Se vazar, gere um novo na mesma tela
(o antigo deixa de valer na hora). A API foi pensada para a **rede
local da escola**; não exponha a porta pra internet.

## Rotas

### `GET /api/v1/ping` (sem token)

Healthcheck. `{"ok": true, "servico": "SIGBEF", "versao": "1.6.0"}`

### `GET /api/v1/estatisticas`

Contagens do painel:

```bash
curl -H "Authorization: Bearer $TOKEN" http://IP_DA_BIBLIOTECA:8765/api/v1/estatisticas
```

```json
{"livros": 214, "exemplares": 512, "disponiveis": 448,
 "emp_abertos": 61, "atrasados": 3, "usuarios": 380}
```

### `GET /api/v1/livros?q=&disponiveis=1`

Acervo com agregados. `q` busca por título, autor, ISBN ou categoria;
`disponiveis=1` filtra só o que tem exemplar livre.

```bash
curl -H "Authorization: Bearer $TOKEN" "http://IP:8765/api/v1/livros?q=machado"
```

### `GET /api/v1/livros/{id}`

Detalhes de um livro com todos os exemplares (tombo, código de barras,
localização e status).

### `GET /api/v1/usuarios/{matricula}/emprestimos`

Situação de um leitor: dados básicos, se pode pegar livro, multas em
aberto, empréstimos abertos e reservas ativas (posição na fila / prazo
de retirada). Não expõe e-mail, telefone nem credenciais.

```bash
curl -H "Authorization: Bearer $TOKEN" http://IP:8765/api/v1/usuarios/2024001/emprestimos
```

### `GET /api/v1/emprestimos/abertos`

Circulação atual completa, com flag de atraso por item.

## Erros

Sempre JSON `{"erro": "mensagem"}`:

| Código | Quando |
|---|---|
| 401 | Token ausente ou inválido |
| 403 | API desligada nas configurações |
| 404 | Rota, livro ou matrícula inexistente |
| 405 | Método diferente de GET (a API é somente leitura) |

## Notas técnicas

- Implementação 100% biblioteca padrão do Python (`http.server`);
  nenhuma dependência nova
- Leituras concorrentes com o balcão/kiosk são seguras (SQLite em WAL)
- Token comparado em tempo constante; geração via `secrets`
