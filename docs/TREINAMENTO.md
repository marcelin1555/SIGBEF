# Roteiro de Treinamento — SIGBEF

Guia prático para capacitar quem vai **usar** o SIGBEF no dia a dia: a
bibliotecária no balcão e os alunos/professores no autoatendimento.

Diferente do [Manual do Usuário](MANUAL_DO_USUARIO.md), que é referência,
este documento é um roteiro de aula: módulos curtos, passo a passo e um
exercício ao fim de cada um. Faça os exercícios no sistema com os
**dados de demonstração** carregados (Configurações → Ferramentas →
"Carregar dados de demonstração").

Duração sugerida: **2h** (Parte 1 com a bibliotecária, ~1h20; Parte 2
com uma turma, ~40 min).

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
   Empréstimos, Fila de espera, Uso do acervo, Relatórios). O item da
   tela atual fica destacado.
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

### Módulo 5: Reservas e fila de espera

Objetivo: entender o que fazer quando um livro reservado volta.

Quando todos os exemplares de um livro estão emprestados, o leitor pode
**reservar** e entrar numa fila — no balcão com você, ou sozinho pelo
aplicativo do celular. O que muda para você:

1. Quando esse livro é **devolvido**, o SIGBEF **não** o solta de volta
   pra prateleira. Aparece um aviso: *"Separe o exemplar para Fulano,
   retirada até tal data"*.
2. **Separe fisicamente** esse exemplar (deixe embaixo do balcão com o
   nome). Só o aluno da vez consegue pegá-lo emprestado.
3. Se ele não aparecer no prazo, a reserva expira sozinha e o livro
   passa para o próximo da fila (ou volta a ficar livre).
4. Menu **Fila de espera**: quem está esperando cada livro. As linhas
   destacadas já têm exemplar separado — a coluna Situação mostra até
   quando o aluno pode retirar e o número de tombo, para você achar o
   livro na prateleira de reservados.

Como o aluno entra na fila pelo celular sem falar com ninguém, esta tela
é onde você descobre o que foi reservado sem passar por você.

**Exercício:** peça a um colega logar como aluno `2024002`, reservar um
livro esgotado; então, como bibliotecária, devolva esse livro, veja o
aviso de separação e confira a linha destacada em **Fila de espera**.

### Módulo 6: Uso do acervo

Objetivo: usar os números para decidir compra e exposição.

Menu **Uso do acervo**. Diferente dos relatórios, que respondem *o que
aconteceu*, esta tela ajuda a decidir *o que fazer*:

1. Os quatro números do topo: quanto do acervo já circulou, quantos
   livros nunca saíram, leitores nos últimos 30 dias e a taxa de atraso
   (fica vermelha acima de 20%).
2. **Empréstimos por mês** — mostra se a biblioteca está viva e onde
   houve queda.
3. **Turmas que mais leem** e **Categorias mais procuradas** — útil na
   conversa com a coordenação e na hora de comprar livro novo.
4. **Livros parados**: o botão abre a lista completa dos títulos que
   nunca foram emprestados, e há exportação em CSV.

O acervo parado costuma ser o achado mais útil. Livro que ninguém pega
raramente é livro ruim — quase sempre é livro que ninguém viu. Vale
montar exposição, indicar em sala ou rever a próxima compra.

**Exercício:** abra **Uso do acervo**, veja qual turma mais lê e exporte
a lista de livros parados.

### Módulo 7: Relatórios e backup

Objetivo: extrair dados e proteger o acervo.

1. Menu **Relatórios**: exporte acervo, usuários, os mais emprestados ou
   as pendências dos leitores em CSV (abre no Excel).
2. **Período**: os botões no topo (Este mês, Este bimestre, Este ano)
   recortam os relatórios de movimento. É assim que se monta o número
   para levar à direção.
3. **Movimentação do período**: o relatório de prestação de contas.
   Numa página: empréstimos, devoluções, atrasos, multas e as turmas
   que mais leram.
4. **Backup**: agora acontece sozinho ao fechar o sistema, uma vez por
   dia, guardando as últimas 7 cópias. O botão manual continua em
   Configurações → Ferramentas, para levar uma cópia no pendrive.

**Exercício:** escolha "Este ano", gere a **Movimentação do período** e
confira quantos empréstimos a escola fez.

### Módulo 8: Conferir o acervo e dar baixa

Objetivo: saber o que a biblioteca realmente tem na estante.

Este módulo é o do fim do ano letivo, e é o que mais dá trabalho — vale
treinar antes de precisar.

1. Menu **Conferir acervo** → **Iniciar conferência**.
2. Passe o leitor em cada exemplar da prateleira. O cursor volta sozinho
   para o campo: dá para segurar o leitor numa mão e os livros na outra.
3. Fique de olho nos avisos em laranja: "Estava emprestado!" quer dizer
   que o livro está na sua frente mas o sistema acha que está com
   alguém.
4. Pode parar e continuar depois — a conferência só fecha quando você
   clicar em **Encerrar**.
5. No fim, exporte o CSV e leve a lista de **não encontrados** para uma
   segunda busca na estante.
6. O que não aparecer nem na segunda busca: **Livros → Ver detalhes →
   Dar baixa no exemplar → Extraviado**.

**Exercício:** faça uma conferência de uma prateleira só, deixando um
livro de fora de propósito, e confira que ele aparece na lista de não
encontrados.

---

## Parte 2 — Aluno / Professor

### Módulo 9: Pesquisar e reservar

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

### Módulo 10: Terminal de Autoatendimento (kiosk)

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

### Módulo 11: O aplicativo no celular

Objetivo: o aluno acompanha a biblioteca sem precisar ir até lá.

O SIGBEF tem um aplicativo Android. Ele não substitui o balcão —
emprestar e devolver continuam exigindo o livro na mão —, mas resolve
tudo o mais.

**Para começar (uma vez só):**
1. A bibliotecária abre **Configurações → Integrações → Parear celular**
   no computador, e um QR code aparece na tela.
2. O aluno abre o app, toca em **Ler o QR da biblioteca** e aponta a
   câmera. Quem preferir pode digitar o endereço.
3. Ele entra com a **mesma matrícula e senha** do sistema.

**O que ele faz pelo celular:**
- Consulta o acervo e vê a ficha do livro (com tombo e sinopse)
- Vê os próprios empréstimos, prazos e o histórico de leituras
- **Renova** um livro, quando as regras permitem
- **Entra na fila** de um livro emprestado, e sai dela
- Mostra o **cartão digital** com código de barras — funciona sem
  internet, e o leitor do balcão lê da tela do celular
- Em **Minha leitura**, vê quanto já leu e recebe sugestões

**O que dizer quando perguntarem:**
- *"Por que não renovou?"* — o app mostra o motivo na tela: prazo
  vencido, alguém na fila esperando, ou limite de renovações atingido.
- *"Preciso de internet?"* — só do Wi-Fi da escola, e só para atualizar.
  O cartão funciona sempre.
- *"Meus dados vão para a internet?"* — não. O app só fala com o
  computador da biblioteca, na rede da escola.

> Antes de treinar os alunos, confirme que o Wi-Fi da escola **não tem
> isolamento de clientes** ligado. Com ele, o celular não enxerga o
> computador da biblioteca e o app diz que o endereço está errado, mesmo
> estando certo. Ver `SIGBEF_MOBILE.md` §7.

**Exercício:** pareie um celular com a biblioteca, entre com um login de
aluno e mostre o cartão digital no leitor do balcão.

---

## Checklist do multiplicador

Ao final, cada pessoa treinada deve conseguir, sem ajuda:

- [ ] Entrar no sistema e reconhecer o menu
- [ ] Cadastrar um livro e imprimir a etiqueta
- [ ] Cadastrar um usuário e imprimir o cartão
- [ ] Fazer um empréstimo e uma devolução (inclusive por duplo clique)
- [ ] Explicar o que fazer quando um livro reservado volta
- [ ] Consultar a **fila de espera** e achar o exemplar separado
- [ ] Abrir **Uso do acervo** e exportar a lista de livros parados
- [ ] Gerar um relatório e um backup
- [ ] Parear um celular e explicar o que o aplicativo faz
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
