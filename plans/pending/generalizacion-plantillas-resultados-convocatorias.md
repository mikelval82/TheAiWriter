# De "paper de perspectiva" a escritor de documentos científicos: plantillas LaTeX, resultados/código y convocatorias

Ticket: ninguno todavía
Estado: **propuesta, pendiente de aprobación**. No se ha implementado nada.
Fecha: 2026-11-10

## 1. Objetivo

Hoy TheAIWriter hace una sola cosa: un paper de perspectiva en Markdown a partir de un abstract y una colección de PDFs. El objetivo es que el mismo motor sirva para tres cosas más:

1. **Plantillas LaTeX**: el documento generado sale ajustado a una plantilla que aporta el usuario (revista, congreso, arXiv, formulario de convocatoria).
2. **Resultados y código**: el usuario aporta los resultados y el código de un análisis y el sistema escribe el paper de investigación correspondiente (métodos, resultados, discusión).
3. **Convocatorias**: a partir de las bases de una convocatoria, el sistema escribe la memoria de solicitud.

## 2. Qué hay hoy (análisis del repo)

### Flujo actual

`process` (PDF → texto con PyMuPDF → ideas, claims y referencias con LLM → embeddings) y después `generate`: clusters de ideas → outline párrafo a párrafo → escritura con RAG por párrafo → revisión por sección → resolución de citas → revisión crítica. Corpus actual: 43 papers, 3.733 ideas, 3.839 claims, 2.713 referencias.

### Lo que impide generalizar

| Limitación | Dónde | Consecuencia |
|---|---|---|
| Las 8 secciones del paper de perspectiva son una constante | `agents/planner_agent.py` (`PERSPECTIVE_SECTIONS`) | No se puede escribir otro tipo de documento |
| La lógica depende del **nombre** de la sección en español | `orchestrators/advanced_orchestrator.py` (`_create_section_topic_mapping`), `utils/enhanced_context_manager.py` (`SECTION_CONFIGS`), `agents/writer_agent.py` (`_get_section_instructions`) | Una sección nueva cae en el caso por defecto ("Introducción") sin avisar |
| Idioma español escrito dentro de los prompts | todos los agentes | El inglés solo se consigue traduciendo después |
| Un único corpus global y un abstract en ruta fija | `config/settings.py`, `data/processed/` | No hay concepto de proyecto: dos documentos distintos comparten índices |
| La única evidencia es la literatura (ideas y claims) | `utils/enhanced_context_manager.py` | No hay sitio para resultados propios, código ni bases de convocatoria |
| Salida solo en Markdown; el PDF es texto plano con PyMuPDF | `writers/` | No hay LaTeX, figuras, tablas ni ecuaciones |
| Citas como `[@Autor et al., Año]` resueltas por coincidencia de texto contra referencias extraídas por LLM | `utils/reference_processor.py` | No hay BibTeX ni claves estables. Una cita no resuelta se queda en el texto como si fuera válida, así que una cita inventada no se detecta |
| El modelo `Paper` es título + secciones de texto | `models/paper.py` | No puede representar figuras, tablas, límites de extensión ni metadatos de plantilla |

### Fallos encontrados al leer el código

Son fallos actuales, independientes de las funciones nuevas:

- **El paper final nunca se guarda con las citas resueltas.** `advanced_orchestrator.py:762` llama a `markdown_writer.write(reviewed_paper, paper_path)` con los argumentos al revés (la firma es `write(path, content)`). Lanza una excepción que el `except` de la línea 764 captura y presenta como "Paper guardado sin revisión final". En disco queda la versión incremental, anterior al postproceso de referencias y a la revisión global.
- `advanced_orchestrator.py:363` llama a `outline.to_dict()`, que no existe en `PaperOutline`. Falla cuando el revisor pide cambios en el outline y el logging está activo.
- `main.py:147` usa `settings.paths.pdfs_dir`, que no existe: el comando `process` falla si no se pasa `--input`.
- `main.py:186` importa `ai_writer.embeddings.embedding_manager`, que no existe: el comando `stats` falla siempre.
- `agents/translator_agent.py:30` apunta a una guía de estilo `mikel_val_calvo_uk_english.md`; el fichero del repo se llama `uk_english_writing_style.md`. No he comprobado qué hace el traductor cuando no la encuentra.
- `run()` llama a `phase1_analyze_topics()` sin título: todos los logs se guardan como `run_paper`.
- El revisor reescribe la sección entera con `max_tokens=4096` y sin comprobar después que las citas siguen ahí ni que no ha añadido otras.

### Deuda que conviene pagar antes de crecer

- Sin capa común de LLM: `PlannerAgent` no hereda de `BaseAgent`, el orquestador llama al cliente directamente, no hay reintentos, ni salida estructurada validada, ni recuento de coste. Solo OpenAI (la clave de Anthropic está en la configuración pero no se usa).
- Sin reanudación: si falla en la sección 6 hay que empezar de cero.
- Tests: un solo fichero (24 tests, pasan), todos sobre `ClusterAnalyzer`. Nada cubre agentes, orquestador ni referencias.
- Documentación desalineada: `docs/architecture.md` dice Docling, el código usa PyMuPDF; versión 1.1.0 frente a 1.0.0; `.env.example` con `gpt-4o`.
- Código muerto o duplicado: `perspective_paper_orchestrator.py` (antiguo), `scripts/test_*.py`, memoria de sección duplicada entre orquestador y revisor.
- CI: solo compila el ejecutable de Windows; no ejecuta tests ni linter.

## 3. Arquitectura objetivo

Cuatro conceptos nuevos. Todo lo demás se apoya en ellos.

```
proyecto/                      ← un documento = un proyecto
├── project.yaml               ← tipo, idioma, plantilla, fuentes
├── sources/
│   ├── literature/*.pdf       ← lo que hoy es data/references/pdfs
│   ├── library.bib            ← bibliografía del usuario (opcional)
│   ├── analysis/              ← resultados y código (opcional)
│   ├── call/                  ← bases de la convocatoria (opcional)
│   └── brief.md               ← hechos propios: idea, equipo, datos
├── template/                  ← plantilla LaTeX (opcional)
├── index/                     ← índices y embeddings del proyecto
├── runs/<fecha>/              ← estado, checkpoints, logs, coste
└── output/                    ← .md, .tex, .bib, .pdf, informes
```

1. **Proyecto** (`project.yaml`): sustituye a las rutas globales. Cada documento tiene su corpus, su configuración y sus ejecuciones.
2. **Blueprint** (`DocumentBlueprint` → `SectionSpec`): descripción declarativa del documento. Cada sección declara propósito, extensión (párrafos, palabras o páginas), **de qué fuentes de evidencia bebe**, parámetros de búsqueda, instrucciones de escritura, elementos obligatorios y criterios que atiende. Sustituye a `PERSPECTIVE_SECTIONS`, `SECTION_CONFIGS` y `_get_section_instructions`. Blueprints de serie: `perspective` (el actual), `research_paper` (IMRaD), `review`. Los de convocatoria se generan a partir de las bases.
3. **Fuentes de evidencia** (`EvidenceSource`): interfaz común `search(query, section_spec) → list[EvidenceItem]`. Cada `EvidenceItem` lleva texto, procedencia y una clave citable. Implementaciones: literatura (lo actual), hallazgos del análisis, hechos de métodos, requisitos de la convocatoria, hechos del brief.
4. **Documento intermedio y renderizadores**: el escritor produce Markdown restringido (citas `[@clave]`, figuras y tablas con etiqueta, matemáticas `$…$`). Un renderizador lo convierte a Markdown final, a LaTeX con plantilla o a DOCX. El contenido no sabe nada de la plantilla.

Regla transversal: **nada que el escritor afirme puede carecer de procedencia**. Solo puede citar claves presentes en la evidencia que recibió, solo puede dar cifras que existan en los hallazgos y solo puede afirmar hechos del equipo o del presupuesto que estén en el brief. Lo que falta se marca como `[[PENDIENTE: …]]` y aparece en un informe de huecos. Un validador automático lo comprueba después de cada escritura y de cada revisión.

## 4. Fases

Orden por riesgo y dependencia. Cada fase deja el sistema funcionando.

### Fase 0: Estabilizar lo que hay

Verificada cuando: `generate` termina y el fichero final contiene las citas resueltas y la sección de referencias; `process` y `stats` arrancan sin argumentos; CI en verde.

#### Paso 0.1: Arnés de tests con LLM falso (Tamaño: M)
- Criterios: un `FakeLLM` devuelve respuestas guionizadas; un corpus sintético mínimo (3 papers) vive en `tests/fixtures/`; un test de extremo a extremo ejecuta `run()` sin red.
- Verificación: `python -m pytest tests/test_pipeline_e2e.py`
- Ficheros: `tests/conftest.py`, `tests/fixtures/`, `tests/test_pipeline_e2e.py`
- Costura de test: `AdvancedPerspectiveOrchestrator.run()` con cliente inyectado
- Bloqueado por: ninguno

#### Paso 0.2: Corregir los fallos del apartado 2 (Tamaño: S)
- Criterios: los seis fallos listados tienen test de regresión; el `except` genérico de `run()` deja de ocultar errores de programación.
- Verificación: `python -m pytest tests/test_regressions.py`
- Ficheros: `orchestrators/advanced_orchestrator.py`, `main.py`, `agents/translator_agent.py`
- Costura de test: la del paso 0.1 y `typer.testing.CliRunner` para la CLI
- Bloqueado por: 0.1

#### Paso 0.3: CI de tests y linter; limpieza (Tamaño: S)
- Criterios: workflow que ejecuta `ruff` y `pytest` en cada push; se elimina el orquestador antiguo y los `scripts/test_*.py`; `docs/architecture.md` y `.env.example` reflejan el código.
- Verificación: `ruff check . && python -m pytest`
- Ficheros: `.github/workflows/ci.yml`, `orchestrators/`, `scripts/`, `docs/`, `.env.example`
- Bloqueado por: 0.2

### Fase 1: Núcleo generalizado

Verificada cuando: el blueprint `perspective` produce, con el LLM falso, el mismo outline y la misma secuencia de llamadas que el código actual, y no queda ninguna comparación por nombre de sección en el código.

#### Paso 1.1: Capa única de LLM con backend de Claude Code (Tamaño: L, se divide en 1.1a y 1.1b)
- 1.1a (M): `LLMClient` con interfaz `complete(system, user, schema=None, role=...)`, reintentos, salida estructurada validada con Pydantic y registro de coste por ejecución. Backend `ClaudeCodeBackend`, que lanza `claude -p --output-format json --system-prompt … --tools "" --strict-mcp-config --no-session-persistence` (y `--json-schema` cuando se pide salida estructurada) y lee el campo `result`. Backend `OpenAIBackend` con el comportamiento actual. Se elige con `LLM_BACKEND` (`claude-code` por defecto) y el modelo por rol con `--model`.
- 1.1b (M): todos los agentes, `PlannerAgent` y la llamada directa del orquestador pasan a usar `LLMClient`; desaparece `GPT5_MODELS`; el `FakeLLM` de los tests pasa a ser un backend más.
- Criterios: `generate` completa una ejecución sin `OPENAI_API_KEY` si los índices ya existen (ver la decisión abierta sobre embeddings); un fallo del CLI (no instalado, sin sesión iniciada, límite de uso) produce un error claro y no un paper a medias; las llamadas independientes se pueden lanzar en paralelo con un límite configurable.
- Verificación: `python -m pytest tests/test_llm_client.py` (el CLI se sustituye por un ejecutable falso) y una ejecución real manual de `generate` con el corpus actual
- Ficheros: `llm/client.py`, `llm/backends/claude_code.py`, `llm/backends/openai.py` (nuevos), `agents/*.py`, `processors/extraction_agent.py`, `orchestrators/advanced_orchestrator.py`, `config/settings.py`, `.env.example`
- Costura de test: `LLMClient` con backend falso; `ClaudeCodeBackend` con `subprocess` sustituido
- Bloqueado por: 0.2
- Riesgos conocidos: cada llamada arranca un proceso (unos segundos de sobrecoste; un paper son cientos de llamadas); el consumo cuenta contra los límites de la suscripción de Claude Code; el ejecutable de Windows exigirá tener el CLI instalado y con sesión iniciada. El 2026-11-10 se comprobó que el CLI (2.1.322) acepta esas opciones, pero la llamada de prueba devolvió "Not logged in" dentro del entorno aislado de la sesión de trabajo, así que **falta una prueba real de extremo a extremo**.

#### Paso 1.1c: Embeddings locales (Tamaño: M)
- Criterios: `EmbeddingIndex` y `ReferenceIndex` obtienen los vectores de un `Embedder` configurable (`EMBEDDING_BACKEND=local` por defecto, modelo en `EMBEDDING_MODEL`); el índice guarda con qué modelo se generó y se niega a mezclar vectores de modelos distintos; `ai-writer reindex` regenera los índices del corpus sin volver a extraer los PDFs; desaparecen las dimensiones 1536 escritas a mano.
- Comprobación de calidad antes de dar el cambio por bueno: para una muestra de ideas del corpus usadas como consulta, comparar los 10 vecinos más próximos en el índice antiguo (OpenAI, ya en disco) y en el nuevo. No necesita API key. Si el solapamiento es bajo, se revisa a mano una muestra antes de seguir.
- Verificación: `python -m pytest tests/test_embedder.py` (con un modelo falso) y `ai-writer reindex` real sobre el corpus actual
- Ficheros: `embeddings/embedder.py` (nuevo), `embeddings/embedding_index.py`, `utils/reference_index.py`, `utils/enhanced_context_manager.py`, `config/settings.py`, `main.py`, `pyproject.toml`
- Costura de test: `Embedder` falso inyectado en `EmbeddingIndex`
- Bloqueado por: 0.2
- Riesgos conocidos: las puntuaciones de similitud cambian de escala, así que los umbrales y pesos de `EnhancedContextManager` hay que recalibrarlos; PyTorch engorda mucho el ejecutable de Windows.

#### Paso 1.2: Proyecto como unidad de trabajo (Tamaño: M)
- Criterios: `ai-writer init <dir>` crea la estructura; todas las rutas salen de `project.yaml`; `ai-writer migrate` convierte el `data/` actual en un proyecto sin reprocesar PDFs.
- Verificación: `python -m pytest tests/test_project.py`
- Ficheros: `project/` (nuevo), `config/settings.py`, `main.py`, `processors/batch_processor.py`
- Bloqueado por: 0.2

#### Paso 1.3: Blueprint y SectionSpec (Tamaño: L, se divide en 1.3a y 1.3b)
- 1.3a (M): modelos `DocumentBlueprint` y `SectionSpec`; blueprint `perspective` en YAML con los valores actuales; planner y orquestador leen del blueprint.
- 1.3b (M): `EnhancedContextManager` y `WriterAgent` leen configuración e instrucciones de `SectionSpec`; se eliminan `SECTION_CONFIGS` y `_get_section_instructions`.
- Verificación: `python -m pytest tests/test_blueprint.py tests/test_pipeline_e2e.py`
- Ficheros: `models/blueprint.py` (nuevo), `blueprints/perspective.yaml` (nuevo), `agents/planner_agent.py`, `agents/writer_agent.py`, `utils/enhanced_context_manager.py`, `orchestrators/advanced_orchestrator.py`
- Bloqueado por: 1.1, 1.2

#### Paso 1.4: Idioma como parámetro (Tamaño: S)
- Criterios: los prompts reciben idioma y guía de estilo del proyecto; se puede escribir directamente en inglés sin pasar por el traductor.
- Verificación: `python -m pytest tests/test_language.py`
- Ficheros: `agents/*.py`, `prompts/` (nuevo)
- Bloqueado por: 1.3

#### Paso 1.5: Estado de ejecución, reanudación y puntos de control (Tamaño: M)
- Criterios: cada fase y cada sección guardan checkpoint; `--resume` continúa donde se quedó; el pipeline se detiene tras el outline para que el usuario lo edite, salvo con `--yes`.
- Verificación: `python -m pytest tests/test_resume.py`
- Ficheros: `orchestrators/`, `utils/pipeline_logger.py`, `main.py`
- Bloqueado por: 1.2

### Fase 2: Citas con BibTeX e integridad

Requisito previo del LaTeX y la mejora de calidad más importante del sistema actual.

Verificada cuando: el corpus actual genera un `references.bib` válido, todas las citas del documento son claves de ese fichero, y un documento con una cita inventada hace fallar la validación.

#### Paso 2.1: Biblioteca BibTeX del proyecto (Tamaño: M)
- Criterios: cada paper del corpus y cada referencia extraída tiene una clave estable; si el usuario aporta `library.bib`, manda sobre lo extraído; las entradas sin datos suficientes se listan en un informe.
- Verificación: `python -m pytest tests/test_bibliography.py`
- Ficheros: `bibliography/` (nuevo), `processors/pdf_processor.py`, `utils/reference_index.py`
- Bloqueado por: 1.2

#### Paso 2.2: Evidencia con claves y validador de citas (Tamaño: M)
- Criterios: el contexto que recibe el escritor muestra la clave exacta de cada fuente; el escritor cita con `[@clave]`; el validador rechaza claves que no estaban en la evidencia y pide reescritura; se ejecuta también después del revisor.
- Verificación: `python -m pytest tests/test_citation_integrity.py`
- Ficheros: `utils/enhanced_context_manager.py`, `agents/writer_agent.py`, `agents/reviewer_agent.py`, `validation/citations.py` (nuevo), `utils/reference_processor.py`
- Bloqueado por: 2.1, 1.3

### Fase 3: Plantillas LaTeX

Verificada cuando: el paper de perspectiva actual compila a PDF con una plantilla genérica y con una plantilla real aportada por el usuario, sin editar el `.tex` a mano.

#### Paso 3.1: Renderizador LaTeX con plantilla genérica (Tamaño: M)
- Criterios: `ai-writer render --format latex` produce `main.tex` + `references.bib`; el cuerpo se convierte desde el Markdown restringido con escapado correcto; se compila con `latexmk` si está instalado y, si no, se entrega un zip listo para Overleaf.
- Verificación: `python -m pytest tests/test_latex_render.py` (la compilación real se marca como test opcional)
- Ficheros: `renderers/latex.py` (nuevo), `renderers/templates/generic/`, `main.py`, `pyproject.toml`
- Costura de test: `render(document, template_profile) → ficheros`
- Bloqueado por: 2.2

#### Paso 3.2: Perfil de plantilla (Tamaño: M)
- Criterios: `template.yaml` declara fichero principal, huecos (título, autores, afiliaciones, resumen, palabras clave, cuerpo, agradecimientos, bibliografía), paquete de citas (natbib, biblatex o numérico), estilo bibliográfico, secciones obligatorias y límites; el renderizador respeta el perfil.
- Verificación: `python -m pytest tests/test_template_profile.py`
- Ficheros: `renderers/template_profile.py` (nuevo), `renderers/latex.py`
- Bloqueado por: 3.1

#### Paso 3.3: Importar una plantilla del usuario (Tamaño: M)
- Criterios: `ai-writer template add <carpeta>` analiza el `.tex` de ejemplo de la plantilla, propone `template.yaml` y un `main.tex` con huecos, compila un documento de prueba y muestra el resultado para que el usuario lo confirme.
- Verificación: `python -m pytest tests/test_template_import.py` con dos plantillas reales en `tests/fixtures/templates/`
- Ficheros: `renderers/template_import.py` (nuevo), `main.py`
- Bloqueado por: 3.2

#### Paso 3.4: Figuras, tablas y ecuaciones (Tamaño: M)
- Criterios: el modelo de documento admite figuras y tablas con etiqueta y pie; las referencias cruzadas se resuelven; las tablas salen de CSV con formato `booktabs`.
- Verificación: `python -m pytest tests/test_floats.py`
- Ficheros: `models/paper.py`, `renderers/latex.py`, `writers/markdown_writer.py`
- Bloqueado por: 3.1

#### Paso 3.5: Bucle de compilación y cumplimiento (Tamaño: S)
- Criterios: los errores de `latexmk` se leen del log y se corrigen los mecánicos (escapado, paquetes, referencias sin definir); se comprueba el límite de páginas del perfil y se informa de qué sección sobra.
- Verificación: `python -m pytest tests/test_latex_compile.py`
- Ficheros: `renderers/compile.py` (nuevo)
- Bloqueado por: 3.2

### Fase 4: Paper a partir de resultados y código

Verificada cuando: con una carpeta de análisis de ejemplo, el sistema escribe un paper IMRaD en el que cada cifra de Resultados coincide con un valor de los ficheros de resultados y cada figura citada existe.

#### Paso 4.1: Inventario del análisis (Tamaño: M)
- Criterios: `ai-writer analysis ingest` recorre `sources/analysis/` y crea un manifiesto: tablas (CSV, XLSX, JSON), figuras, notebooks, scripts, ficheros de entorno; **no ejecuta código**; excluye secretos (`.env`, claves) y permite un `.aiwriterignore`.
- Verificación: `python -m pytest tests/test_analysis_manifest.py`
- Ficheros: `analysis/manifest.py` (nuevo), `main.py`
- Bloqueado por: 1.2

#### Paso 4.2: Hallazgos a partir de resultados (Tamaño: M)
- Criterios: los estadísticos de cada tabla se calculan con pandas, no con el LLM; cada figura recibe una descripción con un modelo de visión (con el backend de Claude Code, dándole acceso de solo lectura a la carpeta de figuras); cada hallazgo guarda el fichero, la celda o columna de origen y el valor exacto; los hallazgos se indexan como fuente de evidencia.
- Verificación: `python -m pytest tests/test_findings.py`
- Ficheros: `analysis/findings.py` (nuevo), `evidence/findings_source.py` (nuevo)
- Bloqueado por: 4.1, 1.3

#### Paso 4.3: Hechos de métodos a partir del código (Tamaño: M)
- Criterios: se extraen datos de entrada, preprocesado, modelos, hiperparámetros, tests estadísticos, semillas y versiones de software, cada uno con fichero y línea; se enlaza cada resultado con el script que lo genera cuando se puede deducir; se indexan como fuente de evidencia.
- Verificación: `python -m pytest tests/test_methods_facts.py`
- Ficheros: `analysis/code_facts.py` (nuevo), `evidence/methods_source.py` (nuevo)
- Bloqueado por: 4.1, 1.3

#### Paso 4.4: Blueprint `research_paper` y lista de contribuciones (Tamaño: M)
- Criterios: blueprint IMRaD en el que Métodos bebe del código, Resultados de los hallazgos y Discusión de hallazgos más literatura; antes del outline el sistema propone la lista de contribuciones y mensajes principales y **el usuario la confirma**; el resumen se escribe al final.
- Verificación: `python -m pytest tests/test_research_paper_e2e.py`
- Ficheros: `blueprints/research_paper.yaml` (nuevo), `agents/planner_agent.py`, `orchestrators/`
- Bloqueado por: 4.2, 4.3

#### Paso 4.5: Verificador numérico y de figuras (Tamaño: S)
- Criterios: toda cifra de Resultados y Discusión se contrasta con los hallazgos (con tolerancia de redondeo); toda figura o tabla referenciada existe; lo que no cuadra bloquea y se lista.
- Verificación: `python -m pytest tests/test_numeric_integrity.py`
- Ficheros: `validation/numbers.py` (nuevo)
- Bloqueado por: 4.4, 3.4

### Fase 5: Convocatorias

Verificada cuando: con las bases de una convocatoria real, el sistema produce una memoria con todas las secciones exigidas, dentro de los límites, y un informe de cumplimiento y de huecos.

#### Paso 5.1: Extracción de las bases a `CallSpec` (Tamaño: M)
- Criterios: de los documentos de la convocatoria (PDF, DOCX, HTML) se extrae: entidad, programa, plazos, elegibilidad, secciones exigidas con límites, criterios de evaluación con pesos, elementos obligatorios, reglas de formato e idioma; cada dato guarda la página de la que sale; **el usuario valida el `CallSpec` antes de seguir**.
- Verificación: `python -m pytest tests/test_call_spec.py` con una convocatoria real en `tests/fixtures/calls/`
- Ficheros: `grants/call_spec.py` (nuevo), `grants/extractor.py` (nuevo), `readers/`
- Bloqueado por: 1.1, 1.2

#### Paso 5.2: Brief del proyecto y detección de huecos (Tamaño: M)
- Criterios: `brief.md` con apartados fijos (idea, objetivos, equipo, resultados previos, recursos, presupuesto, socios); el sistema compara el brief con lo que exige el `CallSpec` y lista lo que falta **antes** de escribir; nunca se inventan personas, cifras, socios ni cartas de apoyo.
- Verificación: `python -m pytest tests/test_brief_gaps.py`
- Ficheros: `grants/brief.py` (nuevo), `evidence/brief_source.py` (nuevo)
- Bloqueado por: 5.1, 1.3

#### Paso 5.3: Blueprint generado desde el `CallSpec` (Tamaño: M)
- Criterios: cada sección exigida se convierte en un `SectionSpec` con su límite, las fuentes de las que bebe y los criterios de evaluación que debe atender; el planner reparte la extensión según el peso de los criterios.
- Verificación: `python -m pytest tests/test_grant_blueprint.py`
- Ficheros: `grants/blueprint_builder.py` (nuevo), `agents/planner_agent.py`
- Bloqueado por: 5.1, 1.3

#### Paso 5.4: Elementos estructurados (Tamaño: L, se divide)
- 5.4a (M): objetivos, paquetes de trabajo, tareas, entregables e hitos como modelo de datos coherente (cada tarea pertenece a un paquete, cada entregable a una tarea, fechas dentro de la duración).
- 5.4b (M): tablas, cronograma y tabla de riesgos generados desde ese modelo; presupuesto calculado con aritmética determinista a partir de las cifras del brief.
- Verificación: `python -m pytest tests/test_workplan.py`
- Ficheros: `grants/workplan.py` (nuevo), `renderers/latex.py`
- Bloqueado por: 5.3, 3.4

#### Paso 5.5: Evaluador simulado y cumplimiento (Tamaño: M)
- Criterios: un agente puntúa la memoria criterio a criterio con la rúbrica de las bases y devuelve debilidades concretas, que alimentan una ronda de revisión; el comprobador de cumplimiento verifica secciones obligatorias, límites y formato.
- Verificación: `python -m pytest tests/test_grant_review.py`
- Ficheros: `agents/reviewer_agent.py`, `grants/compliance.py` (nuevo)
- Bloqueado por: 5.3

#### Paso 5.6: Salida en el formato de la convocatoria (Tamaño: M)
- Criterios: salida con la plantilla LaTeX de la convocatoria o en DOCX con el documento de referencia que aporte el usuario.
- Verificación: `python -m pytest tests/test_grant_render.py`
- Ficheros: `renderers/docx.py` (nuevo), `renderers/latex.py`
- Bloqueado por: 5.4, 3.3

### Fase 6: Calidad de la escritura (transversal, después de la Fase 2)

Verificada cuando: una ejecución produce un informe con las métricas de abajo y se pueden comparar dos ejecuciones.

#### Paso 6.1: Revisión en dos tiempos (Tamaño: M)
- Criterios: el revisor devuelve primero una lista estructurada de problemas y después se aplican correcciones dirigidas, en lugar de reescribir la sección a ciegas; tras cada corrección se ejecutan los validadores.
- Verificación: `python -m pytest tests/test_review_loop.py`
- Ficheros: `agents/reviewer_agent.py`, `orchestrators/`
- Bloqueado por: 2.2

#### Paso 6.2: Pasadas globales (Tamaño: M)
- Criterios: detección de redundancia entre secciones, consistencia terminológica con el glosario, y resumen y título generados al final a partir del cuerpo.
- Verificación: `python -m pytest tests/test_global_passes.py`
- Ficheros: `agents/`, `orchestrators/`
- Bloqueado por: 6.1

#### Paso 6.3: Informe de ejecución (Tamaño: S)
- Criterios: por ejecución se guarda: citas resueltas frente a totales, afirmaciones sin respaldo, cobertura del corpus, cumplimiento de extensión, coste y tiempo; `ai-writer runs compare` enfrenta dos ejecuciones.
- Verificación: `python -m pytest tests/test_run_report.py`
- Ficheros: `analytics/run_report.py` (nuevo), `main.py`
- Bloqueado por: 1.5, 2.2

#### Paso 6.4: Mejor extracción de PDFs (Tamaño: M, opcional)
- Criterios: extracción con estructura (secciones, tablas, bibliografía) en lugar de texto plano; el corpus se puede reprocesar por paper.
- Verificación: `python -m pytest tests/test_pdf_extraction.py`
- Ficheros: `readers/pdf_reader.py`, `processors/`
- Bloqueado por: 1.2

### Orden y paralelismo

```
F0 → F1 → F2 → F3 → F4 → F5
              F2 → F6 (en paralelo con F3–F5)
```

F4 y F5 son técnicamente independientes entre sí. Por decisión del usuario, F4 (paper con resultados) va antes que F5 (convocatorias).

## 5. Registro de decisiones

| Decisión | Opción elegida | Por qué |
|---|---|---|
| Cómo generalizar | Blueprint declarativo + fuentes de evidencia, un solo orquestador | Tres orquestadores (paper, resultados, convocatoria) triplicarían el código y los fallos |
| Qué escribe el LLM | Markdown restringido, no LaTeX | El contenido queda independiente de la plantilla; el escapado y la compilación son deterministas |
| Cifras de resultados | Calculadas con pandas y verificadas después | Un LLM que lee una tabla puede cambiar un número; en un paper eso es inadmisible |
| Código del usuario | Solo se lee, nunca se ejecuta | Seguridad y reproducibilidad: el sistema describe el análisis, no lo rehace |
| Hechos que faltan | Marcador `[[PENDIENTE]]` + informe de huecos | En una convocatoria, un socio o una cifra inventados son peores que un hueco |
| Orden de fases | Citas (F2) antes que LaTeX (F3) | LaTeX necesita BibTeX y claves estables |
| Privacidad (2026-11-10) | Resultados y código sin publicar se pueden enviar a la API del proveedor de LLM | Respuesta del usuario; no hace falta modelo local |
| Primera plantilla LaTeX (2026-11-10) | Plantilla de arXiv | Respuesta del usuario; es el caso de prueba de los pasos 3.1 a 3.3 |
| Forma de los análisis (2026-11-10) | Python | Respuesta del usuario; R queda fuera del alcance inicial de la Fase 4 |
| Prioridad F4 / F5 (2026-11-10) | Paper con resultados (F4) antes que convocatorias (F5) | Respuesta del usuario |
| Embeddings (2026-11-10) | Modelo local multilingüe con `sentence-transformers`; el modelo es configurable (pequeño por defecto, `BAAI/bge-m3` en la máquina del usuario) | Respuesta del usuario: elimina la API key de OpenAI. Multilingüe porque hoy las consultas van en español y el corpus en inglés |
| Markdown a LaTeX (2026-11-10) | pandoc mediante `pypandoc-binary` | Aceptada la recomendación: resuelve escapado, tablas, matemáticas y DOCX |
| Bibliografía (2026-11-10) | Manda el `.bib` de Zotero cuando exista; lo extraído de los PDFs es el respaldo | Aceptada la recomendación |
| Proveedor de LLM (2026-11-10, revisada el mismo día) | Capa única con el **CLI de Claude Code** (`claude -p`) como backend por defecto; OpenAI queda como backend alternativo | Petición del usuario: no depender de la API key de OpenAI para generar texto. Sustituye a "OpenAI por defecto" |
| Idioma (2026-11-10) | Escribir en el idioma de destino (inglés por defecto en papers); traductor aparte | Aceptada la recomendación |
| Puntos de control (2026-11-10) | Parada para confirmar outline, contribuciones y `CallSpec`; `--yes` los salta | Aceptada la recomendación |
| Ejecutable de Windows (2026-11-10) | Genera el proyecto `.tex`; compila solo si hay LaTeX instalado | Aceptada la recomendación |

## 6. Decisiones abiertas (necesito tu respuesta antes de implementar)

Cada una lleva mi recomendación. "Sí" acepta la recomendación.

Las decisiones 1 a 6 y la de embeddings quedaron resueltas el 2026-11-10 y están en el registro de decisiones. Quedan dos, que no bloquean hasta fases posteriores:

7. **Primera convocatoria real**: ¿cuál? Define el caso de prueba de la Fase 5 y si hace falta DOCX. Propongo la próxima que vayas a solicitar. No bloquea nada hasta la Fase 5.
8. **Formato de los resultados** (derivada de "Python"): ¿scripts `.py`, notebooks o ambos? ¿Resultados en CSV y figuras en PNG/PDF dentro de una carpeta? Propongo admitir ambos y esos formatos. No bloquea nada hasta la Fase 4.

Resueltas el 2026-11-10 (ver registro de decisiones): privacidad, primera plantilla (arXiv), lenguaje de los análisis (Python) y prioridad (F4 antes que F5).

## 7. Supuestos (corrígeme si alguno es falso)

1. El paper de perspectiva actual debe seguir funcionando igual durante toda la migración.
2. El corpus ya procesado (43 papers) se migra al nuevo formato de proyecto sin volver a pagar la extracción.
3. La herramienta sigue siendo una CLI de un solo usuario; no hay interfaz web ni multiusuario.
4. El usuario revisa y firma el documento final: el sistema produce un borrador avanzado, no un envío automático.
5. LaTeX está instalado en tu máquina de trabajo (lo está: `pdflatex`, `xelatex`, `latexmk`, `biber`). `pandoc` no lo está y entraría como dependencia de Python.

## 8. Sin especificar todavía

- Fase 5: formatos de entrada de las bases. ¿Solo PDF, o también formularios web y plantillas DOCX que haya que rellenar en su sitio? Depende de la decisión 9.
- Fase 5: generación del cronograma como figura (paquete LaTeX frente a imagen). Se decide al llegar al paso 5.4b.
- Fase 4: análisis con resultados muy grandes (miles de ficheros). Hace falta ver un caso real para decidir cómo se resume el inventario.
- Paso 6.4: herramienta de extracción de PDFs. Requiere una prueba comparativa sobre tu corpus; hasta entonces es niebla.

## 9. Siempre / Nunca

- Siempre: cada afirmación, cifra y cita con procedencia comprobable; cada paso con su test; el blueprint `perspective` en verde.
- Nunca: ejecutar código del usuario; inventar personas, socios, presupuestos o resultados; enviar solicitudes o papers a ningún sitio; cambiar los algoritmos de clustering y exploración RAG como parte de este plan.

## 10. Progreso

| Fase | Estado |
|---|---|
| 0. Estabilizar | hecha el 2026-11-10, sin commitear; ver notas de ejecución |
| 1. Núcleo generalizado | paso 1.1 (a, b, c) hecho el 2026-11-11, sin commitear; pasos 1.2 a 1.5 pendientes |
| 2. Citas con BibTeX | pendiente |
| 3. Plantillas LaTeX | pendiente |
| 4. Resultados y código | pendiente |
| 5. Convocatorias | pendiente |
| 6. Calidad | pendiente |

## 11. Notas de ejecución

### Fase 0 (2026-11-10)

Verificación: `ruff check . --select F` sin errores y `python -m pytest` con 34 tests en verde (24 anteriores + 10 nuevos). `ai-writer stats` comprobado contra el corpus real. **No se ha ejecutado `generate` contra la API real**: el flujo completo solo está probado con el LLM falso.

Desviaciones respecto al plan:

- Aparecieron dos fallos más de los seis listados. `PipelineLogger.log_data` no existía, así que `generate` fallaba en el refinamiento del outline con el logging activo (que es el valor por defecto). Y `process` llamaba a `BatchProcessor` con argumentos que su constructor no acepta. Ambos corregidos.
- La revisión global del paper se ejecuta ahora **antes** de resolver las citas, no después. Con el orden anterior el revisor recibía la bibliografía ya generada y podía reescribirla o perderla.
- `run()` solo tolera errores de la API (`OpenAIError`) en la revisión global y en la revisión crítica. Cualquier otro error se propaga.
- `--output` ahora se respeta también para el paper; antes solo se aplicaba a la revisión crítica.
- El corpus sintético se genera en `tests/conftest.py`, no en ficheros bajo `tests/fixtures/`.
- CI ejecuta solo las reglas `F` de ruff (errores reales). Las de estilo dan unos 1.500 avisos, casi todos espacios en blanco; arreglarlos es un cambio masivo que conviene hacer en un commit aparte.
- No se ha tocado el número de versión: `pyproject.toml` y `main.py` dicen 1.0.0 y `docs/architecture.md` dice 1.1.0.

### Paso 1.1 (2026-11-11)

Hecho: `ai_writer.llm` (`LLMClient`, backends `claude-code` y `openai`), `ai_writer.embeddings.embedder` (backends `local` y `openai`), todos los agentes y el orquestador migrados, comando `ai-writer reindex`, y el índice guarda y comprueba el modelo de embeddings.

Verificación: `ruff check . --select F` sin errores y `python -m pytest` en verde. Los tests sustituyen el CLI por un `subprocess.run` falso y el modelo de embeddings por uno falso, y fallan si algo construye un cliente de OpenAI.

**Pendiente de verificar por el usuario**: una ejecución real de `generate`. El CLI de Claude Code no tiene sesión iniciada dentro del entorno de trabajo del agente ("Not logged in"), así que el backend `claude-code` solo está probado contra un CLI simulado. Lo comprobado contra el CLI real (2.1.322) es que acepta todas las opciones que se le pasan.

Desviaciones respecto al plan:

- No se usa `--json-schema`. No se pudo comprobar en qué campo devuelve el CLI la salida estructurada, así que el modo JSON añade una instrucción al prompt de sistema y `LLMClient.complete_json` extrae y valida el JSON (con Pydantic si se le pasa un modelo).
- No se ha implementado el lanzamiento de llamadas en paralelo. El pipeline actual es secuencial (cada párrafo depende de los anteriores) y no había dónde usarlo; se añadirá en el paso que lo necesite (extracción de PDFs, Fase 4).
- Modelos por defecto con `claude-code`: `sonnet` para escribir y revisar, `opus` para planificar el outline, `haiku` para los resúmenes de sección. Antes todo usaba `gpt-5.2`. El planificador ya no recurre a `gpt-4o` como alternativa.
- Un error permanente del LLM (CLI sin instalar o sin sesión) detiene el planificador en lugar de producir un outline básico de relleno.
- `max_tokens` y `temperature` no tienen equivalente en el CLI y se ignoran con ese backend.
- Se eliminaron `utils/reference_index.py`, `utils/reference_context_manager.py` y `utils/reference_parser.py`: solo los usaba el orquestador antiguo, borrado en la Fase 0.
- `scripts/process_powerpoint.py` sigue llamando a OpenAI directamente (usa visión). Queda fuera de este paso.
- El `Embedder` distingue consulta y pasaje, porque los modelos E5 necesitan prefijos distintos para cada uno.

#### Reindexado y comprobación de calidad (2026-11-11)

El corpus real está reindexado con `intfloat/multilingual-e5-small` (384 dimensiones): 3.733 ideas, 3.839 claims y 2.713 referencias. Los vectores de OpenAI están en `data/processed/embeddings/previous_text-embedding-3-small/`.

Comparación con el índice de OpenAI, usando 400 ideas del corpus como consulta:

| Medida | Valor |
|---|---|
| Solapamiento medio de los 10 vecinos más próximos | 65 % |
| Consultas con al menos 5 de 10 vecinos en común | 90 % |
| El mejor vecino del índice antiguo aparece entre los 10 del nuevo | 97 % |
| Tiempo para embeber las 3.733 ideas (12 núcleos, sin GPU) | 119 s |

Comprobado además sobre el índice nuevo: una consulta en español recupera ideas pertinentes del corpus en inglés, `get_context_for_idea` devuelve contexto y `ClusterAnalyzer` genera los 25 clusters.

Pendiente:

- **Recalibrar `min_score=0.3`** en `EnhancedContextManager` (búsqueda de ideas y de claims). Con E5 las similitudes están comprimidas en torno a 0,75–0,9, así que ese umbral ya no descarta nada. El orden de los resultados no cambia; lo que se pierde es el filtro cuando el corpus no tiene nada pertinente.

Comparación con `BAAI/bge-m3` (1.024 dimensiones), misma muestra: solapamiento medio 68 %, consultas con al menos 5 de 10 vecinos en común 92 %, mejor vecino antiguo entre los 10 nuevos 98 %. Tardó 1.282 s en embeber las 3.733 ideas, aunque compartió CPU con el reindexado, así que el tiempo real en solitario es menor. La mejora sobre el modelo pequeño es de 1 a 3 puntos, a cambio de un coste varias veces mayor: se mantiene `multilingual-e5-small` como valor por defecto.

#### Prueba real con Claude Code (2026-11-11)

Tras iniciar sesión en el CLI, el backend `claude-code` funciona de verdad: llamadas de texto y JSON validado (unos 4 s por llamada corta con `haiku`), y fases 1 y 2 completas (clusters y outline de 8 secciones y 28 párrafos con `opus`, unos 4,5 minutos, 31.600 tokens de salida). El `abstract` se tomó del paper generado anteriormente, porque `data/references/` (PDFs y `ABSTRACT.md`) no existe en el disco; ya faltaba antes de empezar este trabajo.

Fallo encontrado y corregido: el prompt de refinamiento del outline no indicaba las claves del JSON, y el modelo devolvía `title` y `description` en lugar de `section_name` y `section_purpose`, así que el refinamiento se descartaba siempre. Ahora ambos prompts comparten `OUTLINE_JSON_FORMAT`. Verificado contra el CLI real: el refinamiento se aplica (8 secciones, 35 párrafos).

Observación para el paso 1.3: el refinamiento renombró una sección a "Implicaciones Futuras: Hoja de Ruta". Como `SECTION_CONFIGS` se busca por nombre exacto, esa sección cae en la configuración de "Introducción" sin avisar. Es el problema que resuelve el blueprint.

Sin probar todavía: `generate` completo (fase 3, escritura y revisión).
