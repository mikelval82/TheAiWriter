---
description: Evalúa el borrador por criterios y propone trabajo concreto sin cambiarlo
argument-hint: "[revista a la que se dirige el artículo]"
---

Revisa el borrador de la carpeta actual por criterios con el servidor MCP `theaiwriter` y explica dónde trabajar más, en español. No cambia el borrador.

Petición del usuario: $ARGUMENTS

1. Lee `proyecto.yaml` y determina el origen de los criterios:
   - Tipo `convocatoria`: llama a `comprobar_ficha`. Si falta, hay fallidos o requiere confirmación, sigue el procedimiento de `/theaiwriter:escribir solo ficha` antes de revisar la memoria. Si falta la modalidad, sigue `/theaiwriter:escribir modalidad`. Debe haber al menos un criterio de evaluación con fuente.
   - Si el usuario nombra una revista, pídele que deje en `revista/` las normas de autores o la guía de revisores en PDF. Mira todos los PDF de `revista/` y di qué páginas no has leído, sin afirmar qué hay en ellas. Redacta `revista/ficha.yaml` solo con criterios que estén en esos PDF, cada uno con una cita literal de al menos seis palabras:
     - Si la revista da una lista expresa de criterios de publicación o evaluación, van primero, uno por elemento, sin juntarlos ni saltarse ninguno y con su nombre. Si un elemento tiene menos de seis palabras, cita el tramo seguido de la lista que lo contiene, copiado tal cual, con los elementos vecinos que hagan falta.
     - Las demás preguntas o exigencias para evaluar el manuscrito que detallen un criterio de la lista van en su `descripcion`. Con las que queden, agrupa por tema (literatura, datos y código, claridad…) en pocos criterios más, sin pasar de unos 10 en total salvo que la lista ya los supere.
     - La `descripcion` no añade exigencias que no estén en los PDF. Los formatos, plazos, tasas y trámites no son criterios.

     Usa este esquema:

     ```yaml
     revista: "Nombre de la revista"
     confirmada: false
     criterios:
       - nombre: "Nombre del criterio"
         maximo: null         # puntuación solo si consta en el PDF
         umbral: null         # umbral solo si consta en el PDF
         descripcion: "Descripción del criterio según el PDF"
         fuente:
           fichero: "guia-revisores.pdf"
           pagina: 2          # página del PDF, desde 1
           cita: "Copia aquí una cita literal de al menos seis palabras del PDF"
     ```

     Los valores del ejemplo son ilustrativos: sustitúyelos por los de los PDF. Llama a `comprobar_ficha`, corrige los fallidos y revisa los avisos de página. Si no hay fallidos, enseña el texto de `mostrar_ficha` y pregunta «¿Confirmas la ficha? (sí/no)». Llama a `confirmar_ficha` solo tras el sí. No enseñes el YAML salvo que el usuario lo pida.
   - Si ya existe `revista/ficha.yaml` en un artículo, usa sus criterios aunque el usuario no vuelva a nombrar la revista; compruébala igualmente con `comprobar_ficha`; si no hay fallidos y falta confirmación, enseña `mostrar_ficha`, pregunta «¿Confirmas la ficha? (sí/no)» y llama a `confirmar_ficha` solo tras el sí.
   - Sin revista ni ficha de revista, usa los criterios genéricos del tipo (`perspectiva` o `resultados`) y dilo al usuario.
2. Recomienda haber pasado `/theaiwriter:comprobar` antes: la revisión usa su resultado de apoyo de las citas y actualiza las comprobaciones que no necesitan un modelo. No vuelve a juzgar las citas.
3. Avisa en una línea de que hace una llamada a Claude con su cuenta y corre en segundo plano. Llama a `revisar_documento`; consulta `estado_revision` cuando el usuario lo pida o pasados unos minutos.
4. Presenta las prioridades y, por criterio, su nivel y el trabajo que haría falta. Señala las carencias con el apartado del borrador; no des puntuaciones numéricas. Recuerda que la evaluación es automática y orientativa y no sustituye a la de la convocatoria o revista. Los `[PENDIENTE: …]` piden conseguir el dato, nunca inventarlo; reconocer limitaciones y riesgos es una fortaleza.
5. Conserva el borrador y resume el estado de la revisión.

El informe completo queda en `informes/revision.md` y el resultado también en `informes/revision.json`.

Antes de cerrar, llama a `estado_documento`. Muestra **Siguiente** con `siguiente` y `motivo_siguiente`, y **También puedes** con `alternativas` cuando las haya. Si el paso es pasar a Word, enlaza [la guía](https://github.com/mikelval82/TheAiWriter/blob/master/docs/exportar.md).
