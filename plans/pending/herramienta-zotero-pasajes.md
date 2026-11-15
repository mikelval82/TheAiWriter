# Plan: TheAIWriter como herramientas de consulta y verificación sobre Zotero

Estado: **aprobado el 2026-11-15, en ejecución**. Fecha: 2026-11-15.
Parte de las mediciones de `mejoras-pipeline.md` y de la revisión de `herramientas-existentes.md`.

## Qué cambia

Claude planifica y escribe por su cuenta. El plugin deja de escribir y pasa a darle tres cosas:

- **Buscar** pasajes en una colección de Zotero, con clave de cita, sección y página.
- **Leer** alrededor de un resultado: trozos vecinos, sección entera o páginas.
- **Verificar** el borrador: la obra existe, la cita literal está en el PDF, la frase coincide con lo que dice el paper.

La biblioteca es Zotero. Añadir un paper es meterlo en Zotero; el índice se actualiza solo y sin llamadas a Claude.

## Lo que se ha comprobado en este ordenador (solo lectura)

- Zotero 10 está instalado y abierto. Su API local responde 403: está desactivada, que es el valor por defecto.
- `~/Zotero/zotero.sqlite` tiene 276 obras, 100 PDF adjuntos y la colección «TheAIWriter – Empatía en agentes» con 152 obras.
- Con Zotero abierto hay cambios recientes que solo están en el archivo `-wal`. Leer el `.sqlite` solo da datos atrasados; una copia temporal de los dos archivos se lee bien.
- Los 100 PDF tienen al lado un `.zotero-ft-cache`: el texto ya extraído por Zotero, con saltos de página. En 5 de 102 el texto está recortado por el límite de páginas de Zotero.
- Ninguna obra tiene clave de cita en Zotero. No hay Better BibTeX instalado.
- `cluster_analyzer.py` solo lo usan `advanced_orchestrator.py` y `tests/test_topic_space.py`.

## Decisiones

| # | Decisión | Opción recomendada | Por qué |
|---|---|---|---|
| D1 | Índice de ideas | Se queda fuera de la base. Se mide como capa opcional en la fase 8 y se decide con datos | 66 % frente a 54 % es una sola ejecución contra un troceado sencillo |
| D2 | Código antiguo de escritura | Se borra en la fase 7, cuando la herramienta nueva haya pasado la medición | El historial de git lo conserva; mantener dos caminos duplica el mantenimiento |
| D3 | Biblioteca propia (`~/Documentos/TheAIWriter/biblioteca`) | El plugin deja de usarla. No se toca ni se borra del disco | Contiene 76 papers procesados que solo servirían para la fase 8 |
| D4 | Trabajo sin commit (`demand_run.py`, cambios de `evidence.py`, pruebas, planes) | Commit en `develop` como registro del experimento, y rama nueva `zotero-pasajes` para este plan | `DemandRun` se borrará en la fase 7, pero el experimento queda en el historial |
| D5 | Listón de la medición | Dos ejecuciones con los 12 papers y el juez común; media no inferior al 60 % de frases apoyadas | El juez varía entre ejecuciones y no hemos medido cuánto; ayer B y C dieron 66 % y D 54 % |
| D6 | Cómo se lee Zotero | Archivos locales en solo lectura (copia temporal de la base de datos y carpeta `storage`). Nunca se escribe en Zotero | Funciona con Zotero abierto o cerrado y la alumna no tiene que activar nada |
| D7 | Texto de los PDF | Extraído con PyMuPDF, que ya usamos, página a página | El texto de Zotero viene recortado en documentos largos |
| D8 | Secciones | Detectadas sin modelo: índice del PDF, después tamaño de letra, después corte por tamaño | Mantiene el índice gratis; hoy `segment()` necesita una llamada por paper |
| D9 | Claves de cita | La de Zotero o Better BibTeX si existe; si no, la genera `make_key`, como ahora | Hoy no hay ninguna en Zotero |
| D10 | Búsqueda por palabras | BM25 propio y fusión de rangos con la búsqueda por significado. Sin dependencias nuevas ni reordenador | El reordenador exige otro modelo de cientos de megas |
| D11 | Juez de apoyo | Sigue siendo una llamada aparte a `claude -p`, no la misma sesión que escribe | Quien escribe no debe juzgarse a sí mismo |

D1 a D5 son tuyas. D6 a D11 son técnicas: las tomo así salvo que digas otra cosa.

### Supuestos

1. Instrucciones, comandos e informes en español; los papers y las búsquedas pueden ir en inglés.
2. Un documento se liga a una o varias colecciones de Zotero, con sus subcolecciones.
3. Se mantienen las citas `[@clave]` y la exportación de `referencias.bib`, ahora desde los metadatos de Zotero.
4. Los documentos de tipo «paper con resultados» y «convocatoria» del diseño anterior no entran en este plan.
5. El índice de pasajes se guarda en la carpeta de datos del plugin, no dentro de Zotero.

## Fases

### Fase 0: Preparación
Verificada cuando: `develop` tiene el experimento en un commit y existe la rama `zotero-pasajes`.

#### Paso 0.1: Commit del experimento y rama (Tamaño: XS)
- Criterios: commit solo de `demand_run.py`, `evidence.py`, `tests/test_demand_run.py`, `tests/test_citations.py` y los planes; ningún archivo con cambios propios del usuario.
- Verificación: `.venv/bin/python -m pytest -q` (188 pruebas) y `git status --short`.
- Bloqueado por: ninguno.

### Fase 1: Lector de Zotero
Es la única pieza nueva de verdad y la de más riesgo, por eso va primero.
Verificada cuando: el lector da 276 obras, 100 PDF y la colección de 152 sobre el Zotero real, sin escribir nada en `~/Zotero`.
Archivos: `src/ai_writer/zotero.py` (nuevo), `tests/test_zotero.py` (nuevo).

#### Paso 1.1: Lectura segura de la base de datos (Tamaño: S)
- Criterios: localiza la carpeta de datos (variable de entorno, perfil de Zotero, `~/Zotero`); lee desde una copia temporal de `.sqlite` y `-wal`; error claro en español si no hay Zotero.
- Verificación: `pytest tests/test_zotero.py -q`.
- Costuras de prueba: una base de datos mínima creada en la prueba con el esquema de Zotero.
- Bloqueado por: 0.1.

#### Paso 1.2: Obras, colecciones y adjuntos (Tamaño: M)
- Criterios: árbol de colecciones con sus obras; metadatos (título, autores, año, DOI, revista, tipo); ruta del PDF para adjuntos guardados y enlazados; clave de cita según D9, atada al identificador de la obra en Zotero y conservada como alias si más tarde aparece una clave de Better BibTeX.
- Verificación: `pytest tests/test_zotero.py -q` y un guion de comprobación contra el Zotero real que compara los recuentos.
- Bloqueado por: 1.1.

### Fase 2: Índice de pasajes
Verificada cuando: los 12 papers de prueba se indexan sin llamadas a Claude y cada pasaje tiene clave, sección y páginas.
Archivos: `src/ai_writer/passages.py` (nuevo), `src/ai_writer/processors/segmentation.py`, `src/ai_writer/embeddings/embedding_index.py`, `tests/test_passages.py` (nuevo).

#### Paso 2.1: Texto por páginas y secciones sin modelo (Tamaño: M)
- Criterios: títulos de sección según D8; se saltan referencias y secciones administrativas como hace `segment()`; cada tramo conserva página inicial y final.
- Verificación: `pytest tests/test_passages.py tests/test_segmentation.py -q`; tabla con las secciones detectadas en los 12 papers frente a las que dio el modelo.
- Bloqueado por: 0.1.

#### Paso 2.2: Pasajes e índice incremental (Tamaño: M)
- Criterios: pasajes de 150 a 400 palabras dentro de cada sección, sin solapes; solo se reindexan los PDF nuevos o cambiados; un PDF sin texto se informa y no rompe el índice.
- Verificación: `pytest tests/test_passages.py -q`; tiempo de indexado de los 12 papers.
- Bloqueado por: 1.2, 2.1.

#### Paso 2.3: Búsqueda combinada (Tamaño: S)
- Criterios: BM25 y significado fundidos por rango; filtro por colecciones y por claves; tope de resultados por obra.
- Verificación: `pytest tests/test_passages.py -q`; diez consultas de ejemplo con sus resultados, con y sin la parte de palabras.
- Bloqueado por: 2.2.

### Fase 3: Herramientas para Claude
Verificada cuando: una sesión de Claude con el plugin busca, lee y cita desde una colección de Zotero.
Archivos: `src/ai_writer/mcp_server.py`, `src/ai_writer/library.py` (`Project`), `tests/test_mcp_server.py`.

#### Paso 3.1: Buscar, leer y colecciones (Tamaño: M)
- Criterios: `colecciones_zotero`, `buscar_pasajes` y `leer_pasaje` (vecinos, sección o páginas); el índice se actualiza al buscar si hay PDF nuevos; cada consulta queda registrada en el documento para el juez.
- Verificación: `pytest tests/test_mcp_server.py -q`.
- Bloqueado por: 2.3.

#### Paso 3.2: Documento ligado a colecciones de Zotero (Tamaño: S)
- Criterios: `crear_documento` acepta colecciones de Zotero; `referencia` y `referencias.bib` salen de Zotero.
- Verificación: `pytest tests/test_mcp_server.py tests/test_citations.py -q`.
- Bloqueado por: 1.2.

### Fase 4: Verificación
Verificada cuando: sobre un borrador con errores sembrados (clave inventada, cita literal alterada, frase que el paper no dice) el informe detecta los tres.
Archivos: `src/ai_writer/support.py`, `src/ai_writer/validation.py`, `src/ai_writer/citations.py`, `src/ai_writer/processors/quotes.py`, `hooks/validar.py`, pruebas correspondientes.

#### Paso 4.1: Existencia y cita literal (Tamaño: M)
- Criterios: las claves se comprueban contra las colecciones del documento; cada texto entre comillas junto a una cita se busca en el PDF con `QuoteChecker`; si no coincide, se muestran las diferencias palabra a palabra con el pasaje más parecido.
- Verificación: `pytest tests/test_citations.py tests/test_quotes.py -q`.
- Bloqueado por: 3.2.

#### Paso 4.2: Juez de apoyo sobre pasajes (Tamaño: M)
- Criterios: el juez recibe los pasajes de la obra más cercanos a la frase y los que Claude consultó; veredictos apoyada, parcial, tergiversada y no apoyada; una llamada por párrafo con citas.
- Verificación: `pytest tests/test_support.py -q`.
- Bloqueado por: 3.1.

### Fase 5: Flujo guiado
Verificada cuando: en una carpeta vacía, `/theaiwriter:nuevo` y `/theaiwriter:escribir` producen un borrador con citas y su informe.
Archivos: `commands/*.md`, `.claude-plugin/plugin.json`.

#### Paso 5.1: Comandos reescritos (Tamaño: S)
- Criterios: `/nuevo` elige colecciones de Zotero; `/escribir` son instrucciones para que Claude planifique, consulte y escriba en la sesión; `/validar` lanza la verificación; `/biblioteca` muestra Zotero y el estado del índice.
- Verificación: prueba manual en una carpeta del scratchpad, con el resultado pegado en el registro de ejecución.
- Bloqueado por: 4.2.

### Fase 6: Medición
Verificada cuando: está la tabla A–D de ayer con una fila E nueva y ejemplos concretos de frases ganadas y perdidas.

#### Paso 6.1: Los 12 papers en Zotero (Tamaño: S)
- Criterios: los 12 PDF de prueba están accesibles como colección; si no están todos en el Zotero real, se monta una carpeta de Zotero de prueba en el scratchpad y el Zotero real no se toca.
- Bloqueado por: 1.2.

#### Paso 6.2: Dos ejecuciones y juez común (Tamaño: M)
- Criterios: mismo resumen y mismo juez de texto completo que ayer; se informa del resultado de cada ejecución y de la media, también si no llega al listón de D5.
- Verificación: `juez_texto_completo.py` sobre cada borrador.
- Bloqueado por: 5.1, 6.1.

### Fase 7: Retirada del código antiguo
Solo si la fase 6 pasa el listón. Si no lo pasa, se para y se decide contigo.
Verificada cuando: las pruebas pasan, el plugin arranca y `cluster_analyzer.py` y `tests/test_topic_space.py` siguen intactos.

#### Paso 7.1: Escritura por párrafos (Tamaño: M)
- Criterios: se borran `perspective_run.py`, `demand_run.py`, `agents/`, `orchestrators/`, `enhanced_context_manager.py` y sus herramientas, comandos y pruebas; antes se comprueba qué necesita `tests/test_topic_space.py` y eso no se borra.
- Verificación: `.venv/bin/python -m pytest -q`.
- Bloqueado por: 6.2.

#### Paso 7.2: Biblioteca propia y procesado (Tamaño: M)
- Criterios: se retiran del plugin las herramientas de añadir y procesar PDF; el código de extracción de ideas se mantiene hasta decidir D1 en la fase 8.
- Verificación: `.venv/bin/python -m pytest -q`.
- Bloqueado por: 7.1.

### Fase 8: Ideas como capa opcional
Verificada cuando: hay una medición de pasajes frente a pasajes más ideas, con dos ejecuciones por opción, y una decisión tuya.

#### Paso 8.1: Medir y decidir (Tamaño: M)
- Criterios: mismas condiciones que la fase 6; se informa también del coste en llamadas de construir las ideas.
- Bloqueado por: 7.2.

## Sin especificar todavía

- Fase 2: si la detección de secciones sin modelo falla en muchos de los 12 papers, ¿se acepta una llamada por paper o se corta solo por tamaño? Se decide con la tabla del paso 2.1.
- Fase 5: cómo instalar el modelo de embeddings en el ordenador de una alumna sin terminal. Se revisa al llegar.
- Fase 7: `README.md` y `docs/architecture.md` quedarán desfasados, pero tienen cambios tuyos sin commit. No se tocan hasta que lo digas.
- Rutas de «paper con resultados» y «convocatoria»: fuera de este plan.

## Siempre / Nunca

- Siempre: Zotero en solo lectura; pruebas en verde al cerrar cada paso; cada medición con sus ejemplos, incluido lo que no mejora.
- Nunca: escribir en `~/Zotero`; tocar `cluster_analyzer.py`, `tests/test_topic_space.py`, `.graph-lab/` o `.env`; usar la biblioteca real; hacer push; instalar software de terceros; procesar los 81 PDF pendientes.

## Progreso

| Fase | Estado |
|---|---|
| 0. Preparación | Hecha |
| 1. Lector de Zotero | Hecha |
| 2. Índice de pasajes | Hecha |
| 3. Herramientas para Claude | Hecha |
| 4. Verificación | Hecha |
| 5. Flujo guiado | Hecha |
| 6. Medición | Hecha |
| 7. Retirada del código antiguo | Hecha: de 17.550 a 7.671 líneas, 181 pruebas en verde |
| 8. Ideas como capa opcional | Medida con 50 papers: empate (85 % pasajes, 89 % ideas). Código de ideas conservado |

## Registro de ejecución (2026-11-15)

### Cambios respecto al plan

| Qué | Plan | Hecho | Por qué |
|---|---|---|---|
| Mezcla de búsqueda (D10) | Fusión de rangos | Suma ponderada al 50 % de las dos puntuaciones normalizadas | Con 653 ideas verificadas como consulta y su pasaje de origen como acierto, la fusión de rangos acierta el primero en el 71,5 % y la suma ponderada en el 87,9 % (solo significado: 53,8 %; solo palabras: 91,4 %). La prueba favorece a las palabras porque las ideas se redactaron leyendo el pasaje, así que no se deja solo BM25 |
| Tamaño del pasaje | 150 a 400 palabras | 150 a 300 | El modelo de búsqueda solo lee unas 500 piezas de texto por pasaje |
| Carpeta del índice (supuesto 5) | Datos del plugin | `Documentos/TheAIWriter/indice` | El hook de edición corre fuera del servidor y tiene que encontrar las claves en el mismo sitio |
| Claves y Better BibTeX (paso 1.2) | Alias | La primera clave asignada se queda para siempre | Más simple y los borradores ya escritos siguen valiendo |
| Cita literal | `QuoteChecker` | Comparación palabra a palabra | `QuoteChecker` tolera un 8 % de diferencia: daba por literal una cita con «narrow» donde el PDF dice «broad» |
| Paso 6.1 | Colección en el Zotero real o carpeta de prueba | Carpeta de Zotero de prueba en el scratchpad | El Zotero real no se toca |
| Reparto | — | Codex escribió BM25 y la explicación de diferencias de una cita, y hace la retirada de la fase 7 | Pedido por el usuario para repartir el gasto |

### Verificaciones

- Lector contra el Zotero real: 272 obras (4 en la papelera), 100 PDF, colección de 152 obras con 50 PDF, en 0,1 s y sin cambios en `~/Zotero`.
- Secciones sin modelo en los 12 papers: 7 por el índice del PDF, 5 por el tamaño de letra, ninguno por tamaño. 251 pasajes, indexados en 49 s sin llamadas a Claude.
- Borrador con errores sembrados: detectados la clave inventada, la cita literal alterada (con la palabra exacta), la frase contraria a la obra (tergiversada) y la frase que la obra no dice (no apoyada). Una llamada al juez, 7 s.
- Pruebas: 227 en verde antes de la fase 7.

### Medición (fase 6)

Mismo resumen, mismos 12 papers y mismo juez de texto completo que las versiones A–D de `mejoras-pipeline.md`. Claude (Sonnet) escribe en una sesión con las herramientas nuevas y las instrucciones de `/theaiwriter:escribir`, sin el juez de apoyo ni su ronda de correcciones.

| Versión | Frases apoyadas | Parciales | No apoyadas | Búsquedas | Tiempo de escritura |
|---|---|---|---|---|---|
| A. Pipeline por párrafos | 24/65 (37 %) | | | | |
| B. Claude directo, 12 papers en una llamada | 62/94 (66 %) | | | | |
| C. A demanda sobre ideas | 47/71 (66 %) | | | | |
| D. A demanda sobre trozos sencillos | 33/61 (54 %) | | | | |
| E1. Herramientas nuevas | 54/60 (90 %) | 6 | 0 | 10 | 2 min |
| E2. Herramientas nuevas | 48/56 (86 %) | 7 | 1 | 13 | 1 min 40 s |

Media de E: 88 %. Supera el listón de D5 (60 %).

Lo que esta medición no separa:

- E cambia a la vez los pasajes, la búsqueda y las reglas de cita del comando. Parte de la mejora puede venir de las reglas y no de los pasajes.
- E1 cita las 12 obras y E2 solo 10.
- La única frase «no apoyada» (E2, prueba de significación en `chen2024mixed`) es un error del juez de medición, que lee el paper solo hasta las referencias. El dato está en un apéndice posterior (p. 10, pasaje `chen2024mixed#22`): «the scores of ground truth are significantly higher than all model-generated results». El índice de pasajes sí llega a los apéndices.
- Los 7 + 6 veredictos «parcial» son casi todos inferencias del ensayo colgadas de una cita, no datos inventados.

## Fase 8: ideas frente a pasajes con 50 papers (2026-11-15)

Los 50 PDF de la colección «TheAIWriter – Empatía en agentes» se procesaron en ideas con modelos baratos, repartidos entre dos cuentas, y se indexaron también por pasajes. Datos en `Documentos/TheAIWriter/ideas-empatia` (fuera del repositorio).

| Procesado | Haiku (Claude) | gpt-6-luna (Codex) |
|---|---|---|
| Papers / páginas | 24 / 445 | 26 / 448 |
| Llamadas | 258 | 402 |
| Ideas (con cita verificada) | 1.231 (99,5 %) | 1.837 (98,4 %) |
| Claims (con cita verificada) | 1.078 (99,4 %) | 2.006 (97,4 %) |

Un ensayo por condición, mismo flujo (Claude Sonnet en sesión), mismo resumen y mismas reglas; solo cambia la herramienta de consulta. Juez común sobre el texto completo de cada paper, apéndices incluidos.

| | Pasajes | Ideas |
|---|---|---|
| Coste del índice | 5 min, 0 llamadas | 660 llamadas, 1 h 33 min con dos cuentas |
| Búsquedas / lecturas de contexto | 9 / 1 | 12 / 5 |
| Obras citadas | 23 de 50 | 19 de 50 |
| Frases apoyadas | 52/61 (85 %) | 54/61 (89 %) |
| Parciales / no apoyadas | 9 / 0 | 7 / 0 |

Lectura: empate dentro del ruido (dos frases de diferencia, una ejecución por condición). Con 50 papers las ideas no mejoran de forma apreciable a los pasajes, y los pasajes no se degradan respecto a los 12 papers (88 %). No se probó la condición con las dos herramientas a la vez ni bibliotecas de cientos de papers.
