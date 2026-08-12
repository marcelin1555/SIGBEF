# API REST do SIGBEF

Permite que outros sistemas da escola (secretaria, sistema acadêmico) e o
aplicativo do aluno consultem o acervo e a situação de empréstimos pela
rede local, sem acesso direto ao banco de dados.

**O acervo é somente leitura.** Livros, exemplares e cadastros não podem
ser alterados por aqui — isso continua sendo do balcão. As únicas
gravações que existem são três, todas feitas pelo próprio aluno logado e
só nos dados dele: entrar numa fila de espera, sair dela e renovar um
empréstimo que é seu. Emprestar e devolver seguem fora da API de
propósito: exigem o livro na mão.

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

### `POST /api/v1/login`

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
massa. Matrícula ou senha errada devolve **401**.

Trate os tokens como senhas. A API foi pensada para a **rede local da
escola**; não exponha a porta pra internet.

## Rotas

### `GET /api/v1/ping` (sem token)

Healthcheck. `{"ok": true, "servico": "SIGBEF", "versao": "1.10.0"}`

### `GET /api/v1/estatisticas`

Contagens do painel:

```bash
curl -H "Authorization: Bearer $TOKEN" http://IP_DA_BIBLIOTECA:8765/api/v1/estatisticas
```

```json
{"livros": 214, "exemplares": 512, "disponiveis": 448,
 "emp_abertos": 61, "atrasados": 3, "usuarios": 380}
```

### `GET /api/v1/livros?q=&disponiveis=1&pagina=1&limite=50`

Acervo com agregados, **em páginas**. `q` busca por título, autor, ISBN
ou categoria; `disponiveis=1` filtra só o que tem exemplar livre.

`limite` vai de 1 a 500 (padrão 50) e `pagina` começa em 1. Valor fora
da faixa é ajustado para o limite mais próximo, não vira erro: quem
integra outro sistema não deve quebrar por pedir demais.

Atenção à diferença entre dois números da resposta:

| Campo | O que é |
|---|---|
| `total` | Quantos livros a busca encontrou no acervo |
| `livros` | Só os que couberam nesta página |
| `paginas` | Quantas páginas existem no total |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://IP:8765/api/v1/livros?q=machado&pagina=2&limite=100"
```

```json
{"total": 2867, "pagina": 2, "limite": 100, "paginas": 29,
 "livros": [ ... 100 itens ... ]}
```

Para varrer o acervo inteiro, itere `pagina` até `paginas`. **Não existe
mais uma resposta com o acervo todo**: até a v1.7.0 a rota devolvia tudo
de uma vez, e num acervo grande isso virava dezenas de MB num JSON só,
que o cliente precisava segurar inteiro na memória antes de usar a
primeira linha.

### `GET /api/v1/livros/{id}`

Detalhes de um livro com todos os exemplares (tombo, código de barras,
localização e status).

### `GET /api/v1/usuarios/{matricula}/emprestimos` — exige token completo

Situação de um leitor: dados básicos, se pode pegar livro, multas em
aberto, empréstimos abertos e reservas ativas (posição na fila / prazo
de retirada). Não expõe e-mail, telefone nem credenciais.

Cada empréstimo aberto traz `pode_renovar` e `motivo_renovacao`, para o
app saber se oferece o botão antes de o aluno tentar — e, quando não,
com que frase explicar.

```bash
curl -H "Authorization: Bearer $TOKEN" http://IP:8765/api/v1/usuarios/2024001/emprestimos
```

### `GET /api/v1/usuarios/{matricula}/leitura?limite=6`

Retrato da leitura da pessoa e sugestões de próximos livros. Mesmo
isolamento das outras rotas pessoais: o token de aluno só lê a própria
matrícula, e pedir a de outro devolve **403**.

```json
{
  "estatisticas": {
    "total_lidos": 7, "lidos_no_ano": 3, "dias_medios": 6.4,
    "leitor_desde": "2025-03-11",
    "categoria_favorita": "Literatura Brasileira", "lidos_na_favorita": 4
  },
  "recomendacoes": [
    {"id": 42, "titulo": "São Bernardo", "categoria": "Literatura Brasileira",
     "motivo": "Quem leu \"Vidas Secas\" também leu"}
  ]
}
```

`total_lidos` conta só o que foi **devolvido** — livro em mãos ainda não
foi lido.

As sugestões saem em cascata, porque biblioteca de escola tem pouco dado
e um algoritmo colaborativo puro devolveria lista vazia quase sempre:
quem leu os mesmos livros → categoria favorita → mais lidos da escola →
o que ninguém pegou ainda. Cada item traz o `motivo`, para a tela
explicar a sugestão em vez de mostrar uma lista sem contexto.

O passo colaborativo lê o histórico de outros leitores **em agregado**:
a resposta nunca diz quem leu o quê.

Rota separada da de empréstimos de propósito — o aplicativo
ressincroniza a situação do leitor a cada reserva e renovação, e
recalcular a recomendação em toda ação seria desperdício.

`limite` aceita de 1 a 20 (padrão 6). Valor fora da faixa ou inválido é
ajustado, não recusado.

### `GET /api/v1/emprestimos/abertos` — exige token completo

Circulação atual completa, com flag de atraso por item.

## Gravações (apenas com token de aluno)

As três rotas abaixo exigem o token de sessão do aplicativo. Token
completo ou de consulta recebe **403**: eles pertencem à escola, não a
uma pessoa, e toda ação aqui precisa de um dono. Cada rota confere que o
registro é do aluno da sessão.

### `POST /api/v1/reservas`

Entra na fila de espera de um livro sem exemplar disponível.

```bash
curl -X POST http://IP:8765/api/v1/reservas \
  -H "Authorization: Bearer $TOKEN_DO_ALUNO" \
  -H "Content-Type: application/json" -d '{"livro_id": 42}'
```

```json
{"reserva": {"id": 7, "titulo": "Dom Casmurro", "posicao": 2}}
```

Devolve **201** em caso de sucesso e **409** quando a regra recusa: livro
com exemplar disponível (é para pegar emprestado, não reservar), reserva
repetida do mesmo livro ou limite de reservas ativas atingido
(`LIMITE_RESERVAS`, padrão 3).

### `POST /api/v1/reservas/{id}/cancelar`

Sai da fila. **409** se a reserva for de outro aluno ou já estiver
encerrada. Se o exemplar já estava separado, ele passa ao próximo da
fila automaticamente.

### `POST /api/v1/emprestimos/{id}/renovar`

Estende o prazo do próprio empréstimo, pelo prazo do perfil.

```json
{"data_prevista": "2026-08-10"}
```

**403** se o empréstimo for de outro leitor, **404** se não existir e
**409** quando a regra recusa. As três regras:

| Recusa | Por quê |
|---|---|
| Prazo já vencido | Livro atrasado precisa passar pelo balcão |
| Alguém na fila de reservas | Quem espera tem prioridade sobre quem renova |
| Limite de renovações atingido | `LIMITE_RENOVACOES`, padrão 2 |

No **balcão** essas regras não se aplicam: a bibliotecária tem o aluno na
frente e o contexto que o sistema não tem, então continua podendo renovar
em qualquer situação.

## Erros

Sempre JSON `{"erro": "mensagem"}`:

| Código | Quando |
|---|---|
| 401 | Token ausente ou inválido |
| 403 | API desligada nas configurações |
| 404 | Rota, livro ou matrícula inexistente |
| 405 | PUT/DELETE/PATCH, ou POST em rota que não aceita gravação |
| 409 | A regra da biblioteca recusou a ação. A mensagem vem escrita para o aluno ler ("Outro leitor está esperando por este livro.") |

## Notas técnicas

- Implementação 100% biblioteca padrão do Python (`http.server`);
  nenhuma dependência nova
- Leituras concorrentes com o balcão/kiosk são seguras (SQLite em WAL)
- Token comparado em tempo constante; geração via `secrets`
