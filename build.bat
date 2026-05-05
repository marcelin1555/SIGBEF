@echo off
REM =====================================================================
REM  SIGBEF - Gerador de executavel para Windows
REM
REM  Este script:
REM    1. Garante que o PyInstaller esta instalado
REM    2. Gera o executavel SIGBEF.exe na pasta dist\SIGBEF\
REM    3. Cria um atalho com instrucoes para a biblioteca
REM
REM  Pre-requisito: Python 3.10+ instalado e no PATH
REM =====================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ======================================================
echo  SIGBEF - Build do Executavel
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
    python -m pip install --upgrade pip
    python -m pip install pyinstaller
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

REM 4. Limpar builds anteriores
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM 5. Executar PyInstaller
echo.
echo Compilando executavel... isso pode levar alguns minutos.
python -m PyInstaller sigbef.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERRO] Build falhou. Verifique as mensagens acima.
    pause
    exit /b 1
)

REM 6. Copiar README e dados iniciais para a pasta de distribuicao
copy README.md "dist\SIGBEF\" >nul
copy LICENSE "dist\SIGBEF\" >nul
echo.> "dist\SIGBEF\COMO_USAR.txt"
echo SIGBEF - Sistema Integrado de Gestao da Biblioteca do CEFE>> "dist\SIGBEF\COMO_USAR.txt"
echo ============================================================>> "dist\SIGBEF\COMO_USAR.txt"
echo.>> "dist\SIGBEF\COMO_USAR.txt"
echo Para iniciar o sistema, de duplo-clique em SIGBEF.exe>> "dist\SIGBEF\COMO_USAR.txt"
echo.>> "dist\SIGBEF\COMO_USAR.txt"
echo Para iniciar direto no autoatendimento:>> "dist\SIGBEF\COMO_USAR.txt"
echo    SIGBEF.exe --autoatendimento>> "dist\SIGBEF\COMO_USAR.txt"
echo.>> "dist\SIGBEF\COMO_USAR.txt"
echo Credenciais de demonstracao iniciais:>> "dist\SIGBEF\COMO_USAR.txt"
echo    admin / admin123       (Administrador)>> "dist\SIGBEF\COMO_USAR.txt"
echo    bibliotecaria / biblio123  (Bibliotecario)>> "dist\SIGBEF\COMO_USAR.txt"
echo    aluna / aluna123      (Aluno)>> "dist\SIGBEF\COMO_USAR.txt"
echo.>> "dist\SIGBEF\COMO_USAR.txt"
echo O banco de dados sera criado em:>> "dist\SIGBEF\COMO_USAR.txt"
echo    %%APPDATA%%\SIGBEF\sigbef.db>> "dist\SIGBEF\COMO_USAR.txt"

echo.
echo ======================================================
echo  BUILD CONCLUIDO COM SUCESSO!
echo ======================================================
echo.
echo Executavel gerado em:
echo    %CD%\dist\SIGBEF\SIGBEF.exe
echo.
echo Para distribuir, copie a pasta inteira:
echo    %CD%\dist\SIGBEF\
echo.
echo Para criar um instalador profissional, use Inno Setup
echo (https://jrsoftware.org/isinfo.php) com o arquivo:
echo    tools\sigbef_installer.iss
echo.
pause
