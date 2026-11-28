# TheAIWriter

TheAIWriter es un plugin de Claude Code para escribir documentos científicos con los PDF de tu
Zotero. Claude planifica y escribe; el plugin le permite buscar y leer pasajes de los artículos y
verifica las citas del borrador.

**Empieza por el [manual](docs/manual.md)**: diagrama, uso paso a paso y archivos de entrada y salida.

## Requisitos

- Claude Code, en la aplicación de escritorio o en la terminal, con tu propia cuenta.
- Zotero instalado en el mismo ordenador, con los PDF adjuntos a las obras.
- `uv` instalado y disponible en el sistema.

Zotero no necesita estar abierto. El plugin solo lee sus datos: no escribe en Zotero.

## Instalación

En Claude Code:

```text
/plugin marketplace add mikelval82/TheAiWriter
/plugin install theaiwriter@theaiwriter
```

La primera vez que se indexan o buscan pasajes se descarga el modelo de búsqueda, que ocupa unos
cientos de MB. Después se calcula la búsqueda en el ordenador.

## Uso

Abre Claude Code en la carpeta donde vas a escribir el documento.

El camino tiene cinco pasos: **nuevo → escribir → comprobar → revisar → exportar**.

1. `/theaiwriter:nuevo`: elige tipo, título, idioma y colecciones de Zotero. Una colección incluye
   sus subcolecciones; sin elegir ninguna se usa todo Zotero. Crea `proyecto.yaml`, `materiales/`,
   `borrador/`, `informes/` y `exportacion/`, y prepara el índice de pasajes. Hay tres tipos:
   perspectiva, resultados y convocatoria. `materiales/abstract.md` trae preguntas según el tipo;
   completa las respuestas antes de escribir. Resultados añade `resultados/` (CSV y figuras) y
   `analisis/` (código); convocatoria añade `convocatoria/` (PDF oficiales) y `materiales/equipo.md`.
2. `/theaiwriter:escribir`: Claude lee `guia_escritura`, explora los artículos, deja el plan en
   `borrador/plan.md` y escribe `borrador/documento.md`, consultando pasajes por sección. En
   proyectos de Resultados o con «con pausa» espera tu aprobación del plan. Registra las lecturas en `informes/consultas.json`.
   Al terminar comprueba el borrador y resume lo señalado; las correcciones se proponen aparte.
3. `/theaiwriter:comprobar`: comprueba el borrador, actualiza `borrador/referencias.bib` y escribe
   `informes/comprobacion.md` y `.json`. El juez corre en segundo plano; con «sin juez» solo hace
   las comprobaciones sin modelo. Con «evidencia» puedes consultar el pasaje de una cita, incluidas las apoyadas. Los cambios del borrador o de los PDF pueden dejar el informe desactualizado.
4. `/theaiwriter:revisar`: evalúa por criterios con una llamada a Claude en segundo plano y deja
   prioridades, fortalezas, carencias y trabajo concreto en `informes/revision.md` y `.json`.
   No cambia el borrador ni da una nota. Conviene comprobar antes: usa el apoyo previo de las citas.
5. `/theaiwriter:exportar` genera `exportacion/documento.docx` con Pandoc y bibliografía. Consulta la [guía de exportación](docs/exportar.md) para elegir un estilo o usar citas vivas de Zotero.

Cuatro ayudas acompañan el camino:

- `/theaiwriter:estado` usa `estado_documento` para ver materiales que faltan o siguen como plantilla,
  palabras del borrador, comprobación, revisión y siguiente paso; también resume el índice.
- `/theaiwriter:corregir` propone una lista numerada con apartado, antes y después. Aplica solo lo
  que aceptes, vuelve a comprobar sin juez y sugiere pasar el juez por las frases cambiadas.
- `/theaiwriter:diagnostico` comprueba la instalación y resume la biblioteca. Puedes pedir «obras
  sin PDF» o «actualiza el índice». Las obras y colecciones se gestionan en Zotero.
- `/theaiwriter:ayuda` explica los comandos y qué toca ahora; con una duda («cómo paso a Word»)
  contesta a partir del manual. No escribe nada ni lanza comprobaciones.

Los comandos resumen el resultado e indican el siguiente paso, su motivo y las alternativas disponibles. Antes de escribir, comprobar con juez o revisar, avisan del gasto con tu cuenta de Claude.
Cuando el juez o el revisor terminan, se detienen por límite de uso o fallan, dejan un aviso en
`informes/avisos.json`: el hook lo recoge en tu siguiente mensaje y Claude te lo menciona al principio.
Al abrir un documento antiguo se migra `revision/` a `informes/` si esta última no existe,
y se renombran sus informes `verificacion.*` a `comprobacion.*`, con un aviso una sola vez.

Las citas del borrador usan claves como `[@smith2020empathy]`. Si falta una fuente, Claude debe
marcarla con `[@?]`.

En documentos de tipo `resultados`, `/theaiwriter:hallazgos` inventaría los archivos y permite aprobar hallazgos con su evidencia antes de escribir. Admite celdas CSV, salidas de texto y salidas guardadas de cuadernos Jupyter. El informe de comprobación coteja las frases vinculadas con los enunciados aprobados y muestra la ubicación de cada fuente. Claude lee los materiales antes de planificar y usa
Introducción, Métodos, Resultados, Discusión y Conclusión, en el idioma del documento. Las cifras
propias no llevan cita: salen de tablas de `resultados/` o de scripts guardados en `analisis/`
que escriben allí sus salidas CSV o Markdown, incluidos los recuentos y diferencias citados.

En documentos de tipo `convocatoria`, pon los PDF oficiales (convocatoria, instrucciones y
plantilla) en `convocatoria/` y completa `materiales/equipo.md`: personas y su papel, resultados
previos, recursos, presupuesto y duración previstos. Claude redacta `convocatoria/ficha.yaml`
desde los PDF y la comprueba con `comprobar_ficha`. Cada requisito lleva fichero, página y una
cita literal de al menos seis palabras. Claude te enseña el texto legible con `mostrar_ficha` y
pregunta «¿Confirmas la ficha? (sí/no)».
Solo tras el sí llama a `confirmar_ficha`, que vuelve a comprobar las citas y conserva el formato
del YAML. No muestra el YAML salvo que lo pidas. Debes confirmar antes de escribir el borrador.
El plan reparte palabras entre apartados y relaciona los criterios con las secciones.
El borrador sigue los títulos, niveles y orden oficiales; lo que falte del equipo se marca
`[PENDIENTE: …]`, sin inventar datos ni prometer resultados.

Las tres guías están en `src/ai_writer/guias/`, incluidas en el paquete instalado. El comando
de escritura conserva la preparación, las búsquedas, las citas y la verificación comunes.

El revisor usa los criterios de la ficha confirmada de la convocatoria. Para dirigir un artículo
a una revista, deja sus normas de autores o guía de revisores en PDF en `revista/`: Claude redacta
`revista/ficha.yaml`, comprueba las citas literales de sus criterios y pide tu confirmación.
Sin revista, usa criterios genéricos de perspectiva o resultados incluidos en el paquete.
La evaluación es automática y orientativa; no sustituye a la de la convocatoria o revista.

## Qué comprueba la verificación

1. Que la clave de cada cita existe en Zotero y pertenece a las colecciones del documento. También
   señala citas mal formadas, fuentes pendientes y obras sin PDF indexado. Tras editar el borrador,
   un hook bloquea las citas desconocidas, mal formadas o ajenas a sus colecciones.
   Si hay colecciones seleccionadas, muestra cuántas obras contienen (`citas.en_coleccion`) y
   cuáles quedan sin citar (`citas.sin_citar`), para revisar si alguna aporta algo que falta;
   no hace falta citarlas todas.
2. Que una cita literal entre «» aparece palabra por palabra en el PDF de alguna de las obras
   citadas en esa frase. Se comprueban las citas de seis palabras o más; también se reconocen
   comillas inglesas y rectas. Se normalizan diferencias de extracción del PDF, como guiones de
   final de línea, y se permiten omisiones marcadas con puntos suspensivos. Una palabra cambiada
   hace que la cita deje de ser literal. Una traducción no cuenta como cita literal del original.
3. Que cada frase citada dice lo que dice la obra. Un juez compara la frase con pasajes de la obra
   citada, incluidos los consultados al escribir, y la clasifica como **apoyada**, **parcial**,
   **tergiversada** o **no apoyada**. Si no puede comprobarla, queda **sin juzgar**. Recibe el
   párrafo para saber a qué se refiere la frase. Si el borrador cambia, la siguiente comprobación
   descarta las frases que ya no están y deja sin juzgar las nuevas.
4. En documentos de tipo `resultados`, que los decimales y porcentajes propios tienen origen en
   los CSV o Markdown de `resultados/`, incluidos sus subdirectorios. Acepta redondeo y porcentajes
   expresados como fracciones en las tablas. Excluye Introducción, Métodos, frases con cita,
   código y destinos de enlaces e imágenes; no comprueba enteros sin porcentaje. Confirma que
   la cifra existe en los resultados, no que la frase la describa bien.
5. En documentos de tipo `convocatoria`, que las citas de la ficha están en sus PDF oficiales
   y que el borrador cumple sus apartados, orden, extensión estimada y límites de caracteres.
   Una cita en otra página, fuera del margen de ±1, produce un aviso. El informe muestra si la
   ficha está confirmada, los apartados condicionales ausentes, los campos que hay que comprobar
   a mano y las marcas pendientes. La extensión es una estimación por palabras: hay que comprobar
   las páginas reales en la plantilla oficial.
6. Que las frases que hablan de una obra llevan su cita. Se buscan por sus palabras (apellidos de
   autores, «el trabajo original», «los autores»…), así que puede haber avisos de más y faltar alguna.

Solo la comprobación de apoyo, la tercera, usa un modelo.
Por defecto, el juez hace una llamada a Claude por párrafo con citas que tenga pasajes para
comparar, en segundo plano y con
tu cuenta. Guarda el progreso tras cada párrafo y puede reanudar la tarea si se alcanza el límite
de uso. El juez es automático y a veces se equivoca: revisa las frases señaladas y sus fuentes.

## Límites conocidos

- Las obras sin PDF no se pueden consultar ni comprobar.
- Los PDF escaneados sin texto no se indexan como pasajes; no se hace OCR.
- Las consultas funcionan mejor en el idioma de los artículos y con sus términos.
- Las claves de cita las asigna el plugin y quedan en su índice. Para una obra nueva puede adoptar
  una clave existente en Zotero; una vez asignada, conserva la del índice. Usa el archivo generado
  `borrador/referencias.bib` para que las claves coincidan.

## Dónde guarda cosas

El índice de pasajes se guarda en `Documentos/TheAIWriter/indice`, o en `Documents/TheAIWriter/indice`
si esa es la carpeta de documentos del sistema. Puedes cambiarla con `THEAIWRITER_INDICE`.

La carpeta de Zotero se detecta a partir de su configuración; si no se encuentra una ruta
configurada, se busca en `~/Zotero`. Puedes indicarla con `THEAIWRITER_ZOTERO`.

El documento y sus informes se guardan en la carpeta donde abriste Claude. El modelo de búsqueda
se descarga por defecto en `~/.cache/theaiwriter/modelos`; se cambia con `EMBEDDING_CACHE_DIR`.

## Desarrollo

Desde el repositorio, con el entorno preparado:

```bash
uv sync --extra dev
.venv/bin/python -m pytest -q
```

La CLI ofrece `version`, `documento verificar <carpeta>` para el juez de apoyo y
`documento revisar <carpeta>` para el revisor por criterios. El plugin lanza ambos en segundo plano.

```bash
PYTHONPATH=src:. .venv/bin/python -m ai_writer version
PYTHONPATH=src:. .venv/bin/python -m ai_writer documento verificar /ruta/al/documento
PYTHONPATH=src:. .venv/bin/python -m ai_writer documento revisar /ruta/al/documento
```

La configuración se lee del entorno y del archivo `.env` del repositorio, si existe:

| Variable | Uso y valor por defecto |
|---|---|
| `DEFAULT_MODEL` | Modelo del juez y del revisor: `sonnet` |
| `LLM_BACKEND` | Backend del juez y del revisor: `claude-code` o `codex`; por defecto, `claude-code` |
| `CLAUDE_BIN` | Ejecutable de Claude Code: `claude` |
| `CODEX_BIN` | Ejecutable de Codex: `codex` |
| `CODEX_EFFORT` | Esfuerzo del backend Codex: `low` |
| `LLM_TIMEOUT` | Tiempo máximo por llamada, en segundos: `600` |
| `LLM_MAX_RETRIES` | Reintentos tras un fallo transitorio: `2` |
| `EMBEDDING_BACKEND` | Backend de búsqueda: solo `local` |
| `EMBEDDING_MODEL` | Modelo de búsqueda: `intfloat/multilingual-e5-small` |
| `EMBEDDING_CACHE_DIR` | Carpeta de descarga del modelo |
| `THEAIWRITER_INDICE` | Carpeta del índice de pasajes |
| `THEAIWRITER_ZOTERO` | Carpeta que contiene `zotero.sqlite` |

Al cambiar el modelo de búsqueda, la siguiente actualización reconstruye los pasajes y vectores;
conserva las claves de cita. Para usar el juez con Codex, elige también un `DEFAULT_MODEL` disponible
en ese backend. La planificación y la escritura las hace la sesión de Claude Code.

La [arquitectura](docs/architecture.md) describe los módulos y formatos.

## Licencia

El código de este repositorio se publica con licencia [MIT](LICENSE). Para leer los PDF usa
[PyMuPDF](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright), que se instala
aparte y tiene su propia licencia: AGPL-3.0 o comercial. Si distribuyes o ofreces un programa que lo
incluya, mira sus condiciones.
