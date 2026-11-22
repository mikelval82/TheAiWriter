---
description: Propone correcciones de los informes y aplica solo las que acepte el usuario
argument-hint: "[qué corregir: «las parciales», «la prioridad 1», «3.2»]"
---

Corrige lo señalado en los informes del documento con las herramientas MCP de `theaiwriter`. Responde siempre en español.

Petición del usuario: $ARGUMENTS

1. Consulta `estado_comprobacion` y lee `informes/comprobacion.md`. Si el usuario pide trabajar sobre el revisor o sus prioridades, consulta también `estado_revision` y lee `informes/revision.md`. Usa los informes disponibles; si no hay ninguno, sugiere `/theaiwriter:comprobar` y para.
2. Selecciona los puntos pedidos; sin petición, empieza por las frases tergiversadas y no apoyadas, las parciales, las frases sin cita que hablan de una obra, las cifras sin origen y los apartados de convocatoria que faltan.
3. Para cada frase tergiversada, no apoyada o parcial, vuelve a leer la obra con `leer_pasaje` (busca el pasaje con `buscar_pasajes` si hace falta). Propón una redacción fiel al pasaje, otra cita comprobada o `[@?]`. Para cifras sin origen o apartados de convocatoria, propón el cambio concreto a partir de los materiales. Si una prioridad pide datos ausentes, como trayectoria del equipo, no los inventes: indica qué dato debe aportar el usuario y dónde escribirlo, por ejemplo en `materiales/equipo.md`.
4. Enseña una lista numerada; cada elemento debe tener apartado, «Antes:» y «Después:». Pregunta exactamente «¿Cuáles aplico? (todas, 1, 3… o ninguna)» y espera la respuesta. Aplica solo los aceptados; con «ninguna», conserva el borrador.
5. Después llama a `comprobar_documento` con `juez` a falso y resume el resultado en `informes/comprobacion.md`. El informe descarta las frases que ya no están y deja sin juzgar las nuevas. Esta comprobación no gasta llamadas a Claude; los cambios de frases necesitan pasar después por el juez.
6. Termina con «Siguiente: /theaiwriter:comprobar».

Empieza la respuesta final con un resumen de 3 a 5 líneas; el detalle está en el informe. Termina con una línea «Siguiente: /theaiwriter:…» con el paso que toca.
