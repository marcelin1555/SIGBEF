# Publicando o SIGBEF no GitHub

O repositório oficial já existe. Para manutenção, use a seção
[Atualizando o repositório depois](#atualizando-o-repositório-depois).
Os caminhos de criação abaixo são apenas para um repositório novo;
não reinicialize nem reconfigure a origem da cópia existente.

---

## Caminho 1 — Automático (recomendado)

1. Verifique se o **Git** está instalado:
   <https://git-scm.com/download/win>
   Reinicie o computador depois de instalar.
2. Vá em <https://github.com/new> e crie um repositório novo. Sugestão:

   - **Repository name:** `sigbef`
   - **Description:** *Sistema Integrado de Gestão da Biblioteca do CEFE*
   - **Public** ou **Private** (à sua escolha)
   - **NÃO** marque "Initialize this repository with a README" (o nosso
     já existe)

3. Dê **duplo-clique** em `tools\setup_github.bat`. O script muda
   automaticamente para a raiz do projeto antes de executar e vai:
   - Inicializar o git
   - Fazer o primeiro commit
   - Pedir seu usuário do GitHub
   - Configurar a origem e enviar o código

4. Quando o GitHub pedir senha, **use um Personal Access Token (PAT)**
   em vez da senha da conta:
   <https://github.com/settings/tokens>
   (Selecione o escopo `repo` ao gerar.)

---

## Caminho 2 — Manual (terminal)

Abra o **PowerShell** ou **Git Bash** na pasta do projeto e rode:

```bash
cd "F:\programas-projetos\SIGBIB"

git init -b main
git config user.name  "Marcello"
git config user.email "juninho876677@gmail.com"

git add .
git commit -m "Initial commit: SIGBEF v1.0"

# O repositório oficial já existe:
git remote add origin https://github.com/marcelin1555/SIGBEF.git
git push -u origin main
```

---

## O que vai para o GitHub

O `.gitignore` exclui estes arquivos novos por padrão. Ele não remove
arquivos já rastreados nem substitui a revisão de `git diff --cached`:

- `data/` (banco SQLite local)
- `__pycache__/` (bytecode do Python)
- arquivos temporários do OneDrive
- `db.py` (arquivo legado)
- `apresentacao/` e `HANDOFF_CLAUDE_CODE.md` (material privado)

Vão para o repositório:

- Todo o código-fonte em `sigbef/`
- `sigbef.py`, `requirements.txt`, `README.md`, `LICENSE`
- `docs/` (documento de requisitos, manual do usuário, changelog, guias)
- `tools/setup_github.bat` e demais scripts auxiliares

---

## Atualizando o repositório depois

Após qualquer mudança no código:

```bash
git status --short
git diff
git add caminho/do/arquivo
git diff --cached
git commit -m "docs: descrição da mudança"
git push origin main
```

Não inclua bancos, dados de alunos, chaves de assinatura ou senhas.
Commits sem trailer `Co-Authored-By`. Publicar o site é um passo separado
do envio do código; veja o [guia do site](../site/README.md).
