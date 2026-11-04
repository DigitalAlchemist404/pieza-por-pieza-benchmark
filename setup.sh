#!/usr/bin/env bash
# Preparación portátil Linux/macOS; no instala controladores ni descarga modelos.
set -euo pipefail
cd "$(dirname "$0")"
case "$(uname -s)" in
  Linux) OS=Linux ;;
  Darwin) OS=macOS ;;
  *) echo "Sistema no soportado por este instalador: $(uname -s)" >&2; exit 1 ;;
esac
printf '\n🦁 Pieza por Pieza | %s | %s\n' "$OS" "$(uname -m)"
command -v python3 >/dev/null 2>&1 || { echo 'Falta Python 3. Instalalo y volvé a ejecutar bash setup.sh.' >&2; exit 1; }
python3 - <<'PY'
import sys
print('Python:',sys.version.split()[0])
if sys.version_info < (3,10):
    raise SystemExit('Se requiere Python 3.10 o superior.')
PY
if ! python3 -m venv --help >/dev/null 2>&1; then
  echo 'Tu Python no incluye venv. En Debian/Ubuntu instalá python3-venv; en macOS instalá Python 3 desde python.org o Homebrew.' >&2
  exit 1
fi
if [ ! -f .venv/bin/python ]; then
  python3 -m venv .venv
fi
printf '\nInstalando dependencias de evaluación en .venv...\n'
.venv/bin/python -m pip install -r requirements-eval.txt
printf '\n✅ Entorno preparado. No se descargaron modelos GGUF.\n'
printf 'Para el siguiente paso, consultá README.md (Configurar modelos y llama.cpp).\n'
printf 'Siguiente paso: ejecutá python3 scripts/configure.py para configurar tus modelos y llama.cpp.\n'
