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

## Autenticação e níveis de token

Toda rota (exceto `/api/v1/ping`) exige o header:

```
Authorization: Bearer SEU_TOKEN_AQUI
```

Existem **três níveis** de token (princípio do menor privilégio, entregue
só o que o sistema integrado precisa):

| Token | Acessa | Use para |
|---|---|---|
| **Completo** | Tudo: acervo + situação de leitores + circulação | Sistemas internos de confiança |
| **Consulta** | Só o acervo público (livros, disponibilidade, estatísticas) | Mostrar o catálogo num site/totem, sem expor dados de alunos |
| **Sessão do app** | Acervo + os empréstimos **do próprio aluno** | Aplicativo de celular, um token por aparelho |

Um token de consulta que tente acessar dados de leitores recebe **403**.
Os dois primeiros aparecem em Configurações → Integrações, cada um com seu
botão de "gerar novo" (regenerar invalida só aquele token, na hora).

O token de **sessão do app** é diferente: nasce no login do aluno
(`POST /api/v1/login`), fica preso àquela matrícula e expira sozinho
(30 dias por padrão, ajustável em `API_SESSAO_DIAS`). Se o aluno pedir os
empréstimos de outra matrícula, recebe **403** — é o que impede um aluno
de ver a vida de leitura dos colegas. No banco fica só o hash do token,
nunca o valor em claro. A bibliotecária pode desconectar todos os
aparelhos de uma vez em Configurações → Integrações.

### `POST /api/v1/login` (único POST da API)

```bash
curl -X POST http://IP:8765/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"matricula":"2026045892","senha":"..."}'
```

```json
{
  "token": "...",
  "usuario": {"nome": "...", "matricula": "...", "perfil": "ALUNO"}
}
```

Usa o mesmo login do sistema, com a mesma proteção contra tentativa em
massa. Matrícula ou senha errada devolve **401**. Nenhuma outra rota
aceita POST; o acervo continua não sendo alterável pela API.

Trate os tokens como senhas. A API foi pensada para a **rede local da
escola**; não exponha a porta pra internet.

## Rotas

### `GET /api/v1/ping` (sem token)

Healthcheck. `{"ok": true, "servico": "SIGBEF", "versao": "1.6.2"}`

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

### `GET /api/v1/usuarios/{matricula}/emprestimos` — exige token completo

Situação de um leitor: dados básicos, se pode pegar livro, multas em
aberto, empréstimos abertos e reservas ativas (posição na fila / prazo
de retirada). Não expõe e-mail, telefone nem credenciais.

```bash
curl -H "Authorization: Bearer $TOKEN" http://IP:8765/api/v1/usuarios/2024001/emprestimos
```

### `GET /api/v1/emprestimos/abertos` — exige token completo

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
