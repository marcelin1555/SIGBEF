#!/usr/bin/env bash
# =====================================================================
#  SIGBEF - Gerador de executável para Linux e macOS
#
#  Equivalente ao build.bat do Windows. Resultado em dist/:
#    - Linux:  dist/SIGBEF/          (rode ./SIGBEF)
#    - macOS:  dist/SIGBEF.app       (clique duplo no Finder)
#
#  Uso:  ./build.sh
# =====================================================================
set -euo pipefail
cd "$(dirname "$0")"

echo "======================================================"
echo " SIGBEF - Build do Executável (Linux/macOS)"
echo "======================================================"
echo

# 1. Verificar Python 3.10+
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERRO] python3 não encontrado no PATH."
    echo "Instale o Python 3.10+ pelo gerenciador de pacotes da sua distro."
    exit 1
fi
python3 -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ necessário"; print("Python", sys.version.split()[0])'

# 2. Verificar Tkinter (em Linux costuma ser pacote separado)
if ! python3 -c 'import tkinter' 2>/dev/null; then
    echo "[ERRO] Tkinter não encontrado."
    echo "  Debian/Ubuntu:  sudo apt install python3-tk"
    echo "  Fedora:         sudo dnf install python3-tkinter"
    echo "  Arch:           sudo pacman -S tk"
    exit 1
fi

# 3. Verificar / instalar PyInstaller
if ! python3 -c 'import PyInstaller' 2>/dev/null; then
    echo "Instalando PyInstaller..."
    python3 -m pip install --user pyinstaller --quiet \
        || python3 -m pip install --user pyinstaller --quiet --break-system-packages
fi

# 4. Compilar
echo
echo "Compilando executável... isso pode levar alguns minutos."
python3 -m PyInstaller sigbef.spec --clean --noconfirm

# 5. Documentação junto da distribuição
cp README.md LICENSE dist/SIGBEF/ 2>/dev/null || true

echo
echo "======================================================"
if [[ "$(uname)" == "Darwin" ]]; then
    echo " Pronto: dist/SIGBEF.app"
else
    echo " Pronto: dist/SIGBEF/  (execute com ./dist/SIGBEF/SIGBEF)"
fi
echo "======================================================"
