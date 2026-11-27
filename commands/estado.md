---
description: Muestra materiales pendientes, borrador, informes y las acciones disponibles
---

Llama a `estado_documento` y responde en español. Muestra el título, el tipo, los materiales pendientes, el avance del borrador y el estado de los informes. Si hay una copia de Word, muestra dónde está y si hay que actualizarla. En documentos de tipo Resultados, muestra los recuentos de hallazgos, incluidas las fuentes que han cambiado. Si ya hay una comprobación de hallazgos, indica cuántas frases coinciden y cuáles requieren revisar el vínculo o añadirlo. Si hay comprobación, usa el recuento de pares de frase y obra para explicar cuántos se han juzgado del total y cuántos quedan pendientes. Llama a `estado_indice` solo si el usuario pregunta por Zotero o si la indexación afecta al siguiente paso.

Si falta `proyecto.yaml`, sugiere abrir la carpeta de trabajo y usar `/theaiwriter:nuevo`. Ante otro error, indica cómo resolverlo antes de avanzar.

Muestra **Siguiente** con `siguiente` y `motivo_siguiente`, y **También puedes** con `alternativas` cuando las haya. Si hace falta ayuda para exportar, enlaza [la guía](https://github.com/mikelval82/TheAiWriter/blob/master/docs/exportar.md).
