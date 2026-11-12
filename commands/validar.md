---
description: Valida el borrador del documento: citas, huecos pendientes y extensión
---

Llama a la herramienta `validar_documento` del servidor MCP `theaiwriter` y explica el resultado en español, de forma breve:

- Si todo es correcto, dilo en una línea y añade cuántas citas y huecos `[[PENDIENTE]]` hay.
- Si hay citas que no existen o que están fuera de las colecciones del documento, enuméralas con la frase donde aparecen y propone para cada una una alternativa real: busca con `buscar_evidencia` una fuente de la biblioteca que respalde la frase, o sugiere marcarla con `[@?]`. No cambies el borrador sin que el usuario lo confirme.
- Si hay avisos de citas que nunca salieron en una búsqueda, recomienda comprobarlas con `referencia`.
- Muestra la tabla de palabras por sección solo si el usuario la pide o si alguna sección está vacía.

El informe completo queda en `revision/validacion.md`.
