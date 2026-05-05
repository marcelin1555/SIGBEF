@echo off
REM =====================================================================
REM  SIGBEF v1.0.0 - Publicar no GitHub
REM
REM  Este script:
REM    1. Inicializa o repositorio git (limpando estado anterior)
REM    2. Faz o commit inicial estruturado
REM    3. Cria a tag v1.0.0
REM    4. Pergunta seu usuario do GitHub
REM    5. Configura a origem e faz push (com a tag)
REM
REM  Pre-requisitos:
REM    - Git instalado: https://git-scm.com/download/win
REM    - Conta no GitHub e Personal Access Token (PAT):
REM      https://github.com/settings/tokens (escopo "repo")
REM =====================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ======================================================
echo  SIGBEF v1.0.0 - Publicacao no GitHub
echo ======================================================
echo.

REM 1. Verificar Git
where git >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Git nao encontrado no PATH.
    echo Instale em https://git-scm.com/download/win e rode novamente.
    pause
    exit /b 1
)

REM 2. Limpar repositorio antigo
if exist ".git" (
    echo Removendo .git anterior para comecar limpo...
    rmdir /s /q .git
)

REM 3. Inicializar
echo Inicializando repositorio (branch: main)...
git init -b main

REM 4. Configurar identidade
echo.
set /p GIT_NAME="Seu nome completo (ex: Marcello): "
if "%GIT_NAME%"=="" set GIT_NAME=Marcello
set /p GIT_EMAIL="Seu email do GitHub: "
if "%GIT_EMAIL%"=="" set GIT_EMAIL=juninho876677@gmail.com

git config user.name "%GIT_NAME%"
git config user.email "%GIT_EMAIL%"
git config core.autocrlf true

REM 5. Stage + commit
echo.
echo Adicionando arquivos...
git add .

echo Fazendo commit inicial...
git commit -m "feat: SIGBEF v1.0.0 - lancamento inicial" -m "Sistema Integrado de Gestao da Biblioteca do CEFE - prototipo desktop totalmente funcional. Inclui painel administrativo, autoatendimento (kiosk), geracao de codigo de barras, controle de emprestimo/devolucao com calculo de multa, e empacotamento Windows. Stack: Python 3.10+ / Tkinter / SQLite. Licenca: MIT."

REM 6. Tag v1.0.0
git tag -a v1.0.0 -m "v1.0.0 - primeira versao estavel"
echo.
echo ======================================================
echo  Repositorio local pronto com tag v1.0.0
echo ======================================================
git log --oneline -1
git tag -l
echo.

REM 7. Configurar remote e push
echo Agora vamos publicar no GitHub.
echo.
echo PASSO IMPORTANTE: antes de continuar, va ate
echo   https://github.com/new
echo e crie um repositorio chamado, por exemplo: sigbef
echo NAO marque "Initialize this repository with a README"
echo.
pause

set /p GH_USER="Seu usuario do GitHub: "
set /p GH_REPO="Nome do repositorio criado (ex: sigbef): "
if "%GH_REPO%"=="" set GH_REPO=sigbef

set REMOTE_URL=https://github.com/%GH_USER%/%GH_REPO%.git
echo.
echo Adicionando origem: %REMOTE_URL%
git remote add origin %REMOTE_URL%

echo.
echo Enviando codigo (sera pedido o seu Personal Access Token)...
git push -u origin main
if errorlevel 1 (
    echo [ERRO] Falha no push do main. Verifique:
    echo  - Se voce criou o repositorio em github.com/%GH_USER%/%GH_REPO%
    echo  - Se usou um PAT em vez da senha (https://github.com/settings/tokens)
    echo  - Se nome e usuario estao corretos
    pause
    exit /b 1
)

echo.
echo Enviando tag v1.0.0...
git push origin v1.0.0
if errorlevel 1 (
    echo [AVISO] Falha ao enviar a tag. Voce pode tentar manualmente:
    echo   git push origin v1.0.0
    pause
    exit /b 1
)

echo.
echo ======================================================
echo  PUBLICADO COM SUCESSO!
echo ======================================================
echo.
echo Repositorio: https://github.com/%GH_USER%/%GH_REPO%
echo Release:     https://github.com/%GH_USER%/%GH_REPO%/releases/tag/v1.0.0
echo.
echo PROXIMOS PASSOS RECOMENDADOS:
echo.
echo 1) Editar a Release no GitHub (acesse o link acima) e colar
echo    o conteudo do arquivo CHANGELOG.md como descricao.
echo.
echo 2) Para anexar o executavel SIGBEF.exe na release:
echo    - Rode build.bat para gerar dist\SIGBEF\
echo    - Compacte a pasta dist\SIGBEF\ em SIGBEF_v1.0.0.zip
echo    - Na pagina da release, clique em "Edit" e faca upload do .zip
echo.
echo 3) Para futuras atualizacoes:
echo    git add .
echo    git commit -m "feat: descricao da mudanca"
echo    git push
echo.
pause
