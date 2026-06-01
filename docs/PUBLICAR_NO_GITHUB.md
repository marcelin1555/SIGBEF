# Publicando o SIGBEF no GitHub

Há **dois caminhos** para publicar o projeto. Escolha o que for mais
confortável para você.

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
cd "C:\Users\uemas\OneDrive\Documentos\Claude\Projects\SIGBIB"

git init -b main
git config user.name  "Marcello"
git config user.email "juninho876677@gmail.com"

git add .
git commit -m "Initial commit: SIGBEF v1.0"

# Crie um repositório vazio em https://github.com/new e troque
# <USUARIO> e <REPO> abaixo:
git remote add origin https://github.com/<USUARIO>/<REPO>.git
git push -u origin main
```

---

## O que vai para o GitHub

O `.gitignore` já garante que **NÃO** sejam enviados:

- `data/` (banco SQLite local)
- `__pycache__/` (bytecode do Python)
- arquivos temporários do OneDrive
- `db.py` (arquivo legado)

Vão para o repositório:

- Todo o código-fonte em `sigbef/`
- `sigbef.py`, `requirements.txt`, `README.md`, `LICENSE`
- `docs/` (documento de requisitos, manual do usuário, changelog, guias)
- `apresentacao/` (slides e material institucional)
- `tools/setup_github.bat` e demais scripts auxiliares

---

## Atualizando o repositório depois

Após qualquer mudança no código:

```bash
git add .
git commit -m "Descrição da mudança"
git push
```
