---
description: Verifica el borrador: que las citas existan, que las citas literales estén en el PDF y que cada frase coincida con la obra
argument-hint: "[«sin juez» para las comprobaciones que no usan un modelo]"
---

Verifica el borrador del documento de la carpeta actual con el servidor MCP `theaiwriter` y explica el resultado en español, de forma breve.

Petición del usuario: $ARGUMENTS

1. Llama a `verificar_documento`, con `juez` a falso si el usuario pidió «sin juez». Antes de lanzar el juez, avisa en una línea de que hace una llamada a Claude por cada párrafo con citas, con su cuenta, y de que corre en segundo plano.
2. Explica lo que se comprueba al momento:
   - Claves que no existen en Zotero o que están fuera de las colecciones del documento: enuméralas con la frase donde aparecen y propón para cada una una fuente real buscando con `buscar_pasajes`, o marcarla con `[@?]`.
   - Obras citadas sin PDF: sus frases no se pueden comprobar; recomienda adjuntar el PDF en Zotero.
   - Citas literales que no están en el PDF: muestra qué dice el borrador y qué dice el PDF.
   - En documentos de tipo `resultados`, cifras propias sin origen en los CSV o Markdown de `resultados/`: indica cuántas se comprobaron y enumera las que faltan con su sección y frase. Se comprueban decimales y porcentajes, con redondeo, salvo en Introducción, Métodos, frases con cita, código y destinos de enlaces o imágenes; los enteros sin porcentaje no se comprueban. Esta comprobación no usa un modelo y confirma que la cifra existe, no que la frase la describa bien.
   - En documentos de tipo `convocatoria`, resume la sección «Convocatoria»: requisitos de la ficha comprobados y fallidos, confirmación del usuario, apartados que faltan o sobran, orden, extensión, campos con límite de caracteres y marcas pendientes. Los avisos de página y los campos «a mano» requieren revisión. La extensión es una estimación por palabras y hay que comprobar las páginas reales en la plantilla oficial.
3. Para el juez, llama a `estado_verificacion` cuando el usuario lo pida o pasados unos minutos. Resume cuántas frases están apoyadas, parciales, tergiversadas y no apoyadas, y enseña las peores con su motivo. Recuerda que el juez es automático y se equivoca a veces: las frases señaladas hay que mirarlas, no borrarlas sin más.
4. No cambies el borrador sin que el usuario lo confirme.

El informe completo queda en `revision/verificacion.md`.
