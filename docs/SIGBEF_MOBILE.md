# SIGBEF Mobile — especificação do MVP

Status: **entregue e verificado em aparelho real.** Última atualização:
26/07/2026.

O fluxo inteiro foi rodado num Xiaomi com Android 15, contra o acervo de
verdade do CEFE: ler o QR com a câmera, parear, entrar, consultar os
2.867 livros, ver a carteirinha, reservar e renovar. Os 5 achados
críticos e os 9 altos da auditoria (`docs/AUDITORIA_MOBILE.md`) estão
corrigidos.

Um requisito de rede apareceu nesse teste e vale ler antes de implantar
em qualquer escola: **§7**.

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

- Emprestar/devolver pelo app — isso é do balcão e do kiosk, porque
  exige o livro na mão.
- Perfil de bibliotecário — o app é para leitores.

Reserva e renovação **saíram desta lista**: foram entregues junto do R3
(ver §5), com as regras validadas pelo servidor.

---

## 3. Telas

12 telas desenhadas. Mockups em `docs/mobile/` (a exportar).

| # | Tela | Estado | Observação |
|---|---|---|---|
| 1 | Conectar à biblioteca | ✅ | Lê o QR pela câmera; digitar continua disponível |
| 2 | Login | ✅ | Matrícula + senha do próprio sistema |
| 3 | Início | ✅ | Saudação, resumo, atalhos 2×2, status da conexão |
| 4 | Acervo (busca) | ✅ | **Padrão-ouro** das lombadas |
| 5 | Detalhes do livro | ✅ | Lombada e tombo; reserva quando emprestado |
| 6 | Reservar livro | ✅ | Feito dentro do detalhe do livro, não em tela separada |
| 7 | Meus empréstimos | ✅ | Com a fila de espera e o botão de renovar |
| 8 | Como renovar | ✅ | Renovação é pelo app; a tela explica as regras |
| 9 | Cartão digital | ✅ | Code 128 real, lido pelo mesmo leitor do balcão |
| 10 | Modo offline | ✅ | Tarja âmbar no topo (o selo "OFFLINE OK" saiu: estourava a barra) |
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
   │   (cartão,      ─── escola ─────►    (acervo só de leitura)
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
| `POST /api/v1/login` | Entrar com matrícula e senha |
| `POST /api/v1/reservas` | Entrar na fila de espera |
| `POST /api/v1/reservas/{id}/cancelar` | Sair da fila |
| `POST /api/v1/emprestimos/{id}/renovar` | Renovar o próprio empréstimo |

Autenticação: header `Authorization: Bearer TOKEN`. O app usa o **token
de sessão do aluno**, emitido pelo login e presos a ele — não o token de
sistema, que é da escola e não de uma pessoa.

---

## 5. O que o app exige do desktop

Requisitos que a implementação do app criou no SIGBEF desktop. Todos
resolvidos.

| # | Requisito | Prioridade | Por quê |
|---|---|---|---|
| ~~R1~~ | ✅ **ENTREGUE** — QR de pareamento em Configurações → Integrações. Contém **só** endereço + porta (não leva token: o QR fica exposto na tela e seria fotografado). | — | Commit `c54386e` |
| ~~R2~~ | ✅ **ENTREGUE** — `POST /api/v1/login` com matrícula e senha, devolvendo token de sessão preso ao aluno e com validade. | — | Ver `docs/API.md` |
| ~~R3~~ | ✅ **ENTREGUE** — escrita restrita: `POST /api/v1/reservas`, `.../reservas/{id}/cancelar` e `.../emprestimos/{id}/renovar`, todas só com token de aluno e só nos dados dele. Renovação passou a ter regras explícitas (`pode_renovar`). | — | Ver `docs/API.md` |
| ~~R4~~ | ✅ **JÁ EXISTIA** — a coluna `sinopse` está em `livro` (`database.py:115`) e vem em `GET /api/v1/livros/{id}`. O levantamento original errou aqui. | — | Verificado no app, com sinopse real |

> ✅ **O furo de privacidade do R2 está fechado.** Antes, um token dava
> acesso aos empréstimos de qualquer matrícula. Agora o app recebe um
> token de **sessão**, preso a um aluno: pedir os empréstimos de outra
> matrícula devolve **403**. Há teste cobrindo exatamente esse caso
> (`test_aluno_NAO_le_emprestimos_de_outro`).

---

## 6. Tecnologia — decidida

**Kotlin + Jetpack Compose**, APK entregue pela escola (não pela loja) —
evita conta de desenvolvedor paga e revisão.

A escolha não foi por comparação teórica: já existia um app em Compose,
feito no AI Studio, com as telas desenhadas. Refazer em outro stack
jogaria fora ~2.900 linhas de interface que já seguiam este documento.
Ver `docs/AUDITORIA_MOBILE.md` para o que aquele código era (uma
demonstração com dados falsos) e o que foi preciso para torná-lo real.

Dependências que entraram e por quê:

| O quê | Por quê |
|---|---|
| Retrofit + Moshi + OkHttp | Falar com a API do desktop |
| Room | Cache local, para o app funcionar sem rede |
| CameraX + ML Kit (barcode) | Ler o QR de pareamento. O ML Kit é o **embarcado**, não o do Play Services: nem todo aparelho de aluno tem os serviços do Google |

O motor do leitor pesa ~5 MB **por arquitetura**, então o release gera um
APK por ABI: o aluno instala ~19 MB em vez de ~35 MB.

---

## 7. Requisito de rede (descoberto em campo)

**O Wi-Fi da escola não pode ter isolamento de clientes.**

Esse recurso — "AP isolation", "isolamento de clientes", "modo visitante"
— impede que dois aparelhos ligados no mesmo roteador conversem entre si.
É comum vir ligado em redes de convidados. Com ele ativo, o celular
enxerga a internet normalmente, mas **não** enxerga o computador da
biblioteca, e o app não consegue parear.

Como reconhecer: o app diz "Não encontrei a biblioteca nesse endereço"
mesmo com o endereço certo e os dois no mesmo Wi-Fi. Confirmação, no
celular com depuração USB ligada:

```bash
adb shell ip neigh show <IP-DO-COMPUTADOR>
```

Se responder `FAILED`, o celular não consegue nem descobrir o endereço
físico do computador — é isolamento, não é o app. Um teste mais simples:
abrir `http://<IP>:8765/api/v1/ping` no navegador do celular. Se der
`ERR_ADDRESS_UNREACHABLE`, o problema é a rede.

Solução: desligar o isolamento de clientes na administração do roteador,
ou colocar o computador da biblioteca e os celulares na mesma rede sem
isolamento. Vale conferir isso **antes** de implantar em cada escola.

---

## 8. Estado atual

Entregue e verificado em aparelho real (Xiaomi, Android 15) contra o
acervo de verdade do CEFE:

- Pareamento por QR lido pela câmera, login do aluno, acervo com busca,
  ficha do livro, cartão com código de barras Code 128, empréstimos
- Reserva, cancelamento e renovação pelo próprio app
- Tudo funciona offline a partir do cache; o cartão nunca depende de rede

Fora do escopo, por decisão: emprestar e devolver (exigem o livro na
mão, são de balcão) e perfil de bibliotecário (o app é para leitores).

Registrado no roadmap do `README.md` como "Aplicativo móvel para consulta
e renovação do acervo".
