# Roteiro de Treinamento — SIGBEF

Guia prático para capacitar quem vai **usar** o SIGBEF no dia a dia: a
bibliotecária no balcão e os alunos/professores no autoatendimento.

Diferente do [Manual do Usuário](MANUAL_DO_USUARIO.md), que é referência,
este documento é um roteiro de aula: módulos curtos, passo a passo e um
exercício ao fim de cada um. Faça os exercícios no sistema com os
**dados de demonstração** carregados (Configurações → Ferramentas →
"Carregar dados de demonstração").

Duração sugerida: **1h30** (Parte 1 com a bibliotecária, ~1h; Parte 2
com uma turma, ~30 min).

Logins de treino (dados de demonstração):

| Papel | Usuário | Senha |
|---|---|---|
| Bibliotecária | `jaqueline` | `jaqueline123` |
| Aluno | `2024001` | `lucas123` |
| Aluna | `2024002` | `beatriz123` |

---

## Parte 1 — Bibliotecária (balcão)

### Módulo 1: Primeiros passos e a tela

Objetivo: reconhecer as áreas do sistema.

1. Abra o SIGBEF e entre com `jaqueline` / `jaqueline123`.
2. Repare no **menu lateral** à esquerda (Painel, Livros, Usuários,
   Empréstimos, Relatórios). O item da tela atual fica destacado.
3. Atalhos que economizam tempo: **F5** recarrega a tela, **Ctrl+F**
   pula direto para o campo de busca.
4. O **Painel inicial** mostra os números do dia: acervo, empréstimos
   abertos e atrasos.

**Exercício:** navegue por cada item do menu e volte ao Painel usando
só o teclado (Tab e Enter).

### Módulo 2: Cadastrar livros e imprimir etiquetas

Objetivo: colocar um livro novo no acervo pronto para circular.

1. Menu **Livros e exemplares** → botão **Cadastrar livro**.
2. Preencha título e autor (obrigatórios). ISBN, editora, categoria e
   ano são opcionais. Em **Quantidade de exemplares**, informe quantas
   cópias físicas existem.
3. Salve. O sistema gera um código de barras único para cada exemplar.
4. Para colar nos livros: menu **Livros** → **Etiquetas** → escolha o
   acervo todo ou uma busca → **Imprimir** (ou salvar em PDF).

Dica: se tiver a lista do acervo numa planilha, use **Importar CSV** em
vez de cadastrar um a um. Baixe o modelo, preencha e importe.

**Exercício:** cadastre o livro "Menino Maluquinho", de Ziraldo, com 2
exemplares, e imprima as etiquetas dele.

### Módulo 3: Cadastrar usuários e o cartão

Objetivo: dar acesso a um aluno novo.

1. Menu **Usuários** → **Cadastrar usuário**.
2. Preencha nome, matrícula (é o login), perfil (Aluno, Professor,
   Bibliotecário) e uma senha inicial. Série/Turma e e-mail são
   opcionais, mas o e-mail habilita os avisos de vencimento.
3. Salve. Para o cartão com código de barras: selecione o usuário →
   **Imprimir cartão**.

**Exercício:** cadastre um aluno fictício da sua turma e imprima o
cartão dele.

### Módulo 4: Empréstimo e devolução (o coração do balcão)

Objetivo: o fluxo que você mais vai repetir.

**Emprestar:**
1. Menu **Empréstimos abertos** → cartão "Empréstimo rápido".
2. Escaneie o cartão do aluno (ou digite a matrícula) e o código de
   barras do livro (ou o número de tombo). Botão **Registrar
   empréstimo**.
3. O sistema calcula o prazo (7 dias aluno, 14 professor) e já deixa o
   cursor pronto para o próximo aluno da fila.

**Devolver (com um clique):**
1. Na tabela **Empréstimos em aberto**, ache a linha do livro.
2. **Duplo clique** na linha (ou selecione e clique em "Devolver
   selecionado") → confirme.
3. Se houver atraso, o sistema mostra a **multa** automaticamente. Sem
   atraso, some da lista na hora.

Devolvendo uma pilha de livros? Use o campo "Devolução rápida" e vá
escaneando: escaneia, Enter, escaneia. Sem janelinha a cada livro.

**Exercício:** empreste o "Dom Casmurro" para o aluno `2024001`,
depois devolva pelo duplo clique.

### Módulo 5: Reservas e fila de espera (novo na v1.6)

Objetivo: entender o que fazer quando um livro reservado volta.

Quando todos os exemplares de um livro estão emprestados, o aluno pode
**reservar** e entrar numa fila. O que muda para você no balcão:

1. Quando esse livro é **devolvido**, o SIGBEF **não** o solta de volta
   pra prateleira. Aparece um aviso: *"Separe o exemplar para Fulano,
   retirada até tal data"*.
2. **Separe fisicamente** esse exemplar (deixe embaixo do balcão com o
   nome). Só o aluno da vez consegue pegá-lo emprestado.
3. Se ele não aparecer no prazo, a reserva expira sozinha e o livro
   passa para o próximo da fila (ou volta a ficar livre).

**Exercício:** peça a um colega logar como aluno `2024002`, reservar um
livro esgotado; então, como bibliotecária, devolva esse livro e veja o
aviso de separação.

### Módulo 6: Relatórios e backup

Objetivo: extrair dados e proteger o acervo.

1. Menu **Relatórios**: exporte acervo, usuários ou os mais emprestados
   em CSV (abre no Excel).
2. **Backup** (Configurações → Ferramentas → "Fazer backup agora"):
   faça isso toda semana. Guarde a cópia num pendrive ou na nuvem.

**Exercício:** gere o relatório "Top 50 mais emprestados" e faça um
backup do banco.

---

## Parte 2 — Aluno / Professor

### Módulo 7: Pesquisar e reservar

Objetivo: o aluno encontra e garante o livro que quer.

1. Entre com um login de aluno (`2024001` / `lucas123`).
2. Menu **Pesquisar livros**: digite título ou autor. Desmarque
   "Apenas disponíveis" para ver o acervo inteiro.
3. Livro disponível → **Pegar emprestado**. Livro esgotado →
   **Reservar** (entra na fila; o sistema diz sua posição).
4. Menu **Meus empréstimos**: veja o que está com você, os prazos, e
   suas **reservas** (posição na fila ou "separado, retire até tal
   data"). Dá para **cancelar** uma reserva ali.

**Exercício:** reserve um livro esgotado e confira sua posição em
"Meus empréstimos".

### Módulo 8: Terminal de Autoatendimento (kiosk)

Objetivo: emprestar/devolver sozinho, sem a bibliotecária.

1. A bibliotecária abre o modo kiosk (na tela de login, marca
   "Autoatendimento", ou o atalho abre direto).
2. O aluno **aproxima o cartão** do leitor (ou digita a matrícula) e
   escolhe: **Pegar emprestado**, **Devolver** ou **Meus empréstimos**.
3. Escaneia o livro, confirma, pronto. Um comprovante aparece na tela.
4. Se o aluno se distrair, aparece um aviso **15 segundos antes** de
   encerrar a sessão por inatividade ("toque na tela para continuar").

**Exercício:** no modo kiosk, faça um empréstimo e uma devolução
completos usando só a tela de toque/teclado.

---

## Checklist do multiplicador

Ao final, cada pessoa treinada deve conseguir, sem ajuda:

- [ ] Entrar no sistema e reconhecer o menu
- [ ] Cadastrar um livro e imprimir a etiqueta
- [ ] Cadastrar um usuário e imprimir o cartão
- [ ] Fazer um empréstimo e uma devolução (inclusive por duplo clique)
- [ ] Explicar o que fazer quando um livro reservado volta
- [ ] Gerar um relatório e um backup
- [ ] (Aluno) pesquisar, reservar e usar o autoatendimento

## Dúvidas comuns

**Esqueci minha senha.** Procure a bibliotecária ou o administrador;
ele redefine no cadastro do usuário.

**Errei a senha várias vezes e travou.** Após 5 erros a conta bloqueia
por 15 minutos (proteção contra tentativa de invasão). Espere ou peça
ao administrador.

**O sistema precisa de internet?** Não. Tudo funciona offline. Só os
avisos por e-mail e a busca de livro por ISBN usam internet, e ambos
vêm desligados.

**Perdi um livro / a etiqueta rasgou.** Recadastre o exemplar ou
reimprima a etiqueta pelo menu Livros; o histórico de empréstimos é
preservado.
