# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

## [1.7.1] — 2026-07-27

Versão de desempenho: nenhuma função nova, nada mudou de lugar na tela.
O sistema passou a aguentar **250 mil livros** onde antes começava a
doer em 100 mil — e em 25 mil, se a turma inteira estivesse no celular
ao mesmo tempo.

**Atenção a quem integra outro sistema:** `GET /api/v1/livros` passou a
responder em páginas. Quem varria o acervo numa chamada só precisa
iterar `pagina` até `paginas`. Detalhes em `docs/API.md`.

### O acervo deixa de ser carregado inteiro

Um teste de estresse mediu o teto do sistema: **100 mil livros sozinho,
25 mil com uma turma inteira no celular ao mesmo tempo**. O que segurava
esse número era sempre a mesma coisa — nada limitava o tamanho do
resultado, então cada tela, cada resposta da API e cada sincronização do
app carregava o acervo completo para mostrar as vinte linhas visíveis.

Depois das mudanças abaixo, **250 mil livros passam em tudo**, inclusive
com 40 alunos buscando no mesmo instante.

- **Listagem por páginas** (`servicos.listar_livros` ganhou `limite` e
  `offset`, e há um `contar_livros` novo). Cada linha da listagem carrega
  três subconsultas, então o custo é por linha devolvida: pedir 50 de um
  acervo de 250 mil passou de 7,2 s para 5 ms. Quem exporta CSV continua
  recebendo tudo, porque ali é o que se quer mesmo
- O filtro "apenas disponíveis" migrou para o SQL. Era aplicado em
  Python depois da consulta, e com o limite isso cortaria a página antes
  de saber quais linhas sobrevivem
- **`GET /api/v1/livros` responde em páginas** (`pagina` e `limite`, até
  500 por vez), com `total` e `paginas` na resposta. Antes serializava o
  acervo inteiro: 57 MB num JSON só, com 250 mil livros
- **O aplicativo sincroniza o acervo em blocos**, e a lista fica usável
  enquanto o resto ainda baixa. O catálogo antigo só é apagado depois
  que a primeira página nova chega, para uma queda de rede no meio não
  deixar o aluno sem catálogo nenhum
- **As telas de acervo carregam 500 livros por vez**, com a contagem do
  que ficou de fora e um botão para trazer mais. A lista era preenchida
  linha a linha na mesma thread que desenha a janela: 250 mil livros
  davam 9,8 segundos de tela congelada, agora são 0,11 s sem
  travamento nenhum

### Empréstimo de balcão deixa de varrer a tabela

- **Índice novo em `exemplar(numero_tombo)`.** O empréstimo procura o
  exemplar por código de barras **ou** tombo; o código já era indexado
  pela restrição UNIQUE, o tombo não, e com um lado sem índice o SQLite
  varria a tabela inteira a cada atendimento. Com 500 mil exemplares
  isso custava 1,3 segundo por empréstimo — agora são 3 ms. O índice é
  criado sozinho na primeira abertura, sem migração manual

### A turma inteira consegue abrir o app junto

- **Fila de conexões da API subiu de 5 para 128.** O padrão herdado do
  Python deixa cinco conexões esperando para serem aceitas, e a sexta
  leva recusa do sistema operacional. Com 80 aparelhos abrindo o app no
  mesmo minuto, 42 recebiam "sem conexão com a biblioteca" — com a
  biblioteca no ar. Agora nenhum

## [1.7.0] — 2026-07-26

A biblioteca sai do computador da bibliotecária. Até aqui o aluno só
tinha o balcão e o terminal de autoatendimento; agora ele resolve no
próprio celular o que antes exigia pedir para alguém — e ela ganha as
telas para enxergar o que passou a acontecer sem a mão dela.

O aplicativo estreia com numeração própria, **0.1**: ele evolui em
ritmo diferente do desktop e não faz sentido amarrar os dois.

### Pendências dos leitores (RF-052)

Último requisito funcional da versão 1.0 que seguia em aberto. O sistema
já bloqueava o leitor inadimplente e mostrava a multa na ficha dele, mas
não havia como perguntar "quem está devendo?" sem abrir usuário por
usuário.

- Novo relatório em **Relatórios → Pendências dos leitores**, exportado
  em CSV com nome, matrícula, turma, e-mail, exemplares em atraso, dias
  do atraso mais antigo e multa
- Cobre as **duas** causas de bloqueio, não só a multa: quem ainda está
  com o livro da escola em casa aparece na lista mesmo sem multa lançada
  — ela só nasce na devolução
- Ordenado pelo atraso mais antigo, que é por onde a cobrança começa

### Reserva e renovação pelo celular

O aluno passa a resolver sozinho o que antes exigia ir ao balcão para
pedir. São as **três únicas** gravações que a API aceita, sempre nos
dados do próprio aluno logado — o acervo continua intocável pela rede, e
emprestar/devolver seguem sendo do balcão porque exigem o livro na mão.

- **Entrar e sair da fila de espera** pelo app, direto na ficha do livro.
  A fila, o aviso por e-mail e a separação do exemplar já existiam no
  desktop desde a 1.6.0; o que faltava era o aluno alcançá-los
- **Renovar o empréstimo** pelo app, com o novo prazo aparecendo na hora
- **Regras de renovação explícitas** (`servicos.pode_renovar`): não renova
  livro atrasado, livro com alguém na fila, nem depois do limite de
  renovações (`LIMITE_RENOVACOES`, padrão 2, novo). Antes não havia regra
  nenhuma — quem julgava era a bibliotecária, olhando o caso. **No balcão
  isso não muda**: ela continua podendo renovar em qualquer situação,
  porque tem o aluno na frente e o contexto que o sistema não tem
- A recusa vem do servidor já escrita para o aluno ("Outro leitor está
  esperando por este livro"), em vez de o app inventar a explicação
- Empréstimos passam a contar quantas vezes foram renovados
- **Fila de espera no painel** (Bibliotecário → Fila de espera): quem
  está esperando cada livro, a posição de cada um e quais exemplares já
  estão separados aguardando retirada, com o prazo e o tombo. É a
  contrapartida da reserva pelo celular: enquanto reservar exigia ir ao
  balcão, a bibliotecária sabia da fila porque ela mesma a criava; agora
  o aluno entra sozinho, e ela precisava de onde consultar. Dá para
  cancelar uma reserva por ali, com registro em auditoria

### Leitura do QR pela câmera

- O app lê o QR de pareamento apontando a câmera, em vez de exigir que o
  aluno digite o IP. A permissão é pedida na hora de escanear, não na
  abertura; a imagem é analisada em memória e descartada, nada é gravado
  nem enviado
- Digitar o endereço continua disponível o tempo todo — aparelho sem
  câmera ou QR ilegível não podem deixar ninguém sem saída
- O leitor é embarcado no APK, sem depender do Google Play Services, que
  nem sempre está presente nos aparelhos dos alunos. Em troca ele traz um
  motor nativo pesado, então o release passou a gerar **um APK por
  arquitetura**: o aluno instala 19 MB em vez de 35 MB
- Verificado em aparelho real (Xiaomi, Android 15) contra o acervo de
  verdade: ler o QR, parear, entrar, consultar os 2.867 livros, reservar
  e renovar

### Histórico de empréstimos no app

- A rota do leitor passa a devolver `historico` com os empréstimos já
  devolvidos (os 20 mais recentes — quem estuda há anos acumula
  centenas, e a tela mostra só os últimos). A tela do app já tinha a
  seção pronta e um botão "Ver todo o histórico" que **não fazia nada**:
  o dado nunca chegava. O botão saiu; o histórico chegou

### Empacotamento do app

- `docs/COMO_GERAR_APK.md`: como gerar a chave, assinar e qual dos APKs
  entregar. A chave e as senhas ficam fora do repositório, em variável
  de ambiente
- `.gitignore` do app passa a barrar `*.jks`, `*.keystore` e
  `keystore.properties`. Uma chave versionada por acidente permitiria a
  qualquer um publicar atualização no lugar da escola — e chave vazada
  não se revoga, só se troca, obrigando todo aluno a reinstalar
- Build de release com a chave presente mas sem as senhas agora falha
  dizendo exatamente o que falta, em vez de quebrar lá na frente

### Documentação revisada de ponta a ponta

- **Documento de Requisitos v2.0**: a versão 1.0 (abril) era um plano —
  propunha duas pilhas tecnológicas, listava o aplicativo móvel como fora
  de escopo e trazia um cronograma em fases. A nova versão registra o que
  existe, com a **situação de cada um dos 40 requisitos** conferida
  contra o código, e a comparação entre o que foi proposto e o que foi
  implementado em tecnologia. O planejamento original ficou preservado
  como `SIGBEF_Documento_Requisitos_v1.0_abril2026.docx`
- Dois requisitos da v1.0 continuam **em aberto**, e agora estão
  registrados como tal: RF-052 (relatório de inadimplência) e RNF-10
  (internacionalização)
- README, manual do usuário, roteiro de treinamento e README do
  aplicativo atualizados: badge de versão, funcionalidades novas, árvore
  do projeto, como rodar os testes, e as telas de fila de espera e uso do
  acervo, que não estavam documentadas em lugar nenhum

### Requisito de rede para implantar

O teste em celular revelou algo que vale conferir em **cada escola**
antes de instalar: o Wi-Fi não pode ter **isolamento de clientes** (o
mesmo recurso chamado de "AP isolation" ou "modo visitante"). Com ele
ligado, o celular enxerga a internet mas não enxerga o computador da
biblioteca, e o app não consegue parear — mesmo com o endereço certo e
os dois na mesma rede. Como reconhecer e como resolver: `docs/SIGBEF_MOBILE.md` §7.

### Aplicativo de celular (base no desktop)
- **Parear celular**: novo botão em Configurações → Integrações que mostra
  um QR code com o endereço do servidor na rede da escola. O QR **não
  carrega senha nem token** — ele fica exposto na tela, então quem
  fotografasse ganharia acesso aos dados de todos os leitores. Também
  mostra o endereço em texto, para digitar quando a câmera falhar
- **Login pelo aplicativo** (`POST /api/v1/login`): o aluno entra com a
  mesma matrícula e senha do sistema e recebe um acesso preso a ele, com
  validade. Pedir os empréstimos de outro aluno agora devolve erro — antes,
  quem tivesse o token do sistema via a vida de leitura de todo mundo
- Contador de celulares pareados e botão para desconectar todos de uma
  vez (aparelho perdido, fim de ano letivo)
- Gerador de QR Code próprio, escrito em Python puro: o sistema continua
  sem nenhuma dependência externa para funcionar
- A situação do leitor (`/usuarios/{matricula}/emprestimos`) passa a
  informar o limite de empréstimos do perfil, para o app mostrar quantos
  livros ainda cabem

### Aplicativo Android (sigbef-mobile)

O aplicativo, que era uma demonstração com dados fictícios, passou a
funcionar de verdade contra a biblioteca:

- Conecta na API real da escola (busca no acervo, ficha do livro com
  tombo e sinopse, empréstimos do próprio aluno), com o Room servindo só
  de cache para o uso offline
- Login de verdade com matrícula e senha; o endereço da biblioteca vem do
  pareamento e é validado como rede local antes de aceitar (o app não fala
  com host arbitrário da internet, já que a senha trafega em rede local)
- Cartão de biblioteca com **código de barras Code 128 real**, lido pelo
  mesmo leitor do balcão (antes era um desenho que nenhum leitor decifrava)
- Removidos todos os dados de exemplo embutidos. Os botões de reservar e
  renovar, que fingiam funcionar (a bibliotecária nunca recebia o pedido),
  foram refeitos para valer — ver "Reserva e renovação pelo celular"
- Botão de sair da conta e de trocar de biblioteca, com limpeza do que
  ficava guardado no aparelho

### Interface
- Ícones nos 3 cards grandes do menu principal do autoatendimento
  (Pegar emprestado, Devolver, Meus empréstimos), que tinham ficado
  de fora da rodada anterior de identidade visual

### Site
- Página **Eventos** (`/eventos`) com galeria de fotos e lightbox,
  estreando com o V Seminário e II Colóquio de EPT da Rede Estadual
  do RN (Natal, jul/2026), onde o SIGBEF foi apresentado

## [1.6.2] — 2026-07-19

### Interface
- Identidade visual completa em todas as telas: logo do SIGBEF (em
  plaqueta branca, legível sobre qualquer paleta) no login, no
  assistente de primeira execução, no autoatendimento e no diálogo
  Sobre; brasão da instituição também no autoatendimento; e a logo
  como ícone das janelas (barra de título e barra de tarefas), no
  lugar do ícone padrão do Tk
- Paletas de verdade: os textos secundários sobre a cor primária
  (subtítulos de cabeçalho, versão no login, avisos do kiosk) agora
  derivam da paleta escolhida, em vez dos tons de azul fixos que
  destoavam em temas como o marrom; o efeito de clique dos botões do
  kiosk também acompanha a paleta
- Botões de ação com ícones vetoriais no lugar de símbolos de texto
  (cadastrar, registrar empréstimo, devolução, aviso de sessão do
  kiosk)
- Brasão da instituição: em Configurações, Aparência, o administrador
  pode escolher uma imagem (PNG ou GIF, até 512 KB) que passa a
  aparecer na tela de login e no cabeçalho do painel. A imagem fica
  guardada dentro do próprio banco, então o backup de 1 arquivo
  continua levando tudo junto
- Aparência protegida contra cor ilegível: ao escolher uma cor
  primária clara demais (onde o texto e os ícones brancos do menu e
  do cabeçalho sumiriam), o sistema avisa na hora e não deixa salvar,
  usando a razão de contraste do padrão WCAG
- Logo institucional (a mesma do site) no cabeçalho do aplicativo,
  ao lado do nome SIGBEF
- Ícones vetoriais (Font Awesome) na sidebar, no botão Sair e nos
  cards do painel inicial, alinhando o aplicativo à identidade visual
  do site. Sem emojis e sem dependência nova: os PNGs são gerados em
  tempo de desenvolvimento (tools/gerar_icones.js) e embutidos em
  base64; em runtime é só tk.PhotoImage, biblioteca padrão. Cores
  fixas à prova de paleta personalizada (branco na sidebar, cinza
  neutro nos cards, verde/vermelho apenas nos cards de convenção
  universal)

## [1.6.1] — 2026-07-18

### Avisos por e-mail (opt-in)
- Novo aviso: quando um livro reservado fica separado para o aluno, ele
  recebe e-mail avisando que pode retirar (prazo de retirada incluído)
- O botão "Enviar avisos agora" passa a cobrir os dois tipos de aviso
  (vencimento próximo e reserva disponível)

### Acervo
- Busca avançada: filtro por categoria (combo) na pesquisa de livros da
  bibliotecária e do aluno, além da busca por texto livre
- Importação CSV com número de tombo: a coluna `tombo` (aliases:
  `numero_tombo`, `nº de registro`, `registro`) preserva o número do
  livro de tombo em papel; um por exemplar, separados por `/` quando a
  quantidade for maior que 1. Como o empréstimo já aceita o tombo como
  identificador, a bibliotecária pode emprestar digitando o número que
  está escrito no livro físico. Tombos repetidos viram erro de linha

### Interface
- Tela de Configurações sem bordas duplicadas: os blocos internos de
  SMTP, API e predefinições de cor não desenham mais "card dentro de
  card" (novo estilo interno sem borda, aplicado também no assistente
  de primeira execução)
- Botões "Salvar aparência" e "Restaurar padrão" agora acompanham a
  rolagem da tela, em vez de flutuarem fora da área de conteúdo

### Qualidade
- Diálogos de seleção (exemplar e usuário) unificados numa base
  reutilizável, eliminando a duplicação apontada na auditoria
- Suíte com 223 testes automatizados

## [1.6.0] — 2026-07-10

### API REST somente leitura (opt-in)
- Outros sistemas da escola consultam acervo, disponibilidade e
  situação de empréstimos pela rede local, sem tocar no banco
- 100% biblioteca padrão (`http.server`), zero dependência nova
- Token de acesso obrigatório (gerado via `secrets`, comparação em
  tempo constante), com regeneração pela tela de Configurações
- Nasce desligada; ligada, sobe junto com o aplicativo ou roda sem
  interface com `python sigbef.py --api`
- 6 rotas GET (ping, estatísticas, livros, detalhes, situação do
  leitor, circulação); nenhuma rota de escrita; guia em `docs/API.md`

### Reservas com fila de espera
- Aluno/professor reserva um livro sem exemplar disponível (botão
  "Reservar" na pesquisa); fila por ordem de chegada
- Exemplar devolvido de livro com fila fica **separado** pro primeiro
  da fila por 2 dias (configurável), em vez de voltar pra prateleira
- Só o dono da vez consegue emprestar o exemplar separado; prazo
  vencido passa a vez pro próximo automaticamente
- "Meus empréstimos" mostra as reservas (posição na fila ou prazo de
  retirada) com cancelamento; balcão e kiosk avisam quando a devolução
  tem fila esperando

### Avisos de vencimento por e-mail (opt-in)
- Lembrete único por empréstimo para usuários com e-mail cadastrado,
  alguns dias antes do prazo (janela configurável)
- Configuração completa em Configurações → Integrações (servidor SMTP,
  porta, credenciais, remetente) com botão "Enviar avisos agora"
- Desligado por padrão: o sistema continua 100% offline pra quem não usar
- Envio tudo-ou-nada: falha de rede não marca aviso como enviado, a
  próxima tentativa reenvia

### Segurança e robustez
- Verificação de senha em tempo constante e proteção contra
  enumeração de matrículas por tempo de resposta
- Tentativas de login falhas registradas na auditoria (LOGIN_FALHA)
- Auditoria de ativar/desativar usuário registra quem executou
- SQLite em modo WAL: balcão e kiosk simultâneos sem travamentos

### Experiência de uso
- **Devolução com um clique**: duplo clique (ou botão) na linha do
  empréstimo aberto devolve o livro, com confirmação; sem digitar código
- Valores vazios nas tabelas ficam em branco e travessões foram
  removidos de toda a interface (títulos, mensagens e dados de exemplo)
- Suíte com 189 testes automatizados cobrindo as regras de negócio
- F5 recarrega a seção, Ctrl+F foca a busca, sidebar destaca a seção ativa
- Balcão: devolução em série sem janelinha a cada livro; foco volta
  sozinho pro próximo atendimento
- Kiosk avisa 15 segundos antes de encerrar a sessão por inatividade

## [1.5.1] — 2026-07-08

### Manutenção interna (sem mudança de comportamento)
- Limpeza de código guiada por auditoria de complexidade: remoção de seis
  funções nunca utilizadas em `servicos.py` (upsert/listagem de editoras,
  categorias e autores), unificação do parsing de datas em `formato.py` e
  das telas de empréstimo/devolução do autoatendimento num único
  construtor parametrizado, e correção de um import duplicado
- Alinhamento da versão interna do pacote (`__version__`) com a linha de
  release 1.5.x
- Saldo: 105 linhas a menos, mesmo comportamento (validado com testes de
  cadastro, detalhes de livro, empréstimo e devolução)

## [1.5.0] — 2026-07-08

### Distribuição multiplataforma
- **GitHub Actions** (`.github/workflows/build.yml`): cada tag `v*` gera
  automaticamente os pacotes para Windows (instalador + portátil),
  Linux (`.tar.gz`) e macOS (`.app` em `.zip`), anexados na release
- **`build.sh`**: build local em Linux/macOS, equivalente ao `build.bat`
- **`sigbef.spec`**: no macOS o resultado agora é um bundle `SIGBEF.app`
  clicável no Finder
- **Instalador Inno**: versão parametrizável via `/DMyAppVersion` (CI)
- **Site**: requisitos e FAQ atualizados (Linux e macOS suportados)

O código do aplicativo não mudou: ele sempre foi Python + Tkinter +
SQLite portáveis; o que faltava era o empacotamento por plataforma.

## [1.4.0] — 2026-07-02

### Acervo
- **Importação em massa via CSV**: cadastro de milhares de livros a partir
  de planilha, com modelo pronto, detecção automática de separador (`;`/`,`)
  e codificação (UTF-8/Windows-1252), e proteção contra ISBN duplicado.
  Inserção em transação única (~12 mil livros/s)
- **Etiquetas em massa**: impressão dos códigos de barras de todo o acervo
  (ou de uma busca) numa página só
- **Exclusão de livros** do acervo, preservando o histórico de empréstimos

### Usuários
- **Edição de usuários**: nome, contato, perfil e série/turma (útil na
  virada de ano letivo), com matrícula fixa
- **Exclusão de usuários** sem histórico, com bloqueio contra auto-exclusão
  e auto-rebaixamento de perfil
- **Impressão de cartão** de biblioteca com código de barras, no tamanho
  padrão de crachá (85,6 × 54 mm)

### Interface
- Tema refinado: tabelas com linhas zebradas, destaque de foco nos campos
  e efeitos de hover — derivados da paleta ativa, adaptando-se a qualquer
  personalização de cores

### Robustez
- Correção de condição de corrida em empréstimos/devoluções simultâneos
  (trava atômica no exemplar)
- Índices de banco adicionais: busca no acervo até ~260× mais rápida em
  acervos grandes
- Geração de código de barras à prova de colisão em cadastros em lote

### Site
- Contato direto por **WhatsApp** (botão flutuante, planos e rodapé)

## 1.3.0 — 2026-06-25

### Site oficial (React + Vite)

**Multi-página com React Router**
- Migração de landing page única para 5 páginas com HashRouter (compatível com GitHub Pages sem configuração de servidor)
- Rotas: `/` (home), `/#/funcionalidades`, `/#/download`, `/#/planos`, `/#/equipe`
- `ScrollToTop` automático em cada mudança de rota
- `NavLink` com destaque de rota ativa

**Hero aprimorado**
- Layout de 2 colunas no desktop (texto + mockup CSS)
- Mockup CSS puro do painel do SIGBEF: janela escura com stats e tabela de empréstimos simulada
- Nenhuma imagem externa

**Ícones Font Awesome**
- Substituição de todos os emojis por ícones SVG do Font Awesome 6 via `@fortawesome/react-fontawesome`
- Componentes atualizados: `Problema`, `Funcionalidades`, `Equipe`, `ODS`, `Home`
- Tree-shaking automático pelo Vite — apenas os ícones usados entram no bundle

**Novas páginas**
- `FuncionalidadesPage` — funcionalidades completas por perfil + tabela comparativa + CTA
- `DownloadPage` — requisitos de sistema, 4 passos detalhados, FAQ de instalação (6 perguntas)
- `PlanosPage` — pricing completo + FAQ de preços (5 perguntas) + contato
- `EquipePage` — equipe + linha do tempo do projeto + blockquote da missão

**Footer aprimorado**
- 4 colunas: marca, produto, projeto, CTA de download
- Links internos via `react-router-dom Link`

**Infra e repositório**
- `site/README.md` reescrito (era template padrão Vite)
- Badge do site GitHub Pages adicionado ao `README.md` principal
- Repositório Bitbucket configurado: `bitbucket.org/workspacemarcellomelo/sigbef-sistema-de-biblioteca`
- Push inicial para Bitbucket com 40 arquivos

## 1.2.0 — 2026-05-24

Pedido vindo da própria biblioteca do CEFE durante a apresentação do
sistema ao orientador do projeto: incluir série e turma na
identificação do aluno.

### Adicionado

- **Campo "Série / Turma" no cadastro de usuário.** Coluna nova
  `turma` na tabela `usuario` (TEXT, opcional). Aparece como um
  campo a mais no diálogo de cadastro logo abaixo de Telefone, com
  hint embaixo sugerindo o formato ("Ex.: 3º Ano Técnico em
  Informática"). É opcional pra todos os perfis, mas faz sentido
  principalmente pra Aluno.
- **Migração automática de banco existente.** A função
  `init_database()` agora chama `_migrar_schema()`, que detecta se
  a coluna `turma` está faltando e aplica `ALTER TABLE` em bancos
  antigos. Bancos novos já são criados com a coluna.
- **Listagem de usuários passa a aceitar busca por turma.** O termo
  de busca em `listar_usuarios()` agora compara com nome, matrícula,
  e-mail e turma.

### Alterado

- **Dados de demonstração** (seed) atualizados com turma plausível
  pros dois alunos: Lucas Pereira Santos = "3º Ano Técnico em
  Informática", Beatriz Almeida Rocha = "2º Ano Técnico em
  Administração". Staff (admin, bibliotecárias, professora) fica
  com turma vazia.
- Tela de cadastro de usuário aumentou de 520x520 para 520x600 pra
  acomodar o novo campo sem cortar conteúdo.

## 1.1.0 — 2026-05-22

Refino estrutural e visual para a submissão no Desafio Liga Jovem do
Sebrae.

### Adicionado

- **Personalização de cores em Configurações → Aparência**: o
  administrador pode escolher entre 5 paletas predefinidas (CEFE
  padrão, Verde Floresta, Roxo Universitário, Vermelho Acadêmico e
  Marrom Biblioteca) ou definir cada uma das 4 cores principais
  (primária, secundária, destaque e fundo) manualmente, com seletor
  de cor nativo do sistema e campo hex editável. Cada cor tem um
  *swatch* (quadrado de preview) que atualiza em tempo real. As
  alterações são persistidas no banco e aplicadas no próximo boot.
  Cores de sucesso/erro/aviso permanecem fixas (convenção universal
  de UI).
- Novas funções em `sigbef/ui_tema.py`: `PRESETS` (dicionário com 5
  paletas), `carregar_personalizacao()`, `aplicar_preset()`,
  `salvar_cores()`, `restaurar_padrao()`. A função
  `carregar_personalizacao()` é chamada automaticamente no início de
  `aplicar_tema()`, então qualquer entrada do app (login, painel,
  setup, autoatendimento) já reflete a paleta escolhida.
- **Scroll vertical em Configurações** — a tela ganhou rolagem
  automática quando o conteúdo (Configurações + Ferramentas +
  Aparência) ultrapassa a altura da janela. Rolagem pela roda do
  mouse só ativa quando o cursor está sobre a seção (não interfere
  em outras telas).
- **Dados de demonstração com nomes realistas** — o seed inicial
  (carregado em Configurações → Ferramentas → "Carregar dados de
  exemplo") foi reescrito com nomes plausíveis de uma escola real:
  admin "Marcello Melo", bibliotecárias "Laiane Souza" e "Jaqueline
  Dantas", professora "Macilene Lima", alunos "Lucas Pereira
  Santos" (matrícula 2024001) e "Beatriz Almeida Rocha" (2024002).
  Substitui os placeholders genéricos anteriores (Maria Bibliotecária,
  João Professor, Ana Aluna, Pedro Aluno) que prejudicavam a
  apresentação em demos ao vivo.

### Alterado

- **Reorganização da estrutura de pastas** para padrão profissional:
  - Toda a documentação (`MANUAL_DO_USUARIO.md`, `CHANGELOG.md`,
    `COMO_GERAR_EXECUTAVEL.md`, `PUBLICAR_NO_GITHUB.md`,
    `SIGBEF_Documento_Requisitos.docx`) consolidada em `docs/`.
  - `setup_github.bat` movido para `tools/` (com ajuste de `cd` para
    voltar à raiz).
  - `apresentacao/` agora tem subpastas: `pptx/` (artefatos prontos),
    `geradores/` (scripts) e `sebrae/` (material do Liga Jovem).
  - README atualizado refletindo a nova árvore.
- `.gitignore` ampliado: ignora `.claude/`, `skills-lock.json` e
  artefatos locais.

## [1.0.0] — 2026-05-05

Primeira versão estável do **SIGBEF — Sistema Integrado de Gestão da
Biblioteca do CEFE**. Pronto para uso em produção.

### Transição protótipo → produção

- **Removidas credenciais de demonstração da tela de login**
  (vulnerabilidade) — agora mostra apenas o nome da instituição.
- **Assistente de primeira execução** (`sigbef/ui_setup.py`): quando o
  banco está vazio, guia o admin na criação da conta inicial e nome da
  instituição.
- **Auto-seed removido** — em produção o banco começa vazio. O admin
  carrega dados de demo opcionalmente em Configurações → Ferramentas.
- **Diálogo "Sobre"** com versão, licença e autor (Configurações).
- **Backup do banco** com um clique (Configurações → Ferramentas).
- **Argumento `--demo`** para popular dados de exemplo no boot
  (útil em testes/CI).
- **Manual do usuário** (`MANUAL_DO_USUARIO.md`) com fluxos passo a
  passo separados por perfil de usuário.

### Adicionado

#### Núcleo do sistema
- Banco SQLite com 10 tabelas (`livro`, `exemplar`, `usuario`, `emprestimo`,
  `categoria`, `editora`, `autor`, `livro_autor`, `configuracao`, `auditoria`)
- Camada de serviços com regras de negócio isoladas da UI
- Hash de senhas com PBKDF2-HMAC-SHA256 (200 mil iterações + sal aleatório)
- Auditoria automática de operações relevantes
- Configurações dinâmicas (prazos, limites, multas) editáveis pelo Admin
- Banco persistido em `%APPDATA%\SIGBEF\` quando empacotado
- Variável de ambiente `SIGBEF_DB_PATH` para sobrescrever o caminho

#### Cadastros
- CRUD de livros com múltiplos autores, ISBN, editora, categoria, sinopse
- Geração automática de exemplares com código de barras único
  (`EXyymmddHHMMSS####`)
- CRUD de usuários com 4 perfis (Aluno, Professor, Bibliotecário, Admin)
- Geração automática de cartão (código de barras) para cada usuário

#### Empréstimos
- Empréstimo de balcão com seletor de exemplares disponíveis
- Empréstimo direto na pesquisa para alunos/professores
- Aceita **código de barras OU número de tombo** (busca tolerante)
- Aceita **matrícula OU código de barras do cartão**
- Devolução com cálculo automático de multa por atraso
- Renovação respeitando reservas e perfil
- Quitação manual de multa
- Bloqueio automático por inadimplência ou atraso

#### Autoatendimento (kiosk)
- Login por matrícula+senha ou código de barras do cartão
- Empréstimo e devolução autônomos
- Comprovante na tela com data prevista
- Encerramento automático de sessão após 90 segundos de inatividade
- Argumento de linha de comando `--autoatendimento` para abrir direto

#### Relatórios
- Acervo completo (CSV)
- Empréstimos em aberto (CSV)
- Usuários cadastrados (CSV)
- Top livros mais emprestados (CSV)
- Datas em formato brasileiro (dd/mm/yyyy) e valores em R$

#### Interface
- Tema visual institucional (azul CEFE) com Tkinter/ttk
- Sidebar com navegação contextual por perfil
- Dashboard com 6 indicadores em tempo real e top 10 mais emprestados
- Diálogos de seleção de exemplar e usuário com busca embutida
- Destaque visual para empréstimos atrasados (vermelho) e devolvidos (cinza)
- Mensagens inline de sucesso/erro (não só popups)

#### Empacotamento e distribuição
- `build.bat` — gera executável Windows com PyInstaller automaticamente
- `sigbef.spec` — configuração otimizada (excludes de libs não usadas)
- `tools/gerar_icone.py` — gera `.ico` a partir de SVG
- `tools/sigbef_installer.iss` — script Inno Setup para instalador
  profissional `SIGBEF_Setup.exe` com atalhos no menu Iniciar e
  desinstalador
- `setup_github.bat` — automatiza publicação no GitHub

#### Documentação
- README profissional com badges, mockups SVG, diagramas Mermaid
  (arquitetura e ER), modelo de dados, regras de negócio, roadmap
- 5 mockups SVG das principais telas em `docs/screenshots/`
- Logo institucional em `assets/sigbef.svg`
- Documento de requisitos (.docx) com 12 seções técnicas
- Guias separados: `COMO_GERAR_EXECUTAVEL.md` e `PUBLICAR_NO_GITHUB.md`
- Licença MIT com `Copyright (c) 2026 Marcello`
- Cabeçalhos SPDX nos pontos de entrada do código

### Regras de negócio padrão

| Regra | Valor |
|---|---|
| Prazo aluno | 7 dias |
| Prazo professor | 14 dias |
| Limite aluno | 3 empréstimos simultâneos |
| Limite professor | 5 empréstimos simultâneos |
| Multa por dia | R$ 1,50 |
| Teto de multa | R$ 60,00 |

### Dados de demonstração (seed inicial)

- **5 usuários:** admin, bibliotecaria, prof, aluna, pedro
- **10 livros** com múltiplos exemplares em 6 categorias
  (Literatura Brasileira, Computação, História, etc.)

## Versões futuras (roadmap)

Itens previstos para versões posteriores — ver
[README#roadmap](README.md#roadmap):

- API REST para integração com outros sistemas
- Aplicativo móvel (Android/iOS) para consulta do acervo
- Camada de engajamento de leitura para alunos, com estatísticas
  pessoais, recomendações por categoria e possível gamificação leve
  (medalhas, metas mensais). Pensado pra rodar dentro do app móvel
  como evolução natural do consumo do acervo, não como obrigação
- Suporte a múltiplos idiomas (i18n), priorizando português,
  inglês e espanhol na primeira leva. Outros idiomas (francês,
  russo, etc.) entram conforme demanda real
- Importação de acervo a partir de Excel/CSV
- Notificações por e-mail antes do vencimento
- Reservas online com fila de espera
- Suporte a múltiplas unidades / bibliotecas
- Migração para PostgreSQL em ambientes em rede

[1.6.2]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.6.2
[1.6.1]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.6.1
[1.6.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.6.0
[1.5.1]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.5.1
[1.5.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.5.0
[1.4.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/V.1.4.0
[1.0.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/V1.0.0
