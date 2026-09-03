# Manual do Usuário — SIGBEF

Sistema Integrado de Gestão da Biblioteca do CEFE.

Este manual ensina como usar o sistema no dia a dia. Está dividido por
perfil de usuário — vá direto para a seção que interessa.

---

## Sumário

- [Primeira execução](#primeira-execução)
- [Como entrar no sistema](#como-entrar-no-sistema)
- [Para o Bibliotecário](#para-o-bibliotecário)
  - [Cadastrar um livro](#cadastrar-um-livro)
  - [Imprimir etiquetas de código de barras](#imprimir-etiquetas-de-código-de-barras)
  - [Corrigir o tombo de um exemplar](#corrigir-o-tombo-de-um-exemplar)
  - [Cadastrar um usuário](#cadastrar-um-usuário)
  - [Realizar um empréstimo](#realizar-um-empréstimo)
  - [Registrar uma devolução](#registrar-uma-devolução)
  - [Renovar um empréstimo](#renovar-um-empréstimo)
  - [Acompanhar a fila de espera](#acompanhar-a-fila-de-espera)
  - [Ver o uso do acervo](#ver-o-uso-do-acervo)
  - [Quitar multa](#quitar-multa)
  - [Emprestar o livro-texto para a turma inteira](#emprestar-o-livro-texto-para-a-turma-inteira)
  - [Gerar relatórios](#gerar-relatórios)
- [Para o Administrador](#para-o-administrador)
  - [Ajustar prazos e multas](#ajustar-prazos-e-multas)
  - [Fazer backup do banco](#fazer-backup-do-banco)
  - [Restaurar um backup](#restaurar-um-backup)
  - [Carregar dados de demonstração](#carregar-dados-de-demonstração)
- [Para o Aluno / Professor](#para-o-aluno--professor)
  - [Buscar um livro](#buscar-um-livro)
  - [Pegar emprestado pelo balcão](#pegar-emprestado-pelo-balcão)
  - [Ver seus empréstimos](#ver-seus-empréstimos)
- [Terminal de Autoatendimento](#terminal-de-autoatendimento)
- [Aplicativo no celular](#aplicativo-no-celular)
- [Perguntas frequentes](#perguntas-frequentes)

---

## Primeira execução

Quando o sistema é aberto pela primeira vez, ele exibe um **assistente
de configuração** com 3 passos rápidos:

1. **Boas-vindas** — explicação do que será feito.
2. **Instituição** — informe o nome da escola/biblioteca.
3. **Conta de administrador** — crie a primeira conta de acesso (matrícula,
   nome, senha).

Depois disso o sistema abre normalmente. Anote a matrícula e senha do
administrador em local seguro.

> **Importante:** essa conta tem acesso total. Trate-a como uma "chave
> mestra". Crie uma conta separada de bibliotecário para o uso diário e
> guarde a do admin só para configurações.

---

## Como entrar no sistema

1. Dê duplo-clique em **`SIGBEF.exe`**.
2. Digite sua **matrícula** e **senha**.
3. Clique em **Entrar**.

Se você esquecer a senha, procure o administrador — ele pode alterar pela
tela de Usuários.

Para abrir direto no modo de autoatendimento (sem passar pelo login
administrativo), use o atalho `SIGBEF.exe --autoatendimento`.

---

## Para o Bibliotecário

### Cadastrar um livro

1. No menu lateral, clique em **Livros e exemplares**.
2. Clique no botão **+ Cadastrar livro** (canto superior direito).
3. Preencha os campos:
   - **Título** (obrigatório)
   - **Autor(es)** — separe múltiplos autores por ponto-e-vírgula. Ex.:
     `Thomas Cormen; Charles Leiserson`
   - **ISBN, Editora, Categoria, Ano, Edição** (opcionais mas
     recomendados)
   - **Localização** — onde o livro fica fisicamente. Ex.: *"Estante A —
     Prateleira 3"*
   - **Quantidade de exemplares** — quantas cópias estão entrando.
4. Clique em **Salvar livro**.

O sistema gera automaticamente um **código de barras único** para cada
exemplar.

### Imprimir etiquetas de código de barras

1. Na lista de livros, clique duplo no livro desejado (ou selecione e
   clique em **Ver detalhes**).
2. Na janela de detalhes, role até **Exemplares e códigos de barras**.
3. Clique em **Imprimir etiquetas (visualizar)**.
4. Use a função "Imprimir" do navegador/captura de tela ou tire foto da
   tela para preparar a impressão real em uma impressora de etiquetas.

Para imprimir de vários livros de uma vez, veja **Etiquetas em massa**
nas perguntas frequentes.

### Corrigir o tombo de um exemplar

O tombo é o número escrito no livro físico. Ele chega errado com
frequência: a importação da planilha trouxe o número trocado, ou o
dígito escrito à mão estava ilegível.

1. Abra o livro em **Ver detalhes**.
2. Na lista de exemplares, clique no exemplar errado.
3. Clique em **Corrigir tombo**, digite o número certo e salve.

O exemplar mantém o código de barras, os empréstimos e o histórico: só o
número muda, e ele sai atualizado na próxima etiqueta.

**O tombo não pode se repetir.** Se você digitar um número que já está em
outro exemplar, o sistema recusa e diz qual livro está usando. Isso não é
frescura: o balcão procura o exemplar pelo código de barras ou pelo
tombo, e dois iguais fariam o empréstimo registrar o livro errado.

### Cadastrar um usuário

1. Menu lateral → **Usuários** → **+ Cadastrar usuário**.
2. Preencha:
   - **Nome completo**
   - **Matrícula** — apelido curto que o usuário vai digitar no login.
     Ex.: `2024001` para aluno, `bib003` para bibliotecário.
   - **E-mail** e **telefone** (opcionais)
   - **Perfil** — escolha entre Aluno, Professor, Bibliotecário ou
     Administrador.
   - **Senha inicial** — peça para o usuário trocar no primeiro acesso.
   - **Gerar cartão** — deixe marcado para criar um código de barras de
     cartão que o aluno pode usar no autoatendimento.
3. Clique em **Cadastrar**.

O sistema mostra o código do cartão gerado — anote ou imprima.

### Realizar um empréstimo

**Caminho A — você sabe a matrícula e o código:**

1. Menu lateral → **Empréstimos abertos**.
2. No card **Empréstimo rápido**, digite a matrícula e o código.
3. Clique em **✓ Registrar empréstimo**.

**Caminho B — usar os botões de seleção:**

1. Clique em **Buscar usuário...** e selecione o aluno na lista.
2. Clique em **Selecionar exemplar...** — abre uma lista com todos os
   livros disponíveis (você pode buscar por título ou autor).
3. Dê duplo-clique no exemplar desejado.
4. Clique em **✓ Registrar empréstimo**.

A mensagem verde abaixo do formulário confirma o sucesso e mostra a data
prevista de devolução.

> **Tolerância na digitação:** o sistema aceita tanto o **código de
> barras** (ex.: `EX2604301...`) quanto o **número de tombo**
> (ex.: `00001-001`). E para o usuário aceita tanto a **matrícula**
> quanto o **código do cartão**.

### Registrar uma devolução

1. Menu lateral → **Empréstimos abertos**.
2. No card **Devolução rápida**, digite o código de barras ou tombo do
   exemplar.
3. Clique em **↻ Registrar devolução**.

Se houver atraso, o sistema calcula a multa automaticamente e mostra na
caixa de confirmação.

### Renovar um empréstimo

1. Em **Empréstimos abertos**, selecione a linha desejada.
2. Clique em **Renovar selecionado**.
3. A data prevista é estendida pelo prazo padrão do perfil.

### Acompanhar a fila de espera

Quando um livro está todo emprestado, o leitor pode entrar na fila —
pelo balcão ou pelo aplicativo, sem falar com ninguém. Esta tela mostra
tudo o que está na fila.

1. Menu lateral → **Fila de espera**.
2. As linhas **destacadas** são as que pedem atenção: o exemplar já foi
   separado e está esperando o aluno aparecer. A coluna **Situação**
   traz até quando ele pode retirar e o número de tombo, para você achar
   o livro na prateleira de reservados.
3. Passado o prazo de retirada, o sistema libera o exemplar sozinho: ele
   vai para o próximo da fila ou volta para a estante.
4. Para tirar alguém da fila, selecione a linha e clique em **Cancelar
   reserva selecionada**.

Você não precisa avisar o aluno manualmente: quando o livro é devolvido,
o sistema separa o exemplar e — se o aviso por e-mail estiver ligado em
Configurações — manda a mensagem.

### Quitar multa

1. Em **Empréstimos abertos**, selecione o empréstimo com multa.
2. Clique em **Quitar multa**.
3. Confirme. A multa zera e o usuário fica liberado para novos
   empréstimos.

### Ver o uso do acervo

Menu lateral → **Uso do acervo**. Os relatórios em CSV contam *o que
aconteceu*; esta tela ajuda a decidir *o que fazer*.

No topo, quatro números:

| Número | O que significa |
|---|---|
| **% do acervo já emprestado** | Quanto do que está na estante já circulou alguma vez |
| **Livros nunca emprestados** | O acervo parado — o dado mais acionável da tela |
| **Leitores nos últimos 30 dias** | Quantas pessoas diferentes pegaram livro |
| **% de devoluções atrasadas** | Fica vermelho a partir de 20% |

Abaixo vêm os gráficos: empréstimos mês a mês (mostra se a biblioteca
está viva e quando houve queda), turmas que mais leem e categorias mais
procuradas.

O botão **Ver livros parados** abre a lista completa dos títulos que
nunca saíram, e **Exportar CSV** salva essa lista para levar à
coordenação. Vale lembrar: livro que ninguém pega raramente é livro
ruim — quase sempre é livro que ninguém viu. A lista serve para montar
exposição, indicar em sala ou rever a próxima compra.

### Gerar relatórios

1. Menu lateral → **Relatórios**.
2. Se quiser recortar um período, use a faixa no topo da tela. Os
   botões **Este mês**, **Este bimestre** e **Este ano** preenchem as
   datas sozinhos; **Tudo** volta ao histórico completo. Também dá para
   digitar as datas no formato dd/mm/aaaa.
3. Escolha um dos 6 relatórios disponíveis:
   - **Acervo completo** — todos os livros e exemplares
   - **Empréstimos em aberto** — quem está com livros agora
   - **Usuários cadastrados** — listagem completa
   - **Mais emprestados** — livros mais procurados no período
   - **Pendências dos leitores** — quem está impedido de pegar livro
   - **Movimentação do período** — empréstimos, devoluções, atrasos e
     multas, com a quebra por mês e por turma
4. Clique em **Exportar CSV** e escolha onde salvar.

O período vale para os relatórios de movimento (mais emprestados e
movimentação). Acervo, usuários e pendências ignoram as datas de
propósito: eles são uma fotografia de agora, não um histórico.

**Movimentação do período** é o relatório para levar à direção no fim do
bimestre ou do ano. Ele responde numa página: quantos empréstimos, quantas
devoluções, quantas em atraso, quanto de multa e quais turmas leram mais.

O relatório de pendências traz o e-mail e a turma de cada um, porque ele
costuma virar cobrança. Repare que ele lista **duas** situações
diferentes: quem já devolveu com atraso e ficou devendo multa, e quem
ainda está com o livro em casa depois do prazo. O segundo caso não tem
multa lançada — ela só nasce na devolução —, mas é o mais urgente,
porque o livro está fora da biblioteca. Por isso a lista vem ordenada
pelo atraso mais antigo.

O CSV pode ser aberto no Excel ou Google Sheets para análises adicionais.

### Devolver vários livros de uma vez

No fim do ano a turma inteira devolve junto, e confirmar um por um leva
a tarde toda.

1. Menu lateral → **Empréstimos abertos** → **Devolver em lote**.
2. Vá passando o leitor. Cada leitura já devolve — não aparece janela de
   confirmação.
3. A lista mostra o que foi devolvido, de quem era, o atraso e a multa.
4. Se um livro for recusado (código errado, ou exemplar que não estava
   emprestado), aparece um aviso em vermelho e **a pilha continua**.
   Resolva aquele no fim.
5. Clique em **Concluir** para ver o total.

No resumo, preste atenção na lista **"separar da estante"**: são os
livros que alguém está esperando na fila. Esses não voltam para a
prateleira — vão para o balcão de reservados.

### Emprestar o livro-texto para a turma inteira

Trinta exemplares do mesmo livro saem no começo do bimestre e voltam no
fim. Registrar um por um dá trinta linhas iguais na tela — por isso
existe a **coleção**: sai num registro só e volta de uma vez.

1. Menu lateral → **Empréstimos abertos** → **Emprestar coleção...**.
2. **Selecionar...** o livro. A janela mostra quantos exemplares estão
   disponíveis agora, e já sugere esse número na quantidade.
3. Informe a **matrícula do professor** (ou use **Selecionar...**) e a
   **turma**.
4. Ajuste a quantidade e clique em **Emprestar coleção**.

Na lista de empréstimos, a coleção aparece como **uma linha**, com a
palavra "coleção" na primeira coluna e em negrito. Para receber tudo de
volta: selecione essa linha e clique em **Devolver coleção** (ou dê um
duplo clique nela).

**O que é diferente de um empréstimo comum:**

- **Fica no nome do professor, com a turma anotada.** É ele quem
  responde pelos trinta livros. A turma vai junto porque o mesmo
  professor pode levar coleções para turmas diferentes no mesmo
  bimestre — sem isso, ninguém sabe qual pilha é de quem no fim.
- **O prazo é de bimestre** (60 dias por padrão, ajustável em
  Configurações), não os 14 dias do professor.
- **Não conta no limite de empréstimos simultâneos.** O limite existe
  para ninguém monopolizar o acervo; livro-texto da turma é o oposto
  disso.
- **Multa em aberto continua bloqueando.** Essa regra é sobre
  responsabilidade, e trinta livros pesam mais, não menos.
- **Exemplar reservado não entra na coleção.** Ele já está separado para
  alguém da fila.

Se um aluno devolver o exemplar dele avulso, no balcão, tudo bem: a
devolução da coleção recebe o que ainda estiver fora.

### Tirar um exemplar do acervo

Um livro voltou rasgado, o aluno perdeu, ou a coleção ficou
desatualizada. Isso é diferente de excluir o livro: aqui sai **um
exemplar**, e os outros do mesmo título continuam na estante.

1. Menu lateral → **Livros e exemplares**, selecione o livro e clique em
   **Ver detalhes / código de barras**.
2. Na lista de exemplares, clique no que vai sair e depois em **Dar
   baixa no exemplar**.
3. Escolha o motivo:
   - **Extraviado** — não foi encontrado
   - **Danificado** — sem conserto
   - **Descartado** — desatualizado ou fora de uso
   - **Doado ou transferido**
4. Confirme.

O motivo não é burocracia: seis meses depois, "extraviado" e "descartado
por estar velho" levam a decisões diferentes na hora de repor a estante.

**Se o exemplar estiver emprestado** — o caso do aluno que perdeu o
livro — o sistema avisa e, ao confirmar, encerra o empréstimo e lança a
multa de atraso, se houver. Não é preciso esperar uma devolução que não
vai acontecer. O histórico de quem leu aquele exemplar continua
guardado.

### Conferir o acervo (inventário)

A conferência de fim de ano: passar o leitor na estante e descobrir o
que sumiu. Pode ser feita em vários dias — a conferência fica aberta até
você encerrar.

1. Menu lateral → **Conferir acervo** → **Iniciar conferência**.
2. Passe o leitor em cada exemplar da estante. O cursor já fica no campo
   certo e volta sozinho depois de cada leitura, então dá para trabalhar
   com as duas mãos na estante.
3. A tela vai avisando:
   - **Conferido** — tudo certo
   - **Já tinha sido lido** — você passou esse livro duas vezes; não
     conta em dobro, pode seguir
   - **Estava emprestado!** ou **Estava baixado!** — o livro está na
     estante, mas o sistema achava que não. Anote para corrigir
4. Quando terminar, clique em **Encerrar conferência**.

O resultado sai em três listas, e cada uma pede uma ação diferente:

| Lista | O que fazer |
|---|---|
| **Não encontrados** | Procurar na estante. Se não achar, dar baixa como extraviado |
| **Emprestados** | Nada. Estão com os leitores, como esperado |
| **Apareceram** | Corrigir o cadastro: o sistema está errado sobre esses |

Use **Exportar CSV** para levar a lista impressa até a estante.

Só uma conferência pode estar aberta por vez. Se duas pessoas contassem
ao mesmo tempo em conferências diferentes, cada uma acusaria como sumido
o que a outra encontrou.

---

## Para o Administrador

### Ajustar prazos e multas

1. Menu lateral → **Configurações** (visível só para o admin).
2. Ajuste os valores:
   - **Prazo aluno/professor** (em dias)
   - **Limite de empréstimos simultâneos** por perfil
   - **Multa por dia** e **Teto máximo** (em reais)
   - **Nome da instituição**
3. Clique em **Salvar configurações**. As mudanças entram em vigor
   imediatamente.

### Fazer backup do banco

1. Menu lateral → **Configurações**.
2. Role até **Ferramentas** → **Backup do banco de dados**.
3. Clique em **Fazer backup agora**.
4. Escolha onde salvar (ex.: pendrive, pasta de rede, OneDrive).

> **Recomendação:** faça backup diário ou semanal e guarde **fora do
> computador da biblioteca** (pendrive, nuvem).

### Restaurar um backup

Use quando o banco se perdeu, ficou corrompido, ou alguém apagou algo
que não devia. **Restaurar apaga o acervo de hoje e põe o do arquivo no
lugar** — não é uma mesclagem.

1. Menu lateral → **Configurações**.
2. Role até **Ferramentas** → **Restaurar um backup**.
3. Clique em **Restaurar backup...** e escolha o arquivo `.db`.
   A janela já abre na pasta de backups.
4. O sistema confere o arquivo e mostra os dois lados: quantos livros,
   exemplares, usuários e empréstimos em aberto há **hoje** e quantos há
   **no arquivo**. Os números diferentes aparecem em destaque — é
   exatamente essa diferença que se perde.
5. Digite **RESTAURAR** no campo e clique em **Restaurar**.
6. Feche e abra o sistema.

**O que o sistema faz por você:**

- Recusa arquivo que não seja um banco do SIGBEF, antes de mexer em
  qualquer coisa. Se o arquivo não servir, o acervo de hoje continua
  intacto.
- Guarda uma cópia do banco de hoje antes de trocar, na pasta de
  backups, com o nome `sigbef_antes_da_restauracao_<data>.db`. A limpeza
  automática de backups **não** apaga esse arquivo. Se você restaurou o
  arquivo errado, restaure essa cópia e tudo volta.
- Atualiza a estrutura do banco, caso o backup seja de uma versão antiga
  do sistema.

> **Não copie o `.db` por fora.** O banco usa um arquivo auxiliar de
> transações (`-wal`); trocar só o `.db` pelo Explorador produz uma
> cópia que abre e está pela metade — o pior tipo de defeito, o que
> parece que deu certo. É por isso que esta tela existe.

### Carregar dados de demonstração

Útil quando você quer testar o sistema com dados de exemplo antes de
cadastrar o acervo real, ou para treinar novos funcionários.

1. Menu lateral → **Configurações** → **Ferramentas**.
2. Clique em **Carregar dados de demonstração**.
3. Confirme.

Serão adicionados 10 livros e 4 usuários de exemplo. **As senhas desses
usuários são públicas e devem ser trocadas (ou as contas removidas)
antes do uso em produção.**

---

## Para o Aluno / Professor

### Buscar um livro

1. Faça login com sua matrícula e senha.
2. Menu lateral → **Pesquisar livros**.
3. Digite título, autor ou categoria no campo de busca.
4. Marque **Apenas disponíveis** para ver só os que estão na estante.
5. Clique em **Buscar**.

A coluna **Disponíveis** mostra "X/Y" — quantos exemplares estão livres
do total.

### Pegar emprestado pelo balcão

Se você está no painel comum (não no autoatendimento):

1. Selecione o livro na lista de pesquisa.
2. Clique em **✓ Pegar emprestado**.
3. Confirme.

O sistema escolhe automaticamente um exemplar disponível e registra o
empréstimo no seu nome.

> **Bloqueios:** se você tem livros em atraso ou multa em aberto, o
> empréstimo será recusado com uma mensagem explicando o motivo.

### Ver seus empréstimos

1. Menu lateral → **Meus empréstimos**.
2. A lista mostra todos os seus empréstimos (passados e atuais):
   - **Atrasados** ficam em vermelho.
   - **Já devolvidos** ficam em cinza.
3. No topo, uma mensagem indica seu status (quantos empréstimos abertos
   e se há restrições).

---

## Terminal de Autoatendimento

O terminal de autoatendimento é uma tela simplificada, ideal para um
computador com tela touch dedicado.

### Como abrir

- **No próprio computador da biblioteca:** use o atalho
  *"SIGBEF (Autoatendimento)"* criado pelo instalador.
- **Manualmente:** abra um prompt e rode:
  ```
  SIGBEF.exe --autoatendimento
  ```

### Como o aluno usa

1. **Login:** digita a matrícula + senha, OU aproxima o cartão do leitor
   de código de barras (campo "ou aproxime seu cartão").
2. **Tela inicial** mostra 3 botões grandes:
   - **Pegar emprestado** — verde
   - **Devolver** — laranja
   - **Meus empréstimos** — azul
3. Para **pegar emprestado**:
   - Tocar em "Pegar emprestado"
   - Aproximar o livro do leitor (ou digitar o código)
   - Confirmar — o comprovante aparece com a data de devolução
4. Para **devolver**: igual ao processo de empréstimo, escolhendo
   "Devolver" no menu inicial. Se houver multa, o sistema avisa para
   passar no balcão.
5. **Encerrar sessão:** botão vermelho no canto inferior direito, ou
   automático após **90 segundos** de inatividade.

---

## Aplicativo no celular

O SIGBEF tem um aplicativo Android para alunos e professores. Ele não
substitui o balcão: emprestar e devolver continuam exigindo o livro na
mão. Serve para tudo o mais.

O aplicativo **não usa internet nem nuvem**. Conversa só com o
computador da biblioteca, pela rede Wi-Fi da escola. Nenhum dado do
aluno sai dali.

### Parear o celular (uma vez só)

1. **Na biblioteca:** Configurações → Integrações → **Parear celular**.
   Um QR code aparece na tela, junto do endereço em texto.
2. **No celular:** abrir o app, tocar em **Ler o QR da biblioteca** e
   apontar a câmera. Quem preferir pode digitar o endereço.
3. Entrar com a **mesma matrícula e senha** do sistema.

O QR **não contém senha nem token**, de propósito: ele fica exposto na
tela do computador, e quem o fotografasse ganharia acesso indevido.

Em Configurações → Integrações, você vê quantos celulares estão pareados
e pode **desconectar todos** de uma vez — útil quando um aluno perde o
aparelho ou no fim do ano letivo.

### O que o aluno faz pelo app

- Consulta o acervo e abre a ficha do livro (com tombo e sinopse)
- Vê os próprios empréstimos, prazos, atrasos e o histórico
- **Renova** um empréstimo, se as regras permitirem
- **Entra na fila de espera** de um livro emprestado, e sai dela
- Mostra o **cartão digital** com código de barras — funciona sem
  internet, e o leitor do balcão lê direto da tela do celular
- Em **Minha leitura**, vê quanto já leu e recebe sugestões de livros

### Quando a renovação é recusada

O app mostra o motivo na própria tela, no lugar do botão:

| Motivo | Por quê |
|---|---|
| O prazo já venceu | Livro atrasado precisa passar pelo balcão |
| Outro leitor está na fila | Quem espera tem prioridade sobre quem renova |
| Limite de renovações atingido | Padrão: 2 renovações seguidas (ajustável) |

No balcão essas regras não valem: você tem o aluno na frente e o
contexto que o sistema não tem, então continua podendo renovar em
qualquer situação.

### Se o app não achar a biblioteca

A causa mais comum **não** é o endereço errado: é o Wi-Fi da escola com
**isolamento de clientes** ligado (também chamado de "AP isolation" ou
"modo visitante"). Esse recurso impede que dois aparelhos da mesma rede
se enxerguem — o celular acessa a internet normalmente, mas nunca acha o
computador da biblioteca.

Para confirmar: abra `http://ENDEREÇO:8765/api/v1/ping` no navegador do
celular. Se der erro de endereço inacessível, é a rede. A solução é
desligar essa opção na administração do roteador — peça a quem cuida da
rede da escola.

---

## Perguntas frequentes

**Esqueci a senha do administrador. E agora?**
Como medida de segurança, não há recuperação automática. Se você tem
acesso ao arquivo `sigbef.db` em `%APPDATA%\SIGBEF\`, peça ajuda a um
técnico para resetar a senha via SQLite. Se não, é necessário começar do
zero (renomeie o `.db` antigo para `.db.backup` e reabra o sistema — vai
disparar o assistente de configuração novamente).

**Onde fica o banco de dados?**
- **Quando rodando o `.exe`:** `%APPDATA%\SIGBEF\sigbef.db`
- **Quando rodando o código-fonte:** `<pasta-do-projeto>\data\sigbef.db`

**Posso usar em vários computadores ao mesmo tempo?**
Esta versão (1.0) usa SQLite local — não suporta acesso simultâneo de
múltiplos PCs ao mesmo banco. Para essa necessidade, planeje a migração
para PostgreSQL (consulte o desenvolvedor).

**Como funciona o código de barras?**
- Cada **exemplar** tem um código único do tipo `EX260430110856####`.
- Cada **usuário** ganha um código de cartão do tipo `US...` se a opção
  "Gerar cartão" estiver marcada no cadastro.
- O sistema aceita códigos lidos por qualquer leitor USB padrão
  (o leitor age como um teclado que "digita" o código e dá Enter).
- Também aceita o **número de tombo** se você preferir digitar
  manualmente (ex.: `00001-001`).

**Como imprimir etiquetas de código de barras em massa?**
Em **Livros e exemplares**, botão **Etiquetas em massa**. A página abre
no navegador, e daí é Ctrl+P para imprimir ou salvar em PDF.

O que entra na impressão depende do que está marcado na lista:

- **Livros marcados**: só eles. É o caso de chegarem seis livros novos
- **Nada marcado, com busca preenchida**: tudo o que a busca encontrou
- **Nada marcado, busca vazia**: o acervo inteiro

Exemplar baixado não recebe etiqueta.

**O sistema funciona em rede?**
Não nesta versão. Mas o banco pode ficar em pasta compartilhada e ser
acessado por **um** computador por vez (sem concorrência).

**Posso traduzir o sistema para outro idioma?**
Por enquanto o sistema está em pt-BR. A estrutura está preparada para
i18n (internacionalização), mas as strings ainda não estão extraídas.

**Onde posso reportar um problema ou sugerir melhoria?**
Use a aba **Issues** do repositório do GitHub, ou contate o
desenvolvedor.

---

*Manual atualizado para a versão 1.0 — Maio/2026.*
