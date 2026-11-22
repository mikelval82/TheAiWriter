---
description: Muestra materiales pendientes, borrador, informes y el siguiente paso
---

Informa del estado del documento de la carpeta actual con las herramientas MCP de `theaiwriter`. Responde siempre en español y de forma breve.

1. Llama a `estado_documento`: muestra el tipo, los materiales que faltan o siguen como plantilla, las palabras del borrador y el estado de comprobación y revisión. No hace llamadas a modelos.
2. Llama a `estado_indice` para resumir obras, PDF e indexación.
3. Termina con «Siguiente: <valor de siguiente>», usando el `siguiente` de `estado_documento`. Si es completar un fichero o pasar a Word, la línea final conserva ese paso; para Word, enlaza `docs/exportar.md` del plugin. Para un comando, usa «Siguiente: /theaiwriter:…».

Empieza la respuesta final con un resumen de 3 a 5 líneas; el detalle está en el informe. Termina con una línea «Siguiente: /theaiwriter:…» con el paso que toca.

Cuando `siguiente` es un material por completar o la guía de Word, prevalece ese valor literal en la línea final.
