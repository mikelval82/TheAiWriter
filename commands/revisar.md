---
description: Evalúa el borrador por criterios y propone trabajo concreto sin cambiarlo
argument-hint: "[revista a la que se dirige el artículo]"
---

Revisa el borrador de la carpeta actual por criterios con el servidor MCP `theaiwriter` y explica dónde trabajar más, en español. No cambia el borrador.

Petición del usuario: $ARGUMENTS

1. Lee `proyecto.yaml` y determina el origen de los criterios:
   - Tipo `convocatoria`: usa `convocatoria/ficha.yaml`. Si falta o no está confirmada, sigue primero `/theaiwriter:escribir` para prepararla, o compruébala y pide al usuario que la confirme. Debe tener al menos un criterio de evaluación con fuente; no inventes criterios que no estén en los PDF.
   - Si el usuario nombra una revista, pídele que deje en `revista/` las normas de autores o la guía de revisores en PDF. Redacta `revista/ficha.yaml` solo con criterios que estén en esos PDF, cada uno con una cita literal de al menos seis palabras. Usa este esquema:

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

     Los valores del ejemplo son ilustrativos: sustitúyelos por los de los PDF. Llama a `comprobar_ficha`, corrige los fallidos y revisa los avisos de página. Enseña la ficha y pide confirmación al usuario antes de poner `confirmada: true`.
   - Si ya existe `revista/ficha.yaml` en un artículo, usa sus criterios aunque el usuario no vuelva a nombrar la revista; compruébala igualmente y pide confirmación si falta.
   - Sin revista ni ficha de revista, usa los criterios genéricos del tipo (`perspectiva` o `resultados`) y dilo al usuario.
2. Recomienda haber pasado `/theaiwriter:validar` antes: la revisión usa su resultado de apoyo de las citas y actualiza las comprobaciones que no necesitan un modelo. No vuelve a juzgar las citas.
3. Avisa en una línea de que hace una llamada a Claude con su cuenta y corre en segundo plano. Llama a `revisar_documento`; consulta `estado_revision` cuando el usuario lo pida o pasados unos minutos.
4. Presenta las prioridades y, por criterio, su nivel y el trabajo que haría falta. Señala las carencias con el apartado del borrador; no des puntuaciones numéricas. Recuerda que la evaluación es automática y orientativa y no sustituye a la de la convocatoria o revista. Los `[PENDIENTE: …]` piden conseguir el dato, nunca inventarlo; reconocer limitaciones y riesgos es una fortaleza.
5. No cambies el borrador. Si el usuario quiere trabajar un punto, lo hace él o lo pide expresamente.

El informe completo queda en `revision/revision.md` y el resultado también en `revision/revision.json`.
