# Mejoras del pipeline: procesado más barato, citas comprobables y escritura menos previsible

Origen: reanálisis del 2026-11-14 sobre los 76 papers procesados de la biblioteca.

## Qué se ha medido (punto de partida)

- Secciones solapadas: el texto en secciones es 1,5 veces el del PDF (mediana, 33 papers). En otros se pierde texto (0,26 en el peor).
- 32 % de las secciones tiene menos de 150 palabras; 84 son administrativas. Cada sección cuesta 2 llamadas.
- 55 % de las ideas no lleva cita literal; solo el 8 % tiene una cita que aparece tal cual en el PDF.
- 48 % de los claims son afirmaciones apoyadas en otra obra (`evidence_type == "citation"`).
- `SECTION_CONFIGS` solo cubre el perfil «perspectiva»; «revisión» y «ensayo» heredan la ficha de «Introducción».
- `EvidenceEngine.topic_ideas` elige por cercanía al centro; la selección repartida (MMR) de `cluster_analyzer.py` solo la usa el flujo antiguo.
- La memoria entre secciones es un resumen de 150 palabras por sección.

## Contrato de datos (lo comparten todos los pasos)

Ideas (`ideas.jsonl`) y claims (`claims.jsonl`) ganan campos; los antiguos se conservan:

- `quote` (str): frase copiada literalmente del paper, de 40 palabras como mucho. Puede unir fragmentos con `…`.
- `quote_verified` (bool): `find_quote(quote, texto_del_paper)`. Los ítems antiguos no tienen el campo.
- Claims: `origin` = `"citado"` si `evidence_type == "citation"`, si no `"propio"`. `evidence_type` se normaliza a `experiment | data | observation | citation` (lo demás pasa a `observation`).
- Un ítem con `quote_verified is False` se guarda en la carpeta del paper pero **no** entra en `indices/all_ideas.jsonl` ni `all_claims.jsonl`. Sin el campo (ítems antiguos) entra como hasta ahora.
- `metadata.json` gana `procesado: {"metodo": 2, "llamadas": n, "segundos": t, "tramos": n}`.

Interfaces de los módulos nuevos:

```python
# src/ai_writer/processors/segmentation.py
@dataclass
class Segment:
    name: str      # nombres de las secciones unidas con " / "
    number: int    # 1, 2, 3…
    content: str
    start: int     # posición en el texto
    end: int

def segment(text: str, section_names: list[str], min_words: int = 150, max_words: int = 2500) -> list[Segment]

# src/ai_writer/processors/quotes.py
def find_quote(quote: str, text: str) -> bool

# src/ai_writer/support.py
def judge_document(folder: Path, llm=None) -> list[dict]
# cada dict: {"seccion", "frase", "clave", "veredicto": "apoyada"|"parcial"|"no_apoyada", "motivo", "cita_literal"}
```

## Pasos

### Ola 1 (en paralelo, archivos disjuntos)

| Paso | Qué | Archivos | Modelo |
|---|---|---|---|
| A1 | Segmentación sin solapes | `processors/segmentation.py`, `tests/test_segmentation.py` | Sonnet, medio |
| A2 | Comprobación de cita literal | `processors/quotes.py`, `tests/test_quotes.py` | Sonnet, medio |
| A3 | Ideas repartidas por tema; origen y cita literal en la búsqueda | `evidence.py`, `tests/test_citations.py` | Sonnet, medio |
| A4 | Ficha de búsqueda por perfil; texto completo en vez de resúmenes; marca de afirmación citada | `profiles.py`, `utils/enhanced_context_manager.py`, `perspective_run.py`, `agents/writer_agent.py`, `agents/reviewer_agent.py`, `tests/test_perspective_run.py` | Sonnet, alto |
| A5 | Juez de apoyo | `support.py`, `tests/test_support.py` | Sonnet, medio |
| V | Script de comparación del procesado | scratchpad | Haiku, medio |

### Ola 2

| Paso | Qué | Archivos | Modelo | Bloqueado por |
|---|---|---|---|---|
| B1 | Procesado nuevo: una llamada por tramo, cita literal, sin referencias, registro de llamadas | `processors/extraction_agent.py`, `pdf_processor.py`, `batch_processor.py`, `tests/test_regressions.py`, `tests/test_extraction.py`, `tests/conftest.py` | Sonnet, alto | A1, A2 |
| B2 | Enganchar el juez en el cierre y en `validacion.md` | `perspective_run.py`, `validation.py` | orquestador | A4, A5 |

### Ola 3: validación (orquestador)

1. Tests completos en verde.
2. Procesar 12 papers ya procesados con el método nuevo, en una biblioteca de prueba aparte. Comparar con sus salidas antiguas: llamadas, texto leído frente al PDF, ideas, % con cita literal verificada, hallazgos propios frente a afirmaciones citadas.
3. Sin llamadas: ideas elegidas por tema antes y después; evidencia que recibe «Síntesis Temática» antes y después.
4. Un ensayo corto con el código de `HEAD` y otro con el código nuevo, sobre la misma biblioteca de prueba; el juez de apoyo puntúa los dos.
5. Informe con ejemplos concretos.

## Decisiones

| Decisión | Elegido | Por qué |
|---|---|---|
| Qué hacer con un ítem cuya cita no aparece | Guardarlo, fuera de los índices | Se puede auditar y no llega al escritor |
| Ítems antiguos sin cita | Se siguen usando | Excluirlos vaciaría la biblioteca actual |
| Referencias de cada paper | Se dejan de extraer | Nada las usa |
| Afirmaciones citadas | Se marcan y puntúan ×0,85 | Siguen siendo útiles, redactadas como «según recoge A» |
| Memoria entre secciones | Texto completo de lo ya escrito + plan | Un resumen pierde matices y citas usadas |
| Papers de prueba | 12, de 2.000 a 11.000 palabras, con solape de 0,64 a 2,65 | Suficientes para temas y diversidad de fuentes, coste acotado |

## Nunca

- Modificar `src/ai_writer/utils/cluster_analyzer.py`, `README.md`, `docs/architecture.md`, `tests/test_topic_space.py`, `.graph-lab/` ni `.env`.
- Tocar la biblioteca real `~/Documentos/TheAIWriter/biblioteca` durante la validación.
- Hacer commit o push desde un agente.

## No especificado todavía

- Reprocesar los 76 papers antiguos: se decide con el coste real del método nuevo.
- Pares de ideas en tensión para el plan: después de medir la selección repartida.

## Progreso

| Paso | Estado |
|---|---|
| A1–A5, V | hecho (2026-11-14) |
| B1 | hecho (2026-11-14); prueba real con 1 paper: 10 llamadas, 66 de 67 citas verificadas |
| B2 | hecho (2026-11-14) |
| Tests | 165 pasan |
| Validación sin llamadas | hecha: tramos de los 12 papers, ideas del plan, evidencia por sección |
| Validación con llamadas | bloqueada: límite semanal de la cuenta, se restablece el 2026-11-18 a las 19:00 |

## Resultados hasta ahora (2026-11-14)

- 12 papers de prueba: 214 secciones → 110 tramos; 452 llamadas estimadas → 134. Texto leído frente al PDF: mediana 1,40 → 0,74.
- Paper real (Chain of Empathy): 36 llamadas estimadas → 10; ideas con cita verificada 33 % → 97,5 %; claims 0 % → 100 %; ideas 93 → 40.
- Ideas para el plan (colección «Emoción», 104 ideas): obras representadas 14 → 20 de 20; ideas de secciones de método 14 → 16.
- Evidencia para «Síntesis Temática», «Convergencias y Tensiones» y «Argumento»: antes solo claims de tipo cita; ahora experimentos, datos y observaciones.

## Pendiente

- Procesar los 12 papers de prueba y comparar con `comparar_procesado.py`.
- Ensayo antes y después, puntuado por el juez de apoyo.
- El corte en las referencias deja fuera los apéndices: el método nuevo lee entre el 52 % y el 89 % de las palabras del PDF. Falta separar cuánto es bibliografía y cuánto apéndice, y decidir si se recuperan.
- Etiquetar el tipo de cada idea (hallazgo, concepto, método, limitación…) en la misma llamada de extracción, para que el plan no reciba detalles de método. `importance` no sirve: el 65 % de las ideas es «high».

## Validación con llamadas (2026-11-14, tras levantar el límite)

Procesado de los 12 papers, antiguo → nuevo: llamadas 452 (estimadas) → 142; tiempo ~2 h → 30 min; ideas 1.150 → 697; ideas con cita literal verificada 45 % → 99 %; claims 0 % → 99 %. Tipos de idea: método 180, hallazgo 161, concepto 114, propuesta 85, contexto 80, limitación 77.

Ensayo (perfil «ensayo», misma biblioteca de 12 papers, una ejecución de cada):

| | Código anterior | Código nuevo |
|---|---|---|
| Palabras | 3.460 | 3.854 |
| Citas / obras citadas (de 12) | 57 / 10 | 65 / 12 |
| Huecos `[@?]` | 0 | 2 |
| Llamadas | 31 | 46 (incluye el juez) |
| Juez: apoyada / parcial / no apoyada | 23 / 26 / 7 | 25 / 36 / 4 |
| Apoyo pleno | 41,1 % | 38,5 % |
| Revisión crítica | 7/10 | 7,5/10 |

Conclusiones:
- El procesado mejora de forma clara y medida.
- La escritura no muestra mejora medible en apoyo de las citas con una sola ejecución; bajan las no apoyadas (12,5 % → 6 %) y suben las parciales.
- El juez mide con ruido: juzga con las 3 evidencias de la obra más parecidas a la frase, no con las que vio el escritor. Varias «no apoyadas» son falsos negativos (la biblioteca sí tiene la idea, pero no entró entre las 3).
- La mayoría de las «parciales» son frases que añaden una inferencia propia a un dato citado.
- El plan del ensayo nuevo tiene 5 secciones (el planificador añadió «Marco conceptual»); el perfil tiene 4.

Siguiente: que el juez use la evidencia que recibió el escritor en ese párrafo; repetir la medida con varias ejecuciones; decidir si las inferencias propias deben ir sin cita.

## Juez corregido (2026-11-14)

El juez recibe ahora hasta 12 evidencias por frase y obra: las más parecidas a la frase y las que el escritor tuvo delante en esa sección (`revision/evidencia_vista.json`; en borradores anteriores se reconstruyen con las consultas de `evidencia.json`). Tests: 175 pasan.

Mismos dos ensayos, vueltos a medir:

| | Código anterior | Código nuevo |
|---|---|---|
| Apoyada / parcial / no apoyada | 19 / 28 / 9 | 33 / 32 / 0 |
| Apoyo pleno | 33,9 % | 50,8 % |

- Una sola ejecución de cada ensayo; falta repetir para tener margen de error.
- El juez no es estable: entre la primera medida y la segunda, 12 de 56 veredictos del ensayo anterior y 12 de 65 del nuevo cambiaron entre «apoyada» y «parcial». Falta medir su consistencia juzgando dos veces el mismo borrador con la misma evidencia.
- Con más evidencia, el juez detectó en el ensayo anterior frases que dicen lo contrario que la obra citada (festor2026human: el ensayo afirma que la empatía percibida depende del encuadre; el paper concluye que no depende de la etiqueta de autoría).

## Experimento: ¿aporta algo frente a darle los papers a Claude? (2026-11-14)

Mismo resumen, mismos 12 papers, mismo modelo. Juez común: cada frase citada frente al texto completo del paper citado. Una ejecución de cada versión.

| | A. Pipeline (párrafo a párrafo) | B. Claude directo (1 llamada, 12 papers enteros) | C. Consulta a demanda (`demand_run.py`) |
|---|---|---|---|
| Palabras | 3.854 | 4.168 | 3.769 |
| Frases con cita | 65 | 94 | 71 |
| Apoyadas | 24 (37 %) | 62 (66 %) | 47 (66 %) |
| Parciales / no apoyadas | 37 / 4 | 32 / 0 | 22 / 2 |
| Obras citadas (de 12) | 12 | 12 | 11 |
| Revisión crítica a ciegas | 6/10 | 6/10 | 6/10 |

- Con 12 papers, Claude directo iguala o supera a la herramienta en fidelidad de citas, con una sola llamada.
- La consulta a demanda iguala a Claude directo (66 %) leyendo solo lo que consulta, y casi dobla al pipeline (37 %) con el mismo plan y la misma biblioteca.
- La revisión crítica no distingue entre las tres.
- Pendiente: repetir para tener margen de error, y probar con una biblioteca que no quepa en una llamada, que es donde C debería aportar y B no puede.

## Experimento: índice de ideas frente a trozos sin procesar (2026-11-14)

Versión D: misma escritura con consulta a demanda y mismo plan que C, pero el índice son trozos de ~180 palabras de los mismos tramos, sin ninguna llamada al modelo (270 trozos, índice en 43 s). Mismo juez (frase frente al texto completo del paper).

| | C. Índice de ideas | D. Índice de trozos |
|---|---|---|
| Frases con cita | 71 | 61 |
| Apoyadas | 47 (66 %) | 33 (54 %) |
| Parciales / no apoyadas | 22 / 2 | 24 / 4 |
| Obras citadas (de 12) | 11 | 10 |
| Búsquedas distintas | 23 | 15 |
| Llamadas / coste equivalente | 27 / 1,21 $ | 23 / 1,36 $ |
| Coste de preparar la biblioteca | 142 llamadas, 30 min | 0 llamadas, 43 s |

- Los trozos sin procesar ya superan con claridad al pipeline por párrafos (54 % frente a 37 %).
- Las ideas salen 12 puntos por encima de los trozos, pero con una ejecución de cada una y 60–70 frases la diferencia no es concluyente.
- Arreglo de paso: `EvidenceEngine._candidates` fallaba con un índice vacío (biblioteca sin claims).
- Pendiente: repetir C y D para saber si los 12 puntos son reales; de eso depende si el procesado merece su coste.
