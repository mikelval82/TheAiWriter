# TheAIWriter

TheAIWriter es un plugin de Claude Code para escribir documentos científicos con los PDF de tu
Zotero. Claude planifica y escribe; el plugin le permite buscar y leer pasajes de los artículos y
verifica las citas del borrador.

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

1. Ejecuta `/theaiwriter:diagnostico`. Comprueba que se encuentra Zotero y que Claude responde con
   tu cuenta. No crea archivos del documento.
2. Ejecuta `/theaiwriter:nuevo`. Indica el tipo, el título, el idioma y las colecciones de Zotero
   que vas a usar. Una colección incluye sus subcolecciones; si no eliges ninguna, se usa todo
   Zotero. Crea `proyecto.yaml` y las carpetas `materiales/`, `borrador/`, `revision/` y
   `exportacion/`, y prepara el índice de pasajes de los PDF seleccionados. Puedes elegir un ensayo de perspectiva
   (`perspectiva`) o un artículo con resultados propios (`resultados`); este último añade
   `resultados/` para tablas CSV y figuras, y `analisis/` para código.
3. Pon tu idea y la tesis que quieres defender en `materiales/abstract.md`.
4. Ejecuta `/theaiwriter:escribir`. Claude explora los artículos, deja el plan en `borrador/plan.md`
   y escribe `borrador/documento.md`, consultando pasajes mientras redacta. Las búsquedas y los
   pasajes consultados quedan en `revision/consultas.json`. Al terminar lanza la verificación,
   que escribe `borrador/referencias.bib` y `revision/verificacion.md`.
5. Ejecuta `/theaiwriter:validar` para volver a comprobar el borrador. Actualiza la bibliografía y
   el informe, y lanza el juez en segundo plano. Con `/theaiwriter:validar sin juez` solo se hacen
   las comprobaciones que no usan un modelo. Los resultados y el progreso se guardan también en
   `revision/verificacion.json`.
6. Ejecuta `/theaiwriter:estado` para ver cómo van el índice, el borrador y el juez, y qué frases
   hay que revisar. Consulta los archivos existentes; no crea otro informe.
7. Ejecuta `/theaiwriter:biblioteca` para consultar las colecciones de Zotero y el estado del
   índice. Puedes pedirle que actualice el índice; los cambios se guardan en la carpeta del
   índice, fuera del documento. Los artículos y las colecciones se gestionan en Zotero.

Las citas del borrador usan claves como `[@smith2020empathy]`. Si falta una fuente, Claude debe
marcarla con `[@?]`.

En documentos de tipo `resultados`, Claude lee las tablas y el código antes de planificar y usa
Introducción, Métodos, Resultados, Discusión y Conclusión, en el idioma del documento. Las cifras
propias no llevan cita: salen de tablas de `resultados/` o de scripts guardados en `analisis/`
que escriben allí sus salidas CSV o Markdown, incluidos los recuentos y diferencias citados.

## Qué comprueba la verificación

1. Que la clave de cada cita existe en Zotero y pertenece a las colecciones del documento. También
   señala citas mal formadas, fuentes pendientes y obras sin PDF indexado. Tras editar el borrador,
   un hook bloquea las citas desconocidas, mal formadas o ajenas a sus colecciones.
2. Que una cita literal entre «» aparece palabra por palabra en el PDF de alguna de las obras
   citadas en esa frase. Se comprueban las citas de seis palabras o más; también se reconocen
   comillas inglesas y rectas. Se normalizan diferencias de extracción del PDF, como guiones de
   final de línea, y se permiten omisiones marcadas con puntos suspensivos. Una palabra cambiada
   hace que la cita deje de ser literal. Una traducción no cuenta como cita literal del original.
3. Que cada frase citada dice lo que dice la obra. Un juez compara la frase con pasajes de la obra
   citada, incluidos los consultados al escribir, y la clasifica como **apoyada**, **parcial**,
   **tergiversada** o **no apoyada**. Si no puede comprobarla, queda **sin juzgar**.
4. En documentos de tipo `resultados`, que los decimales y porcentajes propios tienen origen en
   los CSV o Markdown de `resultados/`, incluidos sus subdirectorios. Acepta redondeo y porcentajes
   expresados como fracciones en las tablas. Excluye Introducción, Métodos, frases con cita,
   código y destinos de enlaces e imágenes; no comprueba enteros sin porcentaje. Confirma que
   la cifra existe en los resultados, no que la frase la describa bien.

Las dos primeras comprobaciones y la de cifras propias no usan un modelo. Por defecto, el juez hace
una llamada a Claude por párrafo con citas que tenga pasajes para comparar, en segundo plano y con
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

La CLI conserva solo `version` y `documento verificar <carpeta>`. Este último ejecuta el juez; lo
lanza el plugin en segundo plano.

```bash
PYTHONPATH=src:. .venv/bin/python -m ai_writer version
PYTHONPATH=src:. .venv/bin/python -m ai_writer documento verificar /ruta/al/documento
```

La configuración se lee del entorno y del archivo `.env` del repositorio, si existe:

| Variable | Uso y valor por defecto |
|---|---|
| `DEFAULT_MODEL` | Modelo del juez: `sonnet` |
| `LLM_BACKEND` | Backend del juez: `claude-code` o `codex`; por defecto, `claude-code` |
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

La [arquitectura](docs/architecture.md) describe los módulos y formatos. Licencia: **AGPL-3.0-only**.
