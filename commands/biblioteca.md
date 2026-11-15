---
description: Muestra las colecciones de Zotero que puede usar TheAIWriter y el estado de su índice de pasajes
argument-hint: "[qué quieres ver, p. ej. «qué obras no tienen PDF» o «actualiza el índice»]"
---

Muestra la biblioteca de Zotero tal como la ve TheAIWriter, con las herramientas del servidor MCP `theaiwriter`. Responde siempre en español.

Petición del usuario: $ARGUMENTS

- Sin petición: llama a `colecciones_zotero` y a `estado_indice`, y resume en pocas líneas cuántas obras hay, las colecciones con sus obras y cuántas traen PDF, y cuántas están indexadas o pendientes. Si la carpeta actual es un documento, di qué colecciones usa.
- Actualizar el índice: llama a `estado_indice` con `actualizar` a verdadero. No gasta llamadas a Claude. Di cuántas obras se han indexado y cuáles no dieron texto (PDF escaneados) o fallaron.
- Obras sin PDF: enuméralas y explica que no se pueden consultar ni comprobar hasta que tengan el PDF adjunto en Zotero.

La biblioteca se gestiona en Zotero: para añadir un paper, crear una colección o corregir un título, hazlo allí. TheAIWriter solo lee Zotero, nunca escribe en él, y recoge los cambios la siguiente vez que busca.

Si una herramienta devuelve `error`, explícalo con sus palabras y propón cómo resolverlo.
