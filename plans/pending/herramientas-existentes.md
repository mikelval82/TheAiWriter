# Herramientas existentes: ¿qué de TheAIWriter ya está hecho?

Revisión de escritorio del 2026-11-14/15. Tres agentes leyeron repositorios y documentación con `gh`; **nada se instaló ni se ejecutó**, así que todo lo relativo a instalación y calidad sale de documentación y código, no de pruebas.

Contexto: los experimentos de `mejoras-pipeline.md` dejaron dos piezas con valor medido: (a) búsqueda semántica sobre los papers expuesta a Claude como herramientas (buscar pasajes y leer el pasaje completo) y (b) verificación de citas (la obra existe, la frase literal está en el PDF, la frase del documento coincide con lo que dice el paper).

## (a) Búsqueda sobre Zotero

| Herramienta | Pasajes con página | Leer alrededor | PDF locales | Sin clave de pago | Instalación | Zotero | Mantenimiento |
|---|---|---|---|---|---|---|---|
| `54yyyu/zotero-mcp` (PyPI `zotero-mcp-server`) | Sí, activando el troceado y subiendo `max_chunks_per_item` | Por rango de páginas | Sí (`ZOTERO_LOCAL=true`, lee `zotero.sqlite` y `storage/`, también enlazados) | Sí (MiniLM local por defecto) | Python + ChromaDB; incidencias en Windows | 7+ | MIT, ~5.900 estrellas, 30 colaboradores, cambios diarios |
| ZotSeek (`introfini/ZotSeek`, plugin de Zotero) | Sí, híbrida, página exacta | No hay herramienta | Sí | Sí (nomic-embed local, incluido) | Instalar un .xpi; sin Python | **8+** | ~240 estrellas, casi un solo autor, licencia poco clara |
| `qiobn/zotero-research-assistant` | Sí, híbrida + reranker | Sección completa y trozos vecinos | Sí | Sí (bge-m3 local) | `pip install` | no indicado | MIT, 1 autor, 6 meses |
| DeepZotero (`ccam80/deep-zotero`) | Sí, por secciones | Trozos vecinos | Sí, pero ignora archivos enlazados | Modelo local flojo; el bueno envía texto a Google | Variables de entorno + indexado | **8** | MIT, 1 autor, 9 estrellas |
| Zoteus (`oscardvs/zoteus`) | Débil: por item, texto completo opcional y recortado | Páginas exactas | Sí | 700 MB a mano u Ollama | `npx`, la más ligera | 7+ | MIT, 1 autor principal, versiones cada pocos días |
| `cookjohn/zotero-mcp` (plugin) | Trozos de ~450 caracteres, sin página | Lectura de texto completo | Sí | Solo con Ollama | .xpi + Ollama | 7+ | MIT, ~1.280 estrellas, 18 colaboradores; incluye herramientas de escritura |
| `zotero-library-mcp` (el instalado ahora) | No: palabras clave, sin fragmento | No | **No**, solo nube | — | ya instalado | — | 1 autor, sin licencia |

Descartados: fork con Postgres (abandonado), `paperqa-mcp-server` (sintetiza en vez de devolver pasajes y necesita OpenAI).

## (b) Verificación de citas

| Herramienta | Obra existe | Cita literal en el PDF | La frase coincide con el paper | Notas |
|---|---|---|---|---|
| `hearthresearch/citefact` | Sí | Sí, con diferencias palabra a palabra | Sí, con un modelo (apoyada / parcial / tergiversada / no está) | Lee una colección de Zotero por la API local; Markdown y citas autor-año solamente; Docling de 1–2 GB; 1 autor, 3 meses |
| Zoteus `zotero_check_citations` | Sí | Sí | No | Parte de un servidor de 47 herramientas |
| TheAIWriter (`validation.py`, `quotes.py`, `support.py`) | Sí | Sí | Sí | Claves pandoc `[@clave]`; juez medido con ruido |

## Conclusión provisional

- Casi todo lo que TheAIWriter hace con valor medido existe ya en proyectos de terceros, incluida la verificación.
- Ninguno lo cubre todo solo, y los que mejor encajan en diseño son proyectos de una persona.
- Lo que no existe fuera: el índice de ideas (sin demostrar que supere a un buen troceado) y el flujo guiado del curso.

## Siguiente paso propuesto

Prueba real con los mismos 12 papers, el mismo resumen y el mismo juez: Claude escribiendo con `54yyyu/zotero-mcp` (y, si hay Zotero 8, con ZotSeek), y `citefact` sobre el borrador. Requiere instalar software de terceros y tener Zotero abierto con los 12 PDF en una colección.
