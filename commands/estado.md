---
description: Muestra cómo va la escritura del documento, aprueba el plan o la detiene
argument-hint: "[«aprobar», «detener» o nada]"
---

Gestiona la escritura automática del documento de la carpeta actual. Responde siempre en español y de forma breve.

Petición del usuario: $ARGUMENTS

- Sin petición: llama a `estado_escritura` y resume el estado, la fase, los párrafos escritos frente al total, las secciones terminadas y el coste estimado. Si hay `error`, explícalo con sus palabras usando las últimas líneas del registro y propone reanudar con `/theaiwriter:escribir`. Si está `interrumpido` o `detenido`, di que se puede reanudar con `/theaiwriter:escribir`.
- Si está `esperando_aprobacion`: resume el plan de `borrador/plan.md` (tesis y secciones con sus ideas clave) y pregunta si lo aprueba o qué quiere cambiar. Los cambios se hacen en `borrador/plan.json`, conservando su estructura. Cuando el usuario apruebe, llama a `aprobar_plan`.
- «aprobar»: llama a `aprobar_plan`.
- «detener»: llama a `detener_escritura` y explica que se parará al terminar el párrafo en curso y que se reanuda con `/theaiwriter:escribir`.
- Si está `terminado`: indica dónde está el resultado (`borrador/documento.md`, `revision/validacion.md`, `revision/revision_critica.md` y, si existe, `revision/citas_corregidas.md`) y resume en una línea la validación.
