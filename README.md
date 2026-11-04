# Pieza por Pieza — Benchmark Qwen3.5 (GX10)

Kit **local**, sin dependencias externas de Python. No descarga, mueve ni modifica modelos. Descubre cuatro variantes desde los manifiestos de Unsloth Studio y su `hub_cache` real (incluyendo `.../hub/hub`).

## Uso en GX10 (Linux AArch64)

Desde la carpeta descomprimida:

```bash
python3 scripts/run.py
python3 scripts/run.py --verify-sha
python3 scripts/run.py --run --reps 3
```

Primero ejecutá solo el diagnóstico. `--verify-sha` lee ~66 GB y puede tardar; verifica los SHA-256 de los manifiestos. `--run` inicia 8 escenarios (4 modelos × prefill 512 / decode 128), con 3 repeticiones cada uno. Cada escenario carga el modelo, por lo que puede llevar bastante tiempo. No hay necesidad de ejecutar comandos de descarga ni de recompilar llama.cpp.

Los archivos se guardan en `results/`: `inventory.json`, `runs.json`, `runs.csv`, y salidas JSONL y logs por escenario. Los JSONL son la salida original de `llama-bench` y contienen los datos de velocidad; `runs.csv` es un índice, **no** un resumen de tokens/s. No afirmar que se midió calidad, exactitud o KL: estas métricas requieren un experimento separado.

## Parámetros

- `--bench /ruta/al/llama-bench`: reemplaza binario por defecto `~/Documents/ai/llamacpp/llama.cpp/build/bin/llama-bench` (resuelto desde HOME).
- `--out carpeta`: ubicación de resultados (por defecto `results/`).
- `--reps N`: número de repeticiones (por defecto 3).
- `--verify-sha`: comprueba hashes antes de cualquier ejecución.
- `--run`: inicia las pruebas (sin este parámetro solo inventaría).

## Interpretación

Las variantes Q4_K_M y UD-Q4_K_XL no son el mismo esquema ni necesariamente la misma tasa de bits. Los resultados de velocidad se deben analizar junto al tamaño real y las condiciones de ejecución. El benchmark mide velocidad de prefill/decode, **no** inteligencia ni fidelidad. Registrar temperatura, carga concurrente y configuración CUDA ayuda a controlar variaciones. Los modelos proceden de dos repositorios distintos; revisar identidad del checkpoint base antes de atribuir diferencias únicamente a cuantización.

## Nota de seguridad

El script no ejecuta código de los manifiestos; los lee como JSON. No requiere `sudo`. Si se interrumpe, conserva resultados parciales. No subas GGUF ni datos privados a GitHub.
