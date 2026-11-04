# Estado del experimento

- **Velocidad:** 8 escenarios completados, 3 repeticiones por escenario. JSONL originales incluidos localmente.
- **Capacidades:** piloto completado, 5 preguntas × 3 datasets × 4 modelos = 60 respuestas. No es una evaluación definitiva.
- **Datasets:** MMLU test, GSM8K test y ARC-Challenge test; semilla 42, selección registrada en `results/pilot/capacidades/dataset_manifest.json`.
- **Arquitectura:** diferencia 41/40 bloques observada en revisión anterior. Falta verificar equivalencia de checkpoint.
- **Fidelidad de logits/KL:** pendiente; no se incluye un evaluador funcional.
- **Perplejidad:** script disponible, requiere corpus local y llama-perplexity; sin resultados previos.
- **Corrección v4:** las corridas nuevas rechazan reanudar con selección de preguntas incompatible o respuestas sin firma de pregunta. El piloto anterior se conserva intacto.
