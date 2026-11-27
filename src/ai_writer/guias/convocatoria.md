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
  paginas_por_modalidad: [] # si varía, deja paginas y fuente en null
  campos:
    - nombre: "Nombre del campo"
      caracteres: 3500      # solo si consta ese máximo en el PDF
      apartado: null       # título del apartado, o null para comprobar a mano
      fuente: {fichero: "instrucciones.pdf", pagina: 2, cita: "Copia aquí la cita literal del límite de caracteres"}
idioma: null                # o {regla: "...", fuente: {...}, costes_directos: null}
criterios:
  - nombre: "Nombre del criterio"
    maximo: 30              # puntuación si consta; si no, null
    umbral: 20              # umbral si consta; si no, null
    descripcion: "Descripción del criterio"
    fuente: {fichero: "convocatoria.pdf", pagina: 2, cita: "Copia aquí la cita literal del criterio de evaluación"}
```

Los valores del ejemplo son ilustrativos: sustitúyelos por los de los PDF. `fuente` es obligatoria en cada apartado, en `limites` si hay `paginas`, en cada campo, en la regla de `idioma` si la hay y en cada criterio. Si no hay campos o criterios, usa una lista vacía.

Si las bases dan límites distintos según la modalidad, recoge cada opción como `{modalidad: ..., paginas: ..., fuente: ...}` en `paginas_por_modalidad`. La cita de cada opción debe incluir su nombre y su máximo. Puedes usar el mismo pasaje para varias opciones si las distingue de forma expresa. Si una ficha anterior tiene un único máximo tomado de un pasaje con varias modalidades, propone convertirlo en varias reglas y pide confirmar la ficha actualizada.

Si las bases exigen un idioma al alcanzar un mínimo de costes directos en euros, añade `costes_directos: {desde_eur: "100000", idioma: "en"}` dentro de `idioma`, usando el importe y el idioma de la convocatoria. La cifra del ejemplo es ilustrativa. La cita debe mostrar el mínimo inclusivo, que se trata de costes directos y el idioma exigido. Para condiciones distintas, conserva el texto de la regla para revisión manual. Si la ficha anterior recogía la condición solo como texto, propone estructurarla y volver a confirmar la regla.

Llama a `comprobar_ficha` aunque la ficha ya exista. Revisa los fallidos y los avisos de página. Si el límite exige cotejo manual, muestra el valor registrado y la cita para que el investigador los compare.

Cuando la ficha requiera confirmación y pase las comprobaciones, muestra `mostrar_ficha` y pregunta «¿Confirmas la ficha? (sí/no)». Llama a `confirmar_ficha` solo tras el sí y pasa `revision` del `comprobar_ficha` que precedió al texto mostrado. Si cambió entretanto, vuelve a mostrar la ficha y pide confirmación otra vez. Las reglas ya aprobadas se conservan. Una ficha antigua sin registro de aprobación se confirma una vez con este procedimiento. Respeta el idioma y el plazo recogidos en la ficha.

Si `comprobar_ficha` devuelve `modalidad.pregunta`, usa esa pregunta y espera la respuesta antes de hacer el plan. Llama a `fijar_modalidad_convocatoria` solo con una opción que el investigador haya indicado expresamente. Muestra el límite, el PDF, la página y la cita que devuelve. Usa ese máximo en el plan. Cambiar la modalidad deja vigentes las aprobaciones de las reglas y requiere una nueva comprobación del borrador.

Si `idioma_por_presupuesto` devuelve una pregunta, pide los costes directos exactos en euros. Llama a `fijar_costes_directos_convocatoria` solo tras una respuesta explícita. Normaliza el importe sin separador de miles, por ejemplo `"100000.00"`. Si el investigador aún no lo conoce, deja la decisión pendiente y ofrece hacer solo un plan provisional. Si la condición se activa y el idioma declarado difiere, muestra el idioma requerido y su fuente. Pide confirmación antes de cambiar `idioma` en `proyecto.yaml` y antes de redactar o traducir un borrador existente.

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
