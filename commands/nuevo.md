---
description: Convierte la carpeta actual en un documento nuevo de TheAIWriter
argument-hint: "[título o idea del documento]"
---

Prepara un documento nuevo de TheAIWriter en la carpeta actual, con las obras de Zotero. Responde siempre en español.

Idea del usuario: $ARGUMENTS

1. Si la carpeta ya tiene un `proyecto.yaml`, explica que puede retomarla e indica el siguiente paso con `estado_documento`. En caso contrario, llama a `colecciones_zotero`. Si devuelve `error`, explica cómo comprobar Zotero con `/theaiwriter:diagnostico` antes de intentar crear el proyecto.
2. Pregunta, en un solo mensaje y con tu propuesta para cada punto, lo que falte:
   - Título de trabajo.
   - Tipo de documento: ensayo de perspectiva (`perspectiva`), artículo con resultados propios (`resultados`) o memoria para una convocatoria (`convocatoria`). En resultados, las tablas (CSV), figuras y salidas van en `resultados/`. Las notas se pueden añadir a `materiales/`, y los scripts y cuadernos van en `analisis/`. En convocatoria, los PDF oficiales (convocatoria, instrucciones de la memoria y plantilla) van en `convocatoria/`; el usuario completa `materiales/equipo.md` con personas y su papel, resultados previos, recursos, presupuesto y duración previstos. Solo se usará lo que esté escrito ahí.
   - Idioma del documento (por defecto, español).
   - Colecciones de Zotero que usa, mostrando las que hay con sus obras y cuántas traen PDF. Una colección incluye sus subcolecciones; ninguna significa todo Zotero.
3. Con sus respuestas, llama a `crear_documento` con el `tipo` elegido: «perspectiva», «resultados» o «convocatoria».
4. Llama a `estado_indice` con `actualizar` a verdadero. Avisa antes de que no gasta llamadas a Claude y de que la primera vez tarda unos segundos por PDF.
5. Resume lo creado, cuántas obras con PDF están indexadas y qué materiales siguen pendientes según `estado_documento`.

Antes de cerrar, llama a `estado_documento`. Muestra **Siguiente** con `siguiente` y `motivo_siguiente`, y **También puedes** con `alternativas` cuando las haya. Si el paso es pasar a Word, enlaza [la guía](https://github.com/mikelval82/TheAiWriter/blob/master/docs/exportar.md).
