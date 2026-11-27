---
description: Exporta el borrador a Word con Pandoc
argument-hint: "[«provisional», «reemplazar», estilo CSL o plantilla DOCX]"
---

Exporta el borrador del proyecto a Word. Responde en español. Petición del usuario: $ARGUMENTS

1. Consulta `estado_documento`. Si falta un borrador, orienta a `/theaiwriter:escribir`. Si la comprobación o la revisión está pendiente, falló, quedó desactualizada o señala problemas, consulta también los recuentos de hallazgos y el siguiente paso. Si queda algo por decidir, explica qué falta y ofrece el siguiente paso del estado o una exportación provisional. Continúa si el investigador pidió una exportación provisional o la acepta.
2. Si se pide un estilo CSL o una plantilla, usa la ruta del archivo correspondiente dentro del proyecto. Si ya existe `exportacion/documento.docx`, aplícale `reemplazar: true` solo si el usuario pidió reemplazarlo o lo confirmó.
3. Llama a `exportar_documento`. Si falta la bibliografía, orienta a `/theaiwriter:comprobar sin juez`. Si falta Pandoc, enlaza su instalación y explica que puede indicar la ruta de una instalación existente con `THEAIWRITER_PANDOC`. Pide que vuelva a abrir Claude Code para repetir la exportación. Si Pandoc avisa de una figura o referencia que no se pudo incluir, indica qué corregir y propone `/theaiwriter:exportar reemplazar` después de corregirlo.
4. Si se generó el DOCX, indica dónde está y si la exportación es provisional. Termina con **Siguiente** y el archivo que debe abrir en Word. Como alternativa, remite a `/theaiwriter:estado` para retomar la revisión de los pendientes o a la [guía de exportación](https://github.com/mikelval82/TheAiWriter/blob/master/docs/exportar.md) si necesita citas vivas de Zotero.

La exportación estándar usa referencias formateadas. El borrador sigue en Markdown.
