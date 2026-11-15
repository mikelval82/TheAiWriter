---
description: Muestra cómo va el documento: el índice, el borrador y la verificación de las citas
---

Informa del estado del documento de la carpeta actual. Responde siempre en español y de forma breve.

1. Llama a `estado_indice`: obras del documento, cuántas tienen PDF y cuántas están indexadas.
2. Mira si existen `materiales/abstract.md`, `borrador/plan.md` y `borrador/documento.md`, y di cuántas palabras tiene el borrador.
3. Llama a `estado_verificacion`. Si todavía no se ha verificado, dilo y sugiere `/theaiwriter:validar`. Si el juez está `en_curso`, di cuántos párrafos lleva. Si está `limite_de_uso` o `interrumpido`, explica que se reanuda donde se quedó con `/theaiwriter:validar`. Si está `terminado`, resume cuántas frases están apoyadas y cuántas hay que revisar.
4. Termina con el siguiente paso útil.
