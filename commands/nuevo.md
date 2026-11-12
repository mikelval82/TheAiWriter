---
description: Convierte la carpeta actual en un documento nuevo de TheAIWriter
argument-hint: "[título o idea del documento]"
---

Prepara un documento nuevo de TheAIWriter en la carpeta actual. Responde siempre en español.

Idea del usuario: $ARGUMENTS

1. Llama a `estado_biblioteca`. Si la carpeta ya es un documento, dilo y para. Si la biblioteca no existe o no tiene papers, explica que primero hay que añadir PDFs con `/theaiwriter:biblioteca` y para.
2. Pregunta, en un solo mensaje y con tu propuesta para cada punto, lo que falte:
   - Tipo: `perspectiva` (paper de perspectiva o revisión a partir de la biblioteca), `resultados` (paper con resultados de un análisis propio) o `convocatoria` (memoria de una convocatoria).
   - Título de trabajo.
   - Idioma del documento (por defecto, español).
   - Colecciones de la biblioteca que usa; ninguna significa toda la biblioteca.
3. Con sus respuestas, llama a `crear_documento` y resume lo creado: el `proyecto.yaml`, cuántos papers puede citar y qué poner en `materiales/` (por ejemplo, el abstract en `materiales/abstract.md`).
