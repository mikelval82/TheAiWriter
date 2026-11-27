---
description: Comprueba el borrador: que las citas existan, que las citas literales estén en el PDF y que cada frase coincida con la obra
argument-hint: "[«sin juez» o «evidencia» con una frase o apartado]"
---

Comprueba el borrador del documento de la carpeta actual con el servidor MCP `theaiwriter` y explica el resultado en español, de forma breve.

Petición del usuario: $ARGUMENTS

Si el usuario pide «evidencia», un pasaje o la fuente que respaldó un veredicto, llama a
`evidencia_citas` con la frase o el apartado y omite los pasos que lanzan comprobaciones.
Muestra la afirmación, el veredicto, el pasaje y su página. Enlaza el PDF en Zotero cuando haya
enlace. Para leer el contexto, usa `leer_pasaje` con el identificador. Si todavía falta el informe, orienta a `/theaiwriter:comprobar`. Si quedó
desactualizado, señala qué citas faltan por juzgar y orienta a `/theaiwriter:comprobar`.
Si hay más resultados, ofrece consultar la página siguiente. Si está todo disponible,
ofrece abrir en Zotero o retomar con `/theaiwriter:estado`.

1. Llama a `comprobar_documento`, con `juez` a falso si el usuario pidió «sin juez». Antes de lanzar el juez, avisa en una línea de que hace una llamada a Claude por cada párrafo con citas, con su cuenta, y de que corre en segundo plano.
2. Explica lo que se comprueba al momento:
   - Claves que no existen en Zotero o que están fuera de las colecciones del documento: enuméralas con la frase donde aparecen y propón para cada una una fuente real buscando con `buscar_pasajes`, o marcarla con `[@?]`.
   - Obras citadas sin PDF: sus frases no se pueden comprobar; recomienda adjuntar el PDF en Zotero.
   - Frases que parecen hablar de una obra y no llevan cita (`atribuciones_sin_cita`): enséñalas y propón la clave que les falta, o di que son del propio autor. Se buscan por sus palabras y hay avisos de más.
   - Afirmaciones cuya fuente conviene revisar (`fuentes_por_revisar`). Distingue los `[@?]` de los avisos por redacción empírica o porcentajes. Pide al investigador que decida si la frase requiere una cita, describe un resultado propio o expresa una interpretación.
   - Citas literales que no están en el PDF: muestra qué dice el borrador y qué dice el PDF.
   - En documentos de tipo `resultados` con hallazgos, usa `hallazgos_borrador`. Indica cuántos vínculos coinciden, cuáles requieren revisión y qué frases de Resultados quedan por vincular. Muestra la frase del borrador, la aprobada cuando difiera y la fuente con archivo y ubicación. Si cambió la evidencia, orienta a `/theaiwriter:hallazgos`; si cambió la frase, orienta a `/theaiwriter:corregir`.
   - En documentos de tipo `resultados` que todavía usan la comprobación anterior, cifras propias sin origen en los CSV o Markdown de `resultados/`: indica cuántas se comprobaron y enumera las que faltan con su sección y frase. Se comprueban decimales y porcentajes, con redondeo, salvo en Introducción, Métodos, frases con cita, código y destinos de enlaces o imágenes; los enteros sin porcentaje no se comprueban. Esta comprobación no usa un modelo y confirma que la cifra existe, no que la frase la describa bien.
   - En documentos de tipo `convocatoria`, resume la ficha, las reglas por aprobar y los límites que requieren cotejo manual. Si hay discrepancias, muestra el valor y la cita y orienta a `/theaiwriter:escribir solo ficha`. En el borrador distingue los apartados ausentes de los que están presentes y pendientes de contenido. Resume también los encabezados que sobran, el orden, la extensión, los límites de caracteres y las marcas pendientes. La extensión sigue siendo una estimación por palabras.
3. Para el juez, llama a `estado_comprobacion` cuando el usuario lo pida o pasados unos minutos. Muestra cuántos pares de frase y obra se han juzgado del total, cuántos quedan pendientes y cuántos de los juzgados están apoyados, parciales, tergiversados o sin apoyo. Enseña los casos prioritarios con su motivo. Si su estado es `desactualizado`, el borrador ha cambiado desde que pasó y las frases nuevas salen sin juzgar: dilo y propón volver a lanzarlo. Recuerda que el juez es automático y se equivoca a veces: las frases señaladas hay que mirarlas, no borrarlas sin más.
4. No cambies el borrador sin que el usuario lo confirme.

El informe completo queda en `informes/comprobacion.md`.

Antes de cerrar, llama a `estado_documento`. Muestra **Siguiente** con `siguiente` y `motivo_siguiente`, y **También puedes** con `alternativas` cuando las haya. Si el paso es pasar a Word, enlaza [la guía](https://github.com/mikelval82/TheAiWriter/blob/master/docs/exportar.md).
