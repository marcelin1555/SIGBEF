# SIGBEF Mobile — especificação do MVP

Status: **desenho aprovado, implementação não iniciada.**
Última atualização: 23/07/2026.

Aplicativo de celular para **alunos e professores** consultarem o acervo,
acompanharem os próprios empréstimos e usarem o cartão de biblioteca
digital. Não substitui o desktop: o SIGBEF desktop continua sendo a
fonte da verdade e a única forma de emprestar/devolver.

Identidade visual: seguir `docs/DESIGN.md` (cores, tipografia, ícones).

---

## 1. Princípios (herdados do produto)

1. **O desktop é a fonte da verdade.** O banco SQLite fica no computador
   da biblioteca. O app é um cliente de leitura.
2. **Offline-first opt-in.** Nada de nuvem, push de terceiros, analytics
   ou telemetria. Nenhum dado do aluno sai da escola.
3. **Útil mesmo sem rede.** O cartão digital e a última consulta ficam
   em cache no aparelho.
4. **Escola pública de ensino médio/técnico.** Vocabulário de escola:
   série/turma (não "curso"), tombo (não CDD), livro físico (não e-book).
5. **Acessível.** Alvos de toque ≥ 44 px, contraste AA, textos curtos.

---

## 2. Escopo do MVP

### Dentro

| # | Funcionalidade | Depende de |
|---|---|---|
| 1 | Consultar acervo (busca + filtro por categoria + disponibilidade) | API atual |
| 2 | Meus empréstimos (ativos, prazos, atrasos, histórico) | API atual |
| 3 | Cartão de biblioteca digital (código de barras na tela) | Local, offline |
| 4 | Detalhes do livro (autor, categoria, ano, tombo, sinopse) | API atual |
| 5 | Modo offline (cache da última consulta) | Local |

### Fora (por ora)

- Emprestar/devolver pelo app — isso é do balcão e do kiosk.
- Renovação online — a API é **somente leitura**; a tela explica como
  renovar presencialmente.
- Reserva — desenhada, mas **bloqueada** até a API ganhar escrita
  (ver §5).
- Perfil de bibliotecário — o app é para leitores.

---

## 3. Telas

12 telas desenhadas. Mockups em `docs/mobile/` (a exportar).

| # | Tela | Estado | Observação |
|---|---|---|---|
| 1 | Conectar à biblioteca | ✅ | Falta inserir a ilustração |
| 2 | Login | ✅ | Matrícula + senha do próprio sistema |
| 3 | Início | ✅ | Saudação, resumo, atalhos 2×2, status da conexão |
| 4 | Acervo (busca) | ✅ | **Padrão-ouro** das lombadas |
| 5 | Detalhes do livro | ⚠️ revisar | Trocar capa por lombada; usar tombo |
| 6 | Reservar livro | ✅ | Bloqueada até API de escrita |
| 7 | Meus empréstimos | ⚠️ revisar | Datas para 2026; lombadas |
| 8 | Renovação presencial | ✅ | Instruções numeradas |
| 9 | Cartão digital | ⚠️ revisar | Remover foto de perfil; usar série/turma |
| 10 | Modo offline | ✅ | Banner âmbar + selo "OFFLINE OK" |
| 11 | Vazio: busca sem resultado | ✅ | |
| 12 | Vazio: sem empréstimos | ✅ | |

### Navegação

Tab bar fixa com 4 itens: **Início · Acervo · Empréstimos · Cartão**.
Login e Conectar ficam fora da tab bar (fluxo de entrada).

### Regras visuais específicas do app

- **Livro não tem capa.** Usar placeholder de lombada: retângulo na cor
  da categoria, título na vertical em branco. O acervo real não guarda
  imagens de capa e não vamos inventar dependência de internet para isso.
- **Sem sino de notificações.** Não há push. Avisos de prazo aparecem no
  card de resumo da tela Início, calculados no aparelho.
- **Sem foto de perfil.** O sistema não armazena fotos, e a maioria dos
  usuários é menor de idade.
- Cores de estado: verde = em dia/disponível, laranja = vence em breve,
  vermelho = atrasado. Nunca usar laranja para informação neutra.

---

## 4. Arquitetura

```
[Celular do aluno]                    [Computador da biblioteca]
  SIGBEF Mobile                          SIGBEF Desktop
   ├── cache local  ──── Wi-Fi da ────►   API REST :8765
   │   (cartão,      ─── escola ─────►    (somente leitura)
   │    últimas buscas)                        │
   └── sem internet externa                 SQLite
```

- O app **só fala com o desktop**, na rede local. Nenhum servidor externo.
- Sem conexão: cartão digital e último cache continuam disponíveis, com
  aviso claro de que os dados podem estar desatualizados.

### API disponível hoje (`docs/API.md`)

| Rota | Uso no app |
|---|---|
| `GET /api/v1/ping` | Testar se a biblioteca está acessível |
| `GET /api/v1/livros?q=&disponiveis=1` | Busca do acervo |
| `GET /api/v1/livros/{id}` | Detalhes do livro |
| `GET /api/v1/usuarios/{matricula}/emprestimos` | Meus empréstimos |
| `GET /api/v1/estatisticas` | (não usado no MVP) |

Autenticação: header `Authorization: Bearer TOKEN`. Existem dois níveis;
o app precisa do **token completo** (acessa dados do leitor).

---

## 5. O que o app exige do desktop

Requisitos novos que a implementação do app cria no SIGBEF desktop.
**Nenhum deles existe hoje.**

| # | Requisito | Prioridade | Por quê |
|---|---|---|---|
| ~~R1~~ | ✅ **ENTREGUE** — QR de pareamento em Configurações → Integrações. Contém **só** endereço + porta (não leva token: o QR fica exposto na tela e seria fotografado). | — | Commit `c54386e` |
| ~~R2~~ | ✅ **ENTREGUE** — `POST /api/v1/login` com matrícula e senha, devolvendo token de sessão preso ao aluno e com validade. | — | Ver `docs/API.md` |
| R3 | **Escrita para reserva** (`POST /api/v1/reservas`) | Média | A tela de Reservar existe no desenho, mas fica desativada até isto. |
| R4 | Campo de **sinopse** no acervo | Baixa | A tela de detalhes mostra sinopse; o banco atual não tem esse campo. |

> ✅ **O furo de privacidade do R2 está fechado.** Antes, um token dava
> acesso aos empréstimos de qualquer matrícula. Agora o app recebe um
> token de **sessão**, preso a um aluno: pedir os empréstimos de outra
> matrícula devolve **403**. Há teste cobrindo exatamente esse caso
> (`test_aluno_NAO_le_emprestimos_de_outro`).

---

## 6. Tecnologia — em aberto

A definir com prós e contras antes de codar. Candidatos, considerando
que a equipe domina Python e React:

| Opção | A favor | Contra |
|---|---|---|
| **PWA** (React) | Reaproveita o stack do site; sem loja; instala pelo navegador | Câmera/QR mais limitada; "instalar" confunde usuário leigo |
| **React Native / Expo** | Mesma linguagem do site; APK real; boa câmera | Build e distribuição do APK; mais dependências |
| **Flutter** | Ótimo desempenho e visual | Linguagem nova (Dart) para a equipe |

Distribuição provável: **APK entregue pela escola** (QR/site), não loja —
evita conta de desenvolvedor paga e revisão.

---

## 7. Próximos passos

1. Fechar as 3 telas marcadas como "revisar" (§3) e exportar mockups para
   `docs/mobile/`.
2. Decidir a tecnologia (§6).
3. Implementar **R1 (QR de pareamento)** e **R2 (login por usuário)** no
   desktop — sem eles o app não sai do papel.
4. MVP do app: Conectar → Login → Cartão (offline) → Acervo → Empréstimos.

Registrado no roadmap do `README.md` como "Aplicativo móvel para consulta
e renovação do acervo".
