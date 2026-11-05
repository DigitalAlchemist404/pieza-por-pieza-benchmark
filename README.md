# 🦁 Pieza por Pieza — ¿Menos bits = menos inteligencia?

¡Buenas, gente! 🔥 Hoy quiero comprobar algo que venimos conversando en los videos: **si reducimos los bits de una IA, ¿qué pasa con sus respuestas?** No quiero quedarme con una gráfica bonita: quiero correr las pruebas, ver cuántas preguntas acierta y compartir los resultados para que cualquiera pueda repetirlos. ¡Vamos pieza por pieza! 💪

## 🎯 Nuestro experimento

Probamos cuatro GGUF de **Qwen3.5-35B-A3B** en una **NVIDIA GB10 / GX10**:

| Convencionales | Unsloth Dynamic |
| --- | --- |
| Q4_K_M | UD-Q4_K_XL |
| IQ2_XXS | UD-IQ2_XXS |

**La pregunta principal es qué capacidades conservan**. Usamos tres evaluaciones públicas con respuestas verificables:

- **MMLU** (`cais/mmlu`, test): conocimientos y preguntas de opción múltiple.
- **GSM8K** (`openai/gsm8k`, test): problemas matemáticos.
- **ARC-Challenge** (`allenai/ai2_arc`, test): preguntas de ciencias y razonamiento.

También conservamos la velocidad de procesamiento y generación, y tenemos una opción para medir perplejidad con un corpus de texto propio.

## 📊 Lo que ya corrimos

En `data/pilot_accuracy.csv` están los resultados del **piloto de 5 preguntas por prueba y modelo**. Es una prueba de funcionamiento, no nuestra evaluación final. En `data/velocity.csv` están los resultados del benchmark de velocidad ya realizado. Las salidas originales están dentro de `results/` en este paquete, pero Git las ignora para que no subamos rutas de nuestro equipo por accidente.

**Dato que encontramos al revisar los archivos:** los GGUF convencionales reportan 41 bloques y los Dynamic 40. Por eso presentamos los aciertos observados de estos archivos, sin atribuir automáticamente las diferencias solo a los bits. Antes de estudiar fidelidad contra un checkpoint original, tenemos que verificar que la referencia y la arquitectura sean equivalentes.

## 🚀 Empezá aquí — Linux, macOS y Windows

**Antes de empezar:** necesitás Python 3.10+, una versión de `llama.cpp` ya instalada y compatible con tu equipo, los modelos GGUF y memoria suficiente. **Este repositorio no enseña a instalar `llama.cpp`**: ese tema tendrá su propio tutorial. No instala drivers, no descarga modelos automáticamente y no necesita privilegios de administrador para configurar el entorno Python.

### Opción A — Preparación automática

**Linux o macOS** (Terminal, desde la carpeta del proyecto):

```bash
bash setup.sh
.venv/bin/python scripts/configure.py
```

**Windows** (PowerShell, desde la carpeta del proyecto):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\python.exe scripts\configure.py
```

El modificador `-ExecutionPolicy Bypass` se aplica solo al proceso que ejecuta ese comando; no cambia permanentemente la política de ejecución. Revisá el contenido de `setup.ps1` antes de ejecutarlo. **No necesitás WSL2 ni Git Bash** para preparar el proyecto en Windows.

`configure.py` te pregunta por la carpeta que contiene los GGUF y por la carpeta de los ejecutables `llama.cpp`. Guarda las rutas en `config.local.json`, **que no se sube a GitHub**. Si tenés los archivos en distintas carpetas, podés editar ese JSON y especificar una ruta completa por modelo.

### Opción B — Preparación manual

**1. Comprobá Python 3.10 o superior:**

Linux/macOS:
```bash
python3 --version
```

Windows (PowerShell):
```powershell
py -3 --version
```

Si falta Python, instalalo mediante el gestor de paquetes de tu sistema o el instalador oficial. En Debian/Ubuntu puede hacer falta `python3-venv`.

**2. Creá un entorno virtual:**

Linux/macOS:
```bash
python3 -m venv .venv
```

Windows:
```powershell
py -3 -m venv .venv
```

**3. Instalá las dependencias:**

Linux/macOS:
```bash
.venv/bin/python -m pip install -r requirements-eval.txt
```

Windows:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-eval.txt
```

**4. Configurá las rutas de los modelos y ejecutables:**

Linux/macOS:
```bash
.venv/bin/python scripts/configure.py
```

Windows:
```powershell
.\.venv\Scripts\python.exe scripts\configure.py
```

**5. Comprobá el inventario** (Linux/macOS):
```bash
.venv/bin/python scripts/run.py
```

Windows:
```powershell
.\.venv\Scripts\python.exe scripts\run.py
```

> Los cuatro archivos GGUF son necesarios para ejecutar la batería completa. El inventario comprueba que existen y muestra sus tamaños; para configuraciones manuales no verifica automáticamente los hashes de origen.

### 📥 Modelos exactos utilizados

**Convencionales — Bartowski:** [Qwen_Qwen3.5-35B-A3B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3.5-35B-A3B-GGUF/tree/main)

- `Qwen_Qwen3.5-35B-A3B-Q4_K_M.gguf` — ~22.3 GB
- `Qwen_Qwen3.5-35B-A3B-IQ2_XXS.gguf` — ~10.7 GB

**Dynamic — Unsloth:** [Qwen3.5-35B-A3B-GGUF](https://huggingface.co/unsloth/Qwen3.5-35B-A3B-GGUF/tree/main)

- `Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf` — ~22.2 GB
- `Qwen3.5-35B-A3B-UD-IQ2_XXS.gguf` — ~10.7 GB

Abrí la página del repositorio correspondiente, buscá el nombre **exacto** del archivo en «Files and versions» y descargalo. Comprobá que la variante coincida; algunas distribuciones ofrecen archivos divididos en varias partes. Los nombres y tamaños se tomaron de los archivos usados en nuestro experimento; revisá disponibilidad y condiciones de uso en las páginas originales.

### Ejecutar las pruebas — comandos para copiar

En Linux/macOS, usá `.venv/bin/python`; en Windows, sustituí por `.\.venv\Scripts\python.exe`. La configuración de rutas funciona en los tres sistemas.


**Verificar modelos** (usa `config.local.json` o, si no existe, los manifiestos de Unsloth Studio):

```bash
python3 scripts/run.py
```

**Preparar cinco preguntas** de MMLU, GSM8K y ARC-Challenge, sin cargar modelos:

```bash
.venv/bin/python scripts/evaluate.py --prepare-only --limit 5 --out results/nueva_prueba
```

**Evaluar los cuatro modelos** (necesita `llama-server`; si está en otra ubicación, pasá `--server /ruta/al/llama-server`):

```bash
.venv/bin/python scripts/evaluate.py --limit 5 --out results/nueva_prueba
```

**Resumir aciertos:**

```bash
python3 scripts/summarize.py --input results/nueva_prueba/answers.jsonl --out results/nueva_prueba/summary.csv
```

**Velocidad** (necesita `llama-bench`; si está en otra ubicación, pasá `--bench /ruta/al/llama-bench`):

```bash
python3 scripts/run.py --run --reps 3
```

**Perplejidad** (necesita un corpus UTF-8 y `llama-perplexity`):

```bash
python3 scripts/perplexity.py --corpus datasets/wikitext2_test.txt --ctx-size 2048
```

Si el ejecutable está en otra ubicación, añadí `--binary /ruta/al/llama-perplexity`. El corpus WikiText-2 debe prepararse localmente antes de ejecutar la prueba; no se incluye en el repositorio.

**Exportar resultados numéricos para GitHub:**

```bash
python3 scripts/export_public.py --answers results/nueva_prueba/answers.jsonl --velocity results/velocity
```

Para un estudio más amplio, cambiá `--limit 5` por `--limit 100` o `--limit 500`, siempre con una **carpeta de salida nueva**. `--limit 0` usa el conjunto completo y puede tardar mucho. Los datos se descargan la primera vez; las inferencias se realizan localmente.

### Si algo falla

- **`.venv/bin/python: No such file or directory`**: ejecutá `bash setup.sh` o `python3 -m venv .venv`.
- **Falta `llama-server` / `llama-bench` / `llama-perplexity`**: compilá el ejecutable para tu plataforma y proporcioná su ruta con la opción correspondiente.
- **No se encontraron modelos**: ejecutá python3 scripts/configure.py e indicá dónde están tus modelos GGUF y los ejecutables de llama.cpp.
- **Sin memoria suficiente**: probá con un equipo más capaz o esperá a la futura opción para seleccionar menos modelos; no es necesario descargar todos para leer los resultados publicados.

## 🧩 Qué significa cada resultado

Si un modelo acertó más en MMLU, acertó más preguntas **de ese conjunto**. Eso es lo que vamos a enseñar. Para comparar fidelidad contra el original necesitaríamos ejecutar una referencia de mayor precisión: **esa prueba todavía no está implementada**.

La primera descarga de datasets necesita Internet; después, los modelos y la inferencia corren localmente. **No se descargan GGUF**. No subimos modelos, claves, tokens ni datos privados al repositorio.

## 🏆 ¿Por qué compartirlo?

¡Porque aprender es mucho más divertido cuando podemos poner las cosas a prueba! Acá comparto los scripts, los resultados y el procedimiento. Si alguien lo prueba en su equipo y obtiene resultados diferentes, ¡me encantaría comparar! 🔥

<!-- CAPACIDADES_NO_THINKING_INICIO -->
## 🎯 Capacidades: evaluación sin thinking

Ejecutamos cuatro variantes GGUF con 100 preguntas por benchmark
y por modelo: **1,200 respuestas en total**.

| Modelo | MMLU | GSM8K | ARC-Challenge |
|---|---:|---:|---:|
| Normal Q4_K_M | 80% | 34% | 96% |
| Dynamic Q4_K_XL | 80% | 31% | 96% |
| Normal IQ2_XXS | 74% | 26% | 91% |
| Dynamic IQ2_XXS | 81% | 29% | 94% |

**Condiciones registradas:** temperatura 0, semilla 42,
máximo 512 tokens por respuesta y solicitud de
`enable_thinking=false`.

La configuración registra el modo solicitado, pero no demuestra
por sí sola que cada modelo lo haya respetado internamente.

Se recalificaron **121 respuestas de opción múltiple** que
contenían una letra inicial seguida del texto de la opción.
Las respuestas originales se conservaron para auditoría.

Estos porcentajes corresponden a nuestro protocolo personalizado,
no a puntuaciones oficiales de los benchmarks completos.
Las diferencias pequeñas no demuestran superioridad estadística.
Tampoco hemos confirmado la equivalencia exacta de los checkpoints
utilizados por ambas familias de GGUF.

**Archivos públicos:**

- [Resultados de capacidades](data/capacidades_no_thinking_n100_seed42.csv)
- [Correcciones de extracción](data/correcciones_extraccion_121.csv)
- [Selección de preguntas](data/dataset_manifest_no_thinking.json)
- [Configuración registrada](data/run_config_no_thinking.json)
- [Metodología y limitaciones](docs/METODOLOGIA_CAPACIDADES.md)

<!-- CAPACIDADES_NO_THINKING_FIN -->
