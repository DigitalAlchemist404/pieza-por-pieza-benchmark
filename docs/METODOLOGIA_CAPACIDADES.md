# Recalificación de la corrida sin thinking (n=100 por benchmark/modelo)

- Fuente: `answers.jsonl` compartido por el usuario; 1,200 registros.
- Configuración registrada en `run_config.json`: chat_completions, `enable_thinking=false`, temperatura 0, máximo 512 tokens, seed 42, contexto 8192. El registro demuestra la configuración solicitada, no una verificación independiente de que el modelo respetara el modo.
- Las 121 respuestas marcadas `noncanonical_choice` finalizaron con `finish_reason=stop` y siguen el patrón `^[A-D1-5][).:]` seguido de texto. Se recuperó exclusivamente el identificador de opción inicial, sin buscar la respuesta correcta dentro del texto.
- Se conservaron las calificaciones previas de las 1,079 respuestas `ok`, incluyendo las 400 de GSM8K.
- Los cuatro modelos recibieron los mismos hashes de pregunta por índice y benchmark.
- `answers_regraded.jsonl` conserva el original salvo los 121 campos de calificación corregidos.
- Los porcentajes son de un protocolo personalizado con 100 preguntas por benchmark, no puntuaciones oficiales de benchmarks completos ni prueba de superioridad causal de un método de cuantización.
- Los porcentajes son descriptivos; diferencias pequeñas pueden deberse al muestreo.
