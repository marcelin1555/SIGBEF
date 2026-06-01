@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================================
echo  SIGBEF - Commit e envio para o GitHub
echo ============================================================
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

REM 3. Adiciona, commita e envia
echo.
git add -A
git commit -m "%MSG%"
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao criar o commit.
    pause
    exit /b 1
)

echo.
echo Enviando para o GitHub (git push)...
git push
if errorlevel 1 (
    echo.
    echo [ERRO] Falha no push. Verifique sua internet e o login do GitHub.
    echo Se pedir login, o Git Credential Manager deve abrir uma janela.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  PRONTO! Commit enviado para o GitHub com sucesso.
echo ============================================================
echo.
pause
