---
description: Muestra la biblioteca de papers, añade PDFs y gestiona colecciones
argument-hint: "[qué quieres hacer, p. ej. «añade ~/Descargas/papers» o «crea la colección Emoción»]"
---

Gestiona la biblioteca de TheAIWriter con las herramientas del servidor MCP `theaiwriter`. Responde siempre en español.

Petición del usuario: $ARGUMENTS

- Sin petición: llama a `estado_biblioteca` y resume en pocas líneas la carpeta, cuántos papers hay, las colecciones con su número de papers, los PDFs pendientes y el estado del último procesado. Si la carpeta actual es un documento, di qué colecciones usa. Termina sugiriendo el siguiente paso útil.
- Añadir PDFs: usa `anadir_pdfs` con las rutas que indique. Después pregunta si quiere procesarlos ahora y avisa de que cada paper son unas 6 a 10 llamadas a Claude con su cuenta. Si dice que sí, llama a `procesar_pdfs`: corre en segundo plano y puede seguir trabajando mientras; el progreso se ve con `/theaiwriter:biblioteca`.
- Crear o cambiar una colección: si no sabe qué papers incluir, llama a `listar_papers` y propón una selección por tema; luego `guardar_coleccion`. Muestra los títulos guardados.
- Borrar una colección: confirma antes con el usuario y usa `borrar_coleccion`. Los papers no se borran.

Si una herramienta devuelve `error`, explícalo con sus palabras y propón cómo resolverlo. No edites a mano `colecciones.yaml` ni los ficheros de la biblioteca.
