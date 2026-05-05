# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adere a [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [1.0.0] — 2026-05-05

Primeira versão estável do **SIGBEF — Sistema Integrado de Gestão da
Biblioteca do CEFE**.

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
- Importação de acervo a partir de Excel/CSV
- Notificações por e-mail antes do vencimento
- Reservas online com fila de espera
- Suporte a múltiplas unidades / bibliotecas
- Migração para PostgreSQL em ambientes em rede

[1.0.0]: https://github.com/SEU-USUARIO/sigbef/releases/tag/v1.0.0
