---
description: Propone correcciones de los informes y aplica solo las que acepte el usuario
argument-hint: "[qué corregir: «las parciales», «la prioridad 1», «3.2»]"
---

Corrige lo señalado en los informes del documento con las herramientas MCP de `theaiwriter`. Responde siempre en español.

Petición del usuario: $ARGUMENTS

1. Consulta `estado_comprobacion` y lee `informes/comprobacion.md`. Si el usuario pide trabajar sobre el revisor, la revisión o sus prioridades, consulta también `estado_revision` y lee `informes/revision.md`. Si falta el informe, corresponde a un borrador anterior o `hallazgos_desactualizados` es verdadero, indica cómo obtener uno vigente según `estado_documento` antes de proponer cambios basados en él.
2. Selecciona los puntos pedidos; sin petición, empieza por los vínculos a hallazgos con avisos, las frases de Resultados por vincular, las citas incorrectas o pendientes, las frases tergiversadas, sin apoyo o parciales, las cifras sin origen y las marcas `[PENDIENTE: …]`. Para datos pendientes, explica qué falta y pide al investigador que lo aporte.
3. Para cada frase tergiversada, no apoyada o parcial, vuelve a leer la obra con `leer_pasaje` (busca el pasaje con `buscar_pasajes` si hace falta). Propón una redacción fiel al pasaje, otra cita comprobada o `[@?]`. Para un vínculo con una frase cambiada, compara el antes con `linea_borrador` del hallazgo aprobado y propone restaurarla si sigue siendo válida. Para una frase sin vínculo, propone vincularla a un hallazgo vigente si es la misma afirmación. Si hay un cambio científico o de formulación, guíalo a `/theaiwriter:hallazgos` y espera su aprobación antes de aplicarlo. Para cifras sin origen o apartados de convocatoria, propón el cambio concreto a partir de los materiales. Si una prioridad pide datos ausentes, como trayectoria del equipo, no los inventes: indica qué dato debe aportar el usuario y dónde escribirlo, por ejemplo en `materiales/equipo.md`.
4. Enseña una lista numerada; cada elemento debe tener apartado, «Antes:» y «Después:». Pregunta exactamente «¿Cuáles aplico? (todas, 1, 3… o ninguna)» y espera la respuesta. Aplica solo los aceptados; con «ninguna», conserva el borrador.
5. Después llama a `comprobar_documento` con `juez` a falso y resume el resultado en `informes/comprobacion.md`. El informe descarta las frases que ya no están y deja sin juzgar las nuevas. Esta comprobación no gasta llamadas a Claude; Vuelve a pasar el juez si cambiaste frases con citas bibliográficas.

Antes de cerrar, llama a `estado_documento`. Muestra **Siguiente** con `siguiente` y `motivo_siguiente`, y **También puedes** con `alternativas` cuando las haya. Si el paso es pasar a Word, enlaza [la guía](https://github.com/mikelval82/TheAiWriter/blob/master/docs/exportar.md).
