---
description: Explica qué hace cada comando, qué necesita y qué toca ahora
argument-hint: "[tu duda, p. ej. «cómo paso a Word» o «qué pongo en resultados/»]"
---

Explica TheAIWriter al usuario. Responde siempre en español, breve y sin tecnicismos. No escribas ni cambies ficheros y no lances comprobaciones ni revisiones: esta ayuda no gasta más que la conversación.

Duda del usuario: $ARGUMENTS

## Sin duda concreta

1. Llama a `estado_documento`. Si la carpeta actual es un documento, di en una línea su título, su tipo y el paso que toca, con su `siguiente`. Si no lo es, di que para empezar se abre Claude Code en una carpeta vacía y se usa `/theaiwriter:nuevo`, y que `/theaiwriter:diagnostico` comprueba antes la instalación.
2. Enseña el camino, una línea por comando:
   - `/theaiwriter:nuevo`: crea el documento (perspectiva, resultados o convocatoria) y dice qué materiales rellenar.
   - `/theaiwriter:escribir`: plan y borrador con los PDF de Zotero; con «con pausa» espera a que apruebes el plan.
   - `/theaiwriter:comprobar`: mira que las citas existan, que las literales estén en el PDF y que cada frase diga lo que dice la obra. Con «sin juez» no hace llamadas aparte.
   - `/theaiwriter:corregir`: propone cambios numerados con antes y después y aplica solo los que aceptes.
   - `/theaiwriter:revisar`: evalúa por criterios de la convocatoria o la revista, sin tocar el borrador.
   - Pasar a Word o LibreOffice con Pandoc, según la guía de exportación.
3. Y las ayudas: `/theaiwriter:estado` (dónde estás y qué toca), `/theaiwriter:diagnostico` (instalación y biblioteca de Zotero) y `/theaiwriter:ayuda` con una duda concreta.
4. Recuerda en una línea qué gasta cuota de la cuenta de Claude: escribir, el juez de `comprobar` (una llamada por párrafo con citas) y `revisar` (una llamada).

## Con una duda

Lee el manual del plugin, `${CLAUDE_PLUGIN_ROOT}/docs/manual.md`, y, si la duda es sobre Word, LibreOffice, Pandoc o citas vivas, `${CLAUDE_PLUGIN_ROOT}/docs/exportar.md`. Contesta con lo que digan; si no lo cubren, dilo y no lo inventes. Si la duda es sobre el documento actual, llama también a `estado_documento`.

Termina con «Manual completo: https://github.com/mikelval82/TheAiWriter/blob/master/docs/manual.md» y, si la carpeta es un documento, con «Siguiente: /theaiwriter:…» según su `siguiente`.
