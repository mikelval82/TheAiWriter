---
description: Planifica y escribe el documento consultando los PDF de Zotero, y verifica las citas
argument-hint: "[«con pausa» para aprobar el plan antes de escribir, o la sección que quieres escribir]"
---

Escribe el documento de la carpeta actual apoyándote en los PDF de sus colecciones de Zotero, con las herramientas del servidor MCP `theaiwriter`. Tú planificas y escribes; las herramientas te dan los pasajes. Responde al usuario siempre en español.

Petición del usuario: $ARGUMENTS

## Antes de empezar

1. Lee `proyecto.yaml`. Si no existe, explica que primero hay que crear el documento con `/theaiwriter:nuevo` y para.
2. Llama obligatoriamente a `guia_escritura` y sigue la guía del tipo de documento. Completa sus preparativos antes de planificar.
3. Lee `materiales/abstract.md`. Si no existe o está vacío, pide al usuario la idea y el objetivo, propón un abstract de 150 a 250 palabras, escríbelo ahí cuando lo confirme y sigue.
4. Llama a `estado_indice` con `actualizar` a verdadero. Si hay obras sin PDF, dilo en una línea.

## Plan

5. Explora antes de planificar: haz entre 6 y 12 llamadas a `buscar_pasajes` sobre los temas del abstract. Busca en el idioma de los papers y con los términos que usarían.
6. Escribe `borrador/plan.md`: el objetivo, las secciones y, para cada sección, qué va a sostener y qué obras lo apoyan. Si algo del abstract no tiene apoyo en las colecciones, dilo en el plan en vez de taparlo.
7. Si el usuario pidió «con pausa», enséñale el plan y espera a que lo apruebe. Si no, sigue.

## Escritura

8. Escribe `borrador/documento.md` sección a sección, en el idioma del documento. Para cada sección:
   - Vuelve a buscar con consultas concretas de esa sección; no escribas solo con lo que encontraste al planificar.
   - Antes de citar un dato, un resultado o una cifra de una obra, lee su contexto con `leer_pasaje`.
   - Cita con `[@clave]`, usando solo claves que hayan salido en `buscar_pasajes`, `leer_pasaje` o `leer_paginas`.
9. Reglas de las citas, sin excepciones:
   - Cada frase con cita dice lo que dice el pasaje que leíste, con el mismo alcance. No generalices un resultado de un estudio a «los estudios muestran».
   - Si la obra recoge la afirmación de otra obra, dilo así («según recogen…») o no la cites como hallazgo suyo.
   - La cita va justo detrás de lo que dice la obra. Lo que aportas tú (un plan, una hipótesis, una valoración) va en otra frase, no antes de la cita.
   - Ninguna cifra, muestra o tamaño de efecto atribuido a una obra que no hayas leído en un pasaje.
   - Nada de tu memoria: si lo sabes pero no está en los pasajes, no lleva cita de estas colecciones.
   - Una cita literal va entre «», copiada tal cual y en el idioma original del paper.
   - Si a una afirmación le falta fuente, márcala con `[@?]` en lugar de forzar una cita.

## Verificación

10. Al terminar, llama a `verificar_documento`. Corrige en el momento las claves que no existan o estén fuera de las colecciones y las citas literales que no coincidan.
11. El juez de apoyo corre en segundo plano y hace una llamada a Claude por cada párrafo con citas. Avisa al usuario y consulta el resultado con `estado_verificacion` cuando lo pida o al cabo de unos minutos.
12. Con el resultado del juez: para cada frase «tergiversada» o «no apoyada», vuelve a leer la obra con `leer_pasaje` y corrige la frase para que diga lo que dice el pasaje, cambia la cita o márcala con `[@?]`. Las «parciales», revísalas y ajusta el alcance. Después vuelve a llamar a `verificar_documento` una vez.
13. Resume al usuario: dónde está el borrador, cuántas frases citadas están apoyadas y cuáles quedan por revisar a mano, qué obras de la colección no se citan y si alguna parece aportar algo, con el informe en `revision/verificacion.md` y la bibliografía en `borrador/referencias.bib`.
