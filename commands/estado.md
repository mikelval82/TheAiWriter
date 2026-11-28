---
description: Muestra materiales pendientes, borrador, informes y las acciones disponibles
---

Llama a `estado_documento` y responde en español. Muestra el título, el tipo, los materiales pendientes, el avance del borrador y el estado de los informes. Si hay una copia de Word, muestra dónde está y si hay que actualizarla. En documentos de tipo Resultados, muestra los recuentos de hallazgos, incluidas las fuentes que han cambiado. Si ya hay una comprobación de hallazgos, indica cuántas frases coinciden y cuáles requieren revisar el vínculo o añadirlo. Si hay comprobación, usa el recuento de pares de frase y obra para explicar cuántos se han juzgado del total y cuántos quedan pendientes. Si hay fuentes por revisar, indica cuántas y dónde verlas. Llama a `estado_indice` solo si el usuario pregunta por Zotero o si la indexación afecta al siguiente paso.

Si falta `proyecto.yaml`, sugiere abrir la carpeta de trabajo y usar `/theaiwriter:nuevo`. Ante otro error, indica cómo resolverlo antes de avanzar.

Si el proyecto de convocatoria devuelve `modalidad`, muestra la selección y el máximo de páginas o la pregunta pendiente. Para modificar la elección, indica `/theaiwriter:escribir modalidad`.

Si devuelve `idioma_por_presupuesto`, muestra si el importe en costes directos activa la condición de idioma y si el idioma declarado coincide. Para consultar o corregir el importe, indica `/theaiwriter:escribir presupuesto`.

Si `comprobacion.pdf_final` está disponible, muestra el recuento y el máximo, o explica por qué sigue pendiente. Si se guardó o sustituyó el PDF después del informe, indica que debe volver a comprobarse.

Muestra **Siguiente** con `siguiente` y `motivo_siguiente`, y **También puedes** con `alternativas` cuando las haya. Si hace falta ayuda para exportar, enlaza [la guía](https://github.com/mikelval82/TheAiWriter/blob/master/docs/exportar.md).
