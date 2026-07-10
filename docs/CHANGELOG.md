# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

---

## [Não lançado] — v1.6.0 em desenvolvimento (branch melhorias-v1.6)

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

### Segurança e robustez
- Verificação de senha em tempo constante e proteção contra
  enumeração de matrículas por tempo de resposta
- Tentativas de login falhas registradas na auditoria (LOGIN_FALHA)
- Auditoria de ativar/desativar usuário registra quem executou
- SQLite em modo WAL: balcão e kiosk simultâneos sem travamentos

### Experiência de uso
- Suíte com 164 testes automatizados cobrindo as regras de negócio
- F5 recarrega a seção, Ctrl+F foca a busca, sidebar destaca a seção ativa
- Balcão: devolução em série sem janelinha a cada livro; foco volta
  sozinho pro próximo atendimento
- Kiosk avisa 15 segundos antes de encerrar a sessão por inatividade

---

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

---

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

---

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

---

## [1.3.0] — 2026-06-25

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

---

## [1.2.0] — 2026-05-24

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

---

## [1.1.0] — 2026-05-22

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
  Oliveira", professora "Macilene Lima", alunos "Lucas Pereira
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

---

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

---

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

[1.5.1]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.5.1
[1.5.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.5.0
[1.4.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.4.0
[1.3.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.3.0
[1.2.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.2.0
[1.1.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.1.0
[1.0.0]: https://github.com/marcelin1555/SIGBEF/releases/tag/v1.0.0
