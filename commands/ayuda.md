---
description: Explica qué hace cada comando, qué necesita y qué toca ahora
argument-hint: "[tu duda, p. ej. «cómo paso a Word» o «qué pongo en resultados/»]"
---

Explica TheAIWriter al usuario. Responde siempre en español, breve y sin tecnicismos. No escribas ni cambies ficheros y no lances comprobaciones ni revisiones: esta ayuda no gasta más que la conversación.

Duda del usuario: $ARGUMENTS

## Sin duda concreta

1. Llama a `estado_documento`. Si hay un proyecto, muestra su título y tipo antes de explicar cómo retomarlo.
2. Explica los comandos principales en una línea cada uno.
   - `/theaiwriter:nuevo`: crea el documento (perspectiva, resultados o convocatoria) y dice qué materiales rellenar.
   - `/theaiwriter:escribir`: plan y borrador con los PDF de Zotero; con «con pausa» espera a que apruebes el plan.
   - En proyectos de Resultados, `/theaiwriter:hallazgos` muestra de dónde sale cada resultado y te permite aprobarlo, editarlo o dejarlo pendiente.
   - `/theaiwriter:comprobar` comprueba las citas y señala qué pasajes respaldan las frases citadas. Con «sin juez» hace solo las comprobaciones inmediatas.
   - Pasar a Word o LibreOffice con Pandoc, según la guía de exportación.
3. Añade que `/theaiwriter:estado` sirve para retomar el trabajo. Si toca corregir, revisar por criterios o resolver un problema de instalación, explica también el comando correspondiente.
4. Recuerda en una línea qué gasta cuota de la cuenta de Claude: escribir, el juez de `comprobar` (una llamada por párrafo con citas) y `revisar` (una llamada).

## Con una duda

Lee el manual del plugin, `${CLAUDE_PLUGIN_ROOT}/docs/manual.md`, y, si la duda es sobre Word, LibreOffice, Pandoc o citas vivas, `${CLAUDE_PLUGIN_ROOT}/docs/exportar.md`. Contesta con lo que digan; si no lo cubren, dilo y no lo inventes. Si la duda es sobre el documento actual, llama también a `estado_documento`.

Enlaza el [manual completo](https://github.com/mikelval82/TheAiWriter/blob/master/docs/manual.md). Usa el estado ya consultado o consúltalo antes de cerrar. Si falta `proyecto.yaml`, sugiere abrir la carpeta de trabajo y usar `/theaiwriter:nuevo`, con `/theaiwriter:diagnostico` como alternativa para comprobar la instalación. Ante otro error, indica cómo resolverlo antes de avanzar. En un proyecto, muestra **Siguiente** con `siguiente` y `motivo_siguiente`, y **También puedes** con `alternativas` cuando las haya. Si toca pasar a Word, enlaza la guía de exportación.
