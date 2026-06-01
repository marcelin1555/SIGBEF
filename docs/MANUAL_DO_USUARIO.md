# Manual do Usuário — SIGBEF v1.0

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
  - [Cadastrar um usuário](#cadastrar-um-usuário)
  - [Realizar um empréstimo](#realizar-um-empréstimo)
  - [Registrar uma devolução](#registrar-uma-devolução)
  - [Renovar um empréstimo](#renovar-um-empréstimo)
  - [Quitar multa](#quitar-multa)
  - [Gerar relatórios](#gerar-relatórios)
- [Para o Administrador](#para-o-administrador)
  - [Ajustar prazos e multas](#ajustar-prazos-e-multas)
  - [Fazer backup do banco](#fazer-backup-do-banco)
  - [Carregar dados de demonstração](#carregar-dados-de-demonstração)
- [Para o Aluno / Professor](#para-o-aluno--professor)
  - [Buscar um livro](#buscar-um-livro)
  - [Pegar emprestado pelo balcão](#pegar-emprestado-pelo-balcão)
  - [Ver seus empréstimos](#ver-seus-empréstimos)
- [Terminal de Autoatendimento](#terminal-de-autoatendimento)
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

### Quitar multa

1. Em **Empréstimos abertos**, selecione o empréstimo com multa.
2. Clique em **Quitar multa**.
3. Confirme. A multa zera e o usuário fica liberado para novos
   empréstimos.

### Gerar relatórios

1. Menu lateral → **Relatórios**.
2. Escolha um dos 4 relatórios disponíveis:
   - **Acervo completo** — todos os livros e exemplares
   - **Empréstimos em aberto** — quem está com livros agora
   - **Usuários cadastrados** — listagem completa
   - **Top 50 mais emprestados** — livros mais procurados
3. Clique em **Exportar CSV** e escolha onde salvar.

O CSV pode ser aberto no Excel ou Google Sheets para análises adicionais.

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
> computador da biblioteca** (pendrive, nuvem). Em caso de pane, basta
> substituir o arquivo `sigbef.db` em `%APPDATA%\SIGBEF\` pelo backup.

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
A versão 1.0 mostra as etiquetas em tela. Para imprimir em rolo, será
necessário integrar uma biblioteca de geração de PNG/SVG (planejado para
1.1) ou exportar o relatório de Acervo e usar um software de etiquetas
externo.

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
