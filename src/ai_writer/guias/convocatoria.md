# Guía de escritura: convocatoria

## Antes de planificar

Lee `materiales/equipo.md` y los PDF oficiales de `convocatoria/`: convocatoria, instrucciones de la memoria y plantilla. No escribas el borrador con una ficha sin confirmar.

Si no existe `convocatoria/ficha.yaml`, redáctala desde esos PDF con este esquema. Los títulos van en el idioma del documento; cada requisito lleva fichero, página del PDF (desde 1) y una cita literal de al menos 6 palabras copiada tal cual. No deduzcas requisitos que no estén en los PDF.

```yaml
convocatoria: "Nombre de la convocatoria"
confirmada: false
plazo: null                 # texto si consta
apartados:
  - titulo: "Título exacto del apartado en el idioma del documento"
    nivel: 3                # 2 o 3, según la plantilla
    obligatorio: true
    condicion: null         # texto si solo aplica en ciertos casos
    pide: "Resumen de lo que piden las instrucciones"
    criterios: ["Nombre del criterio que alimenta"]
    fuente:
      fichero: "instrucciones.pdf"
      pagina: 2
      cita: "Copia aquí una cita literal de al menos seis palabras del PDF"
limites:
  paginas: null             # máximo si consta; con páginas, fuente es obligatoria
  palabras_por_pagina: 500
  fuente: null              # {fichero: ..., pagina: ..., cita: ...}
  campos:
    - nombre: "Nombre del campo"
      caracteres: 3500      # solo si consta ese máximo en el PDF
      apartado: null       # título del apartado, o null para comprobar a mano
      fuente: {fichero: "instrucciones.pdf", pagina: 2, cita: "Copia aquí la cita literal del límite de caracteres"}
idioma: null                # o {regla: "...", fuente: {fichero: ..., pagina: ..., cita: ...}}
criterios:
  - nombre: "Nombre del criterio"
    maximo: 30              # puntuación si consta; si no, null
    umbral: 20              # umbral si consta; si no, null
    descripcion: "Descripción del criterio"
    fuente: {fichero: "convocatoria.pdf", pagina: 2, cita: "Copia aquí la cita literal del criterio de evaluación"}
```

Los valores del ejemplo son ilustrativos: sustitúyelos por los de los PDF. `fuente` es obligatoria en cada apartado, en `limites` si hay `paginas`, en cada campo, en la regla de `idioma` si la hay y en cada criterio. Si no hay campos o criterios, usa una lista vacía.

Llama a `comprobar_ficha`, corrige todos los fallidos y revisa los avisos de página. Si no hay fallidos, enseña el texto de `mostrar_ficha` y pregunta «¿Confirmas la ficha? (sí/no)». Llama a `confirmar_ficha` solo tras el sí. No enseñes el YAML salvo que el usuario lo pida. Si ya existe, compruébala igualmente y, si no está confirmada, muestra `mostrar_ficha`, pregunta «¿Confirmas la ficha? (sí/no)» y llama a `confirmar_ficha` solo tras el sí antes de escribir. Respeta también su regla de idioma y su plazo.

## Plan

- Asigna a cada apartado un presupuesto de palabras que respete el límite de extensión y di qué criterio alimenta. Usa `palabras_por_pagina` para estimar el presupuesto total si hay límite de páginas.
- Termina con una tabla criterio → apartados que lo cubren; señala los criterios sin cubrir.
- Los apartados condicionales que no apliquen se omiten y se dice en el plan por qué.

## Borrador

- Usa exactamente los títulos y el orden de la ficha, con su nivel de encabezado.
- El estado del arte y la motivación siguen las reglas de citas comunes, con búsquedas por apartado.
- Equipo, resultados previos, recursos, cronograma y presupuesto: solo lo que esté en `materiales/equipo.md`. Lo que falte se marca `[PENDIENTE: qué dato falta]`. Nunca inventes nombres, cifras, fechas ni méritos.
- No prometas resultados; formula las hipótesis como hipótesis.
- La memoria argumenta por qué el proyecto hace falta, y eso tienta a estirar las fuentes. Lo que una obra no estudió (otra especie, otro periodo, años no vistos) no se le atribuye, y lo que una obra sí aborda no se presenta como laguna suya.
- Los encabezados en negrita de un párrafo no llevan afirmaciones sobre la literatura: si las necesitan, van en la frase con su cita.
- Al terminar, llama a `comprobar_documento` y resume lo que marque la sección «Convocatoria» para proponer las correcciones con `/theaiwriter:corregir`. La extensión es una estimación por palabras: comprueba las páginas reales en la plantilla oficial.
