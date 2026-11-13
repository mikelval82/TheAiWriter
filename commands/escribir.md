---
description: Escribe el documento automáticamente, en segundo plano, con evidencia de tu biblioteca
argument-hint: "[«con pausa» para revisar el plan antes de escribir]"
---

Lanza la escritura automática del documento de la carpeta actual con TheAIWriter. Responde siempre en español.

Petición del usuario: $ARGUMENTS

1. Llama a `estado_escritura`. Si la carpeta no es un documento, explica que primero hay que crearlo con `/theaiwriter:nuevo` y para.
   - Si hay una escritura `en_curso`, muestra el progreso y para.
   - Si está `esperando_aprobacion`, recuerda que el plan está en `borrador/plan.md` y que se aprueba con `/theaiwriter:estado`, y para.
   - Si está `terminado`, dilo y sugiere `/theaiwriter:validar` y revisar `borrador/documento.md`.
2. Comprueba que existe `materiales/abstract.md` con contenido. Si no existe, pide al usuario la idea y la tesis del documento, propón un abstract de 150-250 palabras, escríbelo ahí cuando lo confirme y sigue.
3. Antes de lanzar, avisa en una línea: la escritura hace del orden de 40 a 80 llamadas a Claude con su cuenta, tarda entre 30 y 90 minutos y puede seguir usando el chat mientras tanto.
4. Llama a `escribir_documento`, con `pausar_tras_plan` a verdadero si el usuario pide revisar el plan antes de escribir. Si el documento estaba `detenido`, `interrumpido` o en `error`, la misma llamada lo continúa donde se quedó.
5. Di qué se ha lanzado y que el progreso se consulta con `/theaiwriter:estado`.
