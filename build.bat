@echo off
REM =====================================================================
REM  SIGBEF - Gerador de executavel para Windows
REM
REM  Usa %LOCALAPPDATA%\SIGBEF-build para o build intermediario
REM  (sempre gravavel) e copia o resultado final para a pasta dist\
REM  do projeto so no final.
REM =====================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ======================================================
echo  SIGBEF - Build do Executavel (v2)
echo ======================================================
echo.

REM 1. Verificar Python
where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo Instale o Python 3.10 ou superior em https://www.python.org/downloads/
    echo Marque "Add python.exe to PATH" durante a instalacao.
    pause
    exit /b 1
)

python -c "import sys; print('Python', sys.version.split()[0])"

REM 2. Verificar / instalar PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Instalando PyInstaller...
    python -m pip install --upgrade pip --quiet
    python -m pip install pyinstaller --quiet
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar PyInstaller.
        pause
        exit /b 1
    )
)

REM 3. Garantir que existe icone ICO (opcional)
if not exist "assets\sigbef.ico" (
    echo Gerando icone ICO...
    python -c "import PIL" 2>nul
    if errorlevel 1 (
        echo Instalando Pillow para gerar o icone...
        python -m pip install pillow --quiet
    )
    python tools\gerar_icone.py
)
if not exist "assets\sigbef.ico" (
    echo Aviso: sigbef.ico nao gerado; build continuara sem icone customizado.
)

REM 4. Pastas de trabalho em local sempre gravavel
set BUILD_DIR=%LOCALAPPDATA%\SIGBEF-build\build
set DIST_DIR=%LOCALAPPDATA%\SIGBEF-build\dist
set WORK_PATH=%LOCALAPPDATA%\SIGBEF-build

echo.
echo Workspace temporario: %WORK_PATH%

REM Limpar workspace temporario
if exist "%WORK_PATH%" (
    echo Limpando build anterior...
    rmdir /s /q "%WORK_PATH%" 2>nul
)
mkdir "%WORK_PATH%" 2>nul

REM 5. Executar PyInstaller redirecionando saidas
echo.
echo Compilando executavel... isso pode levar alguns minutos.
echo.
python -m PyInstaller sigbef.spec ^
    --clean ^
    --noconfirm ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%"
if errorlevel 1 (
    echo.
    echo [ERRO] Build falhou. Verifique as mensagens acima.
    pause
    exit /b 1
)

REM 6. Copiar resultado para a pasta do projeto
echo.
echo Copiando executavel para dist\SIGBEF\ no projeto...

REM Tentar criar dist/ no projeto (pode falhar por permissao no F:)
mkdir "%~dp0dist" 2>nul
if not exist "%~dp0dist" (
    echo.
    echo [AVISO] Nao foi possivel criar a pasta dist\ aqui.
    echo O executavel ficou em:
    echo    %DIST_DIR%\SIGBEF\
    echo.
    echo Para copiar para outro lugar, use o Explorer ou rode:
    echo    xcopy /E /I "%DIST_DIR%\SIGBEF" "C:\caminho\desejado\SIGBEF"
    echo.
    explorer "%DIST_DIR%"
    pause
    exit /b 0
)

xcopy /E /I /Y "%DIST_DIR%\SIGBEF" "%~dp0dist\SIGBEF" >nul
if errorlevel 1 (
    echo [AVISO] Falha ao copiar para o projeto. Use o caminho direto:
    echo    %DIST_DIR%\SIGBEF\
    explorer "%DIST_DIR%"
    pause
    exit /b 0
)

REM 7. Documentacao na pasta de distribuicao
copy README.md "%~dp0dist\SIGBEF\" >nul 2>&1
copy LICENSE "%~dp0dist\SIGBEF\" >nul 2>&1
(
echo SIGBEF - Sistema Integrado de Gestao da Biblioteca do CEFE
echo ============================================================
echo.
echo Para iniciar o sistema, de duplo-clique em SIGBEF.exe
echo.
echo Para iniciar direto no autoatendimento:
echo    SIGBEF.exe --autoatendimento
echo.
echo Na primeira execucao o sistema abre o assistente de configuracao
echo para voce criar a conta de administrador.
echo.
echo Credenciais dos usuarios de demonstracao (apos carregar os dados
echo de demo em Configuracoes ou rodar com --demo):
echo    laiane / laiane123        (Bibliotecario)
echo    jaqueline / jaqueline123  (Bibliotecario)
echo    macilene / macilene123    (Professor)
echo    2024001 / lucas123        (Aluno)
echo    2024002 / beatriz123      (Aluno)
echo.
echo O banco de dados sera criado em:
echo    %%APPDATA%%\SIGBEF\sigbef.db
) > "%~dp0dist\SIGBEF\COMO_USAR.txt"

echo.
echo ======================================================
echo  BUILD CONCLUIDO COM SUCESSO!
echo ======================================================
echo.
echo Executavel gerado em:
echo    %~dp0dist\SIGBEF\SIGBEF.exe
echo.
echo Para distribuir, copie a pasta inteira:
echo    %~dp0dist\SIGBEF\
echo.

REM Limpar workspace temporario (build/ pesado, nao precisa mais)
rmdir /s /q "%BUILD_DIR%" 2>nul

REM Abrir a pasta resultado
start "" "%~dp0dist\SIGBEF"
pause
