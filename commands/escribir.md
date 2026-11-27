---
description: Planifica y escribe el documento consultando los PDF de Zotero, y verifica las citas
argument-hint: "[«con pausa» para aprobar el plan antes de escribir, o la sección que quieres escribir]"
---

Escribe el documento de la carpeta actual apoyándote en los PDF de sus colecciones de Zotero, con las herramientas del servidor MCP `theaiwriter`. Tú planificas y escribes; las herramientas te dan los pasajes. Responde al usuario siempre en español.

Petición del usuario: $ARGUMENTS

## Antes de empezar

1. Lee `proyecto.yaml`. Si no existe, explica que primero hay que crear el documento con `/theaiwriter:nuevo` y para.
2. Llama obligatoriamente a `guia_escritura` y sigue la guía del tipo de documento. Completa sus preparativos antes de planificar.
3. Lee `materiales/abstract.md`. Si no existe, está vacío o `guia_escritura` devuelve `abstract_vacio` a verdadero (solo tiene preguntas en comentarios y encabezados), pide al usuario la idea y el objetivo, propón un abstract de 150 a 250 palabras, escríbelo ahí cuando lo confirme y sigue.
4. Llama a `estado_indice` con `actualizar` a verdadero. Si hay obras sin PDF, dilo en una línea. Si solo redactas Métodos o Resultados de un estudio y sus materiales son suficientes, puedes omitir la búsqueda bibliográfica.

## Plan

5. Para las secciones que requieren bibliografía, explora antes de planificar: haz entre 6 y 12 llamadas a `buscar_pasajes` sobre los temas del abstract. Busca en el idioma de los papers y con los términos que usarían.
6. Escribe `borrador/plan.md`: el objetivo, las secciones y, para cada sección, qué va a sostener y qué obras lo apoyan. Si algo del abstract no tiene apoyo en las colecciones, dilo en el plan en vez de taparlo.
7. En un proyecto de Resultados, enseña el plan con los hallazgos por sección y pide aprobación antes de redactar. Aplica la misma pausa en los otros tipos si el usuario pidió «con pausa».

## Escritura

8. Escribe `borrador/documento.md` sección a sección, en el idioma del documento. Si una sección de Métodos o Resultados ya existe, agrupa el antes y después de esa sección y espera a que el investigador elija qué cambios aplicar. Para cada sección:
   - Si la sección usa bibliografía, vuelve a buscar con consultas concretas de esa sección.
   - Antes de citar un dato, un resultado o una cifra de una obra, lee su contexto con `leer_pasaje`.
   - Cita con `[@clave]`, usando solo claves que hayan salido en `buscar_pasajes`, `leer_pasaje` o `leer_paginas`.
9. Reglas de las citas, sin excepciones:
   - Cada frase con cita dice lo que dice el pasaje que leíste, con el mismo alcance. No generalices un resultado de un estudio a «los estudios muestran».
   - Toda frase que diga lo que dice una obra lleva su `[@clave]` en la misma frase, aunque la anterior o la siguiente ya la citen. Sin cita no se comprueba.
   - Si la obra recoge la afirmación de otra obra, dilo así («según recogen…») o no la cites como hallazgo suyo.
   - La cita va justo detrás de lo que dice la obra. Lo que aportas tú (un plan, una hipótesis, una valoración) va en otra frase, no antes de la cita.
   - Ninguna cifra, muestra o tamaño de efecto atribuido a una obra que no hayas leído en un pasaje.
   - Nada de tu memoria: si lo sabes pero no está en los pasajes, no lleva cita de estas colecciones.
   - Una cita literal va entre «», copiada tal cual y en el idioma original del paper.
   - Si a una afirmación le falta fuente, márcala con `[@?]` en lugar de forzar una cita.

## Comprobación

10. Al terminar, avisa del coste del juez y llama a `comprobar_documento`. Resume las claves que no existan o estén fuera de las colecciones y las citas literales que no coincidan.
11. El juez de apoyo corre en segundo plano y hace una llamada a Claude por cada párrafo con citas. Consulta el resultado con `estado_comprobacion` cuando lo pida o al cabo de unos minutos.
12. Con el resultado del juez, resume las frases tergiversadas, no apoyadas y parciales y los avisos sobre hallazgos, cifras o convocatoria. Las correcciones se proponen con `/theaiwriter:corregir`, con el visto bueno del usuario.
13. Resume dónde están el borrador, el informe `informes/comprobacion.md` y la bibliografía `borrador/referencias.bib`. Indica cuántos pares de frase y obra se han juzgado del total y cuántos quedan pendientes. Si hay obras sin citar que podrían aportar algo, indícalas.

Antes de empezar, avisa en una línea de lo que gasta con la cuenta de Claude del usuario.

Antes de cerrar, llama a `estado_documento`. Muestra **Siguiente** con `siguiente` y `motivo_siguiente`, y **También puedes** con `alternativas` cuando las haya. Si el paso es pasar a Word, enlaza [la guía](https://github.com/mikelval82/TheAiWriter/blob/master/docs/exportar.md).
