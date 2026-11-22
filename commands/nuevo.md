---
description: Convierte la carpeta actual en un documento nuevo de TheAIWriter
argument-hint: "[título o idea del documento]"
---

Prepara un documento nuevo de TheAIWriter en la carpeta actual, con las obras de Zotero. Responde siempre en español.

Idea del usuario: $ARGUMENTS

1. Llama a `colecciones_zotero`. Si devuelve `error`, explica que hace falta tener Zotero instalado en este ordenador con los PDF dentro, y para. Si la carpeta ya tiene un `proyecto.yaml`, dilo y para.
2. Pregunta, en un solo mensaje y con tu propuesta para cada punto, lo que falte:
   - Título de trabajo.
   - Tipo de documento: ensayo de perspectiva (`perspectiva`), artículo con resultados propios (`resultados`) o memoria para una convocatoria (`convocatoria`). En resultados, las tablas (CSV) y figuras van en `resultados/` y el código en `analisis/`. En convocatoria, los PDF oficiales (convocatoria, instrucciones de la memoria y plantilla) van en `convocatoria/`; el usuario completa `materiales/equipo.md` con personas y su papel, resultados previos, recursos, presupuesto y duración previstos. Solo se usará lo que esté escrito ahí.
   - Idioma del documento (por defecto, español).
   - Colecciones de Zotero que usa, mostrando las que hay con sus obras y cuántas traen PDF. Una colección incluye sus subcolecciones; ninguna significa todo Zotero.
3. Con sus respuestas, llama a `crear_documento` con el `tipo` elegido: «perspectiva», «resultados» o «convocatoria».
4. Llama a `estado_indice` con `actualizar` a verdadero. Avisa antes de que no gasta llamadas a Claude y de que la primera vez tarda unos segundos por PDF.
5. Llama a `estado_documento`. Resume lo creado y cuántas obras puede citar, con PDF e indexadas; termina con la lista de materiales en estado `falta` o `plantilla` que devuelve la herramienta, según el tipo de documento. Indica como siguiente paso completar el primer material; la línea final usa «Siguiente: /theaiwriter:estado» para consultar lo que falta después de completarlo.

Empieza la respuesta final con un resumen de 3 a 5 líneas; el detalle está en el informe. Termina con una línea «Siguiente: /theaiwriter:…» con el paso que toca.
