---
description: Comprueba la instalación y muestra la biblioteca de Zotero y su índice
argument-hint: "[qué quieres ver, p. ej. «obras sin PDF» o «actualiza el índice»]"
---

Comprueba la instalación o consulta la biblioteca con las herramientas MCP de `theaiwriter`. Responde siempre en español.

Petición del usuario: $ARGUMENTS

- Sin petición: llama a `diagnostico` y `probar_claude`, como comprobación de instalación. Avisa antes de que la prueba hace una llamada breve a Claude con la cuenta del usuario. Resume sistema, Python, Zotero (carpeta, obras y PDF), índice, documento actual y si Claude está disponible y respondió. Añade un resumen de `colecciones_zotero` y `estado_indice`: colecciones y obras con PDF, indexadas o pendientes; si hay documento, di qué colecciones usa.
- «Actualiza el índice»: llama a `estado_indice` con `actualizar` a verdadero. No gasta llamadas a Claude. Di cuántas obras se indexaron, cuáles no dieron texto y cuáles fallaron.
- «Obras sin PDF»: consulta `estado_indice`, enuméralas y explica que no se pueden consultar ni comprobar hasta adjuntarles el PDF en Zotero.
- Otras peticiones sobre colecciones o biblioteca: usa `colecciones_zotero` y `estado_indice` según lo que se pide.

La biblioteca se gestiona en Zotero. TheAIWriter solo la lee y recoge los cambios en la siguiente búsqueda. Si una herramienta devuelve `error`, explica qué dice y cómo resolverlo. Sugiere `nuevo` si todavía no hay documento; si lo hay, `estado`.

Empieza la respuesta final con un resumen de 3 a 5 líneas; el detalle está en el informe. Termina con una línea «Siguiente: /theaiwriter:…» con el paso que toca.
