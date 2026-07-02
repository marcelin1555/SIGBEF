@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "REMOTE=origin"
set "BRANCH=main"

echo ============================================================
echo  SIGBEF - Commit e envio para o GitHub (%REMOTE%/%BRANCH%)
echo ============================================================
echo.

REM 0. Confirma que o remote de destino existe
git remote get-url %REMOTE% >nul 2>&1
if errorlevel 1 (
    echo [ERRO] O remote "%REMOTE%" nao esta configurado neste repositorio.
    echo Configure com: git remote add %REMOTE% https://github.com/marcelin1555/SIGBEF.git
    pause
    exit /b 1
)
echo Destino:
git remote get-url %REMOTE%
echo.

REM 1. Mostra o que mudou (respeita o .gitignore)
echo Mudancas pendentes:
echo ------------------------------------------------------------
git status --short
echo ------------------------------------------------------------
echo.

REM Se nao houver nada para commitar, encerra
git status --porcelain > "%TEMP%\sigbef_gitstatus.txt"
for %%A in ("%TEMP%\sigbef_gitstatus.txt") do set _SIZE=%%~zA
del "%TEMP%\sigbef_gitstatus.txt" 2>nul
if "%_SIZE%"=="0" (
    echo Nada para commitar. Tudo ja esta versionado.
    echo.
    pause
    exit /b 0
)

REM 2. Pede a mensagem do commit
set "MSG="
set /p "MSG=Escreva a mensagem do commit: "
if "%MSG%"=="" (
    echo.
    echo Mensagem vazia. Operacao cancelada.
    pause
    exit /b 1
)

REM 3. Adiciona e commita
echo.
git add -A
git commit -m "%MSG%"
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao criar o commit.
    pause
    exit /b 1
)

REM 4. Envia explicitamente para origin/main (configura upstream na 1a vez)
echo.
echo Enviando para %REMOTE%/%BRANCH% ...
git push -u %REMOTE% %BRANCH%
if errorlevel 1 (
    echo.
    echo [ERRO] Falha no push. Verifique:
    echo   - conexao com a internet
    echo   - login do GitHub ^(o Git Credential Manager deve abrir uma janela^)
    echo   - se o repositorio remoto nao tem commits que voce ainda nao baixou
    echo     ^(nesse caso rode: git pull %REMOTE% %BRANCH% --rebase^)
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  PRONTO! Commit enviado para o GitHub com sucesso.
echo ============================================================
echo.
pause
