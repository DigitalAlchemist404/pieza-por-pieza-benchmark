#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
if [[ ! -f config.local.json ]]; then
  echo 'ERROR: falta config.local.json. Primero configura rutas con scripts/configure.py.' >&2
  exit 2
fi
if [[ ! -x .venv/bin/python ]]; then
  echo 'Preparando entorno virtual .venv ...'
  python3 -m venv .venv || { echo 'ERROR: no se pudo crear .venv. En Ubuntu instalá python3-venv.' >&2; exit 2; }
fi
PY="$ROOT/.venv/bin/python"
if ! "$PY" -c 'import datasets, pyarrow' >/dev/null 2>&1; then
  echo 'Instalando dependencias de datasets en .venv (requiere Internet)...'
  "$PY" -m pip install 'datasets>=3,<5' || { echo 'ERROR: instalación falló. Revisá conexión y pip.' >&2; exit 2; }
fi
"$PY" -c 'import datasets; print("datasets:",datasets.__version__)'
LIMIT="${LIMIT:-100}"; SEED="${SEED:-42}"; PORT="${PORT:-18081}"; MAX_TOKENS="${MAX_TOKENS:-512}"
for n in "$LIMIT" "$SEED" "$PORT" "$MAX_TOKENS"; do [[ "$n" =~ ^[0-9]+$ ]] || { echo 'ERROR: LIMIT/SEED/PORT/MAX_TOKENS deben ser números' >&2; exit 2; }; done
if (( LIMIT < 1 || MAX_TOKENS < 1 )); then echo 'ERROR: LIMIT y MAX_TOKENS deben ser positivos' >&2; exit 2; fi
OUT="results/capacidades_no_thinking_n${LIMIT}_seed${SEED}"
mkdir -p "$OUT"
"$PY" scripts/evaluate_no_thinking.py --limit "$LIMIT" --seed "$SEED" --port "$PORT" --max-tokens "$MAX_TOKENS" --out "$OUT"
"$PY" - "$OUT" <<'PY'
import csv,sys,pathlib,zipfile
p=pathlib.Path(sys.argv[1]);s=p/'summary.csv'
print('\n=== RESUMEN ===')
for r in csv.DictReader(s.open()):print(r)
z=pathlib.Path('capacidades_no_thinking_para_revision.zip')
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:
 for n in ('answers.jsonl','summary.csv','dataset_manifest.json','run_config.json'):
  f.write(p/n,n)
print('\nCompartime:',z.resolve())
PY
