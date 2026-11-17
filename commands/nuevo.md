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
5. Resume lo creado: cuántas obras puede citar el documento, cuántas tienen PDF y están indexadas, y cuáles no tienen PDF (esas no se pueden consultar ni comprobar: conviene adjuntar el PDF en Zotero). Indica que el siguiente paso es poner la idea y la tesis en `materiales/abstract.md` y lanzar `/theaiwriter:escribir`.
