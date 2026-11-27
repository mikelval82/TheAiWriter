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
datos_propuesta: {}          # solo datos que necesitas para evaluar reglas aplicables
reglas_aplicables: []
criterios:
  - nombre: "Nombre del criterio"
    maximo: 30              # puntuación si consta; si no, null
    umbral: 20              # umbral si consta; si no, null
    descripcion: "Descripción del criterio"
    fuente: {fichero: "convocatoria.pdf", pagina: 2, cita: "Copia aquí la cita literal del criterio de evaluación"}
```

Los valores del ejemplo son ilustrativos: sustitúyelos por los de los PDF. `fuente` es obligatoria en cada apartado, en `limites` si hay `paginas`, en cada campo, en la regla de `idioma` si la hay y en cada criterio. Si no hay campos o criterios, usa una lista vacía.

Para condiciones de una ficha nueva, usa `datos_propuesta` y `reglas_aplicables`. Define los datos a partir de las bases con un identificador en minúsculas, `tipo` (`texto`, `numero` o `booleano`), `pregunta` y, para textos, `opciones` si procede. El investigador confirma sus valores. Explicita la unidad en la pregunta para los datos numéricos.

Cada regla incluye `id`, `requisito`, `fuente` y una lista `cuando`. Todas las condiciones de la lista deben cumplirse. Una lista vacía significa que aplica siempre. Una condición es `{dato: ..., operador: ..., valor: ...}`. Usa `igual` o `distinto` con texto y booleanos. Los números admiten también `mayor`, `mayor_o_igual`, `menor` y `menor_o_igual`.

En `comprobar` puedes usar una comparación sobre un dato declarado, `idioma_proyecto`, `paginas_pdf` o `palabras_borrador`. Para un documento obligatorio usa `{archivo: "exportacion/anexo.pdf"}` y explica el nombre de archivo esperado. Este control comprueba la presencia del archivo. Si el requisito precisa juicio humano o queda fuera de estas comprobaciones, omite `comprobar` y conserva la condición y la fuente para revisión manual.

Por ejemplo, este fragmento usa datos declarados en la ficha y una comprobación que sirve para cualquier límite de páginas. Sustituye valores, preguntas y cita por los de la convocatoria. Para agrupar alternativas, usa una regla por alternativa cuando cada una tenga un requisito distinto.

```yaml
datos_propuesta:
  modalidad:
    tipo: texto
    pregunta: "¿Qué modalidad has elegido?"
    opciones: [individual, coordinada]
reglas_aplicables:
  - id: extension_individual
    requisito: "Límite de páginas para propuestas individuales"
    cuando: [{dato: modalidad, operador: igual, valor: individual}]
    comprobar: {dato: paginas_pdf, operador: menor_o_igual, valor: 20}
    fuente: {fichero: "instrucciones.pdf", pagina: 2, cita: "Copia aquí el pasaje literal de la convocatoria"}
```

Las fichas antiguas con `paginas_por_modalidad` o `idioma.costes_directos` siguen admitidas. Evita duplicar en ambos formatos el mismo requisito.

Llama a `comprobar_ficha` aunque la ficha ya exista. Revisa los fallidos y los avisos de página. Si el límite exige cotejo manual, muestra el valor registrado y la cita para que el investigador los compare.

Cuando la ficha requiera confirmación y pase las comprobaciones, muestra `mostrar_ficha` y pregunta «¿Confirmas la ficha? (sí/no)». Llama a `confirmar_ficha` solo tras el sí y pasa `revision` del `comprobar_ficha` que precedió al texto mostrado. Si cambió entretanto, vuelve a mostrar la ficha y pide confirmación otra vez. Las reglas ya aprobadas se conservan. Una ficha antigua sin registro de aprobación se confirma una vez con este procedimiento. Respeta el idioma y el plazo recogidos en la ficha.

Si `comprobar_ficha` devuelve `modalidad.pregunta`, usa esa pregunta y espera la respuesta antes de hacer el plan. Llama a `fijar_modalidad_convocatoria` solo con una opción que el investigador haya indicado expresamente. Muestra el límite, el PDF, la página y la cita que devuelve. Usa ese máximo en el plan. Cambiar la modalidad deja vigentes las aprobaciones de las reglas y requiere una nueva comprobación del borrador.

Si `idioma_por_presupuesto` devuelve una pregunta, pide los costes directos exactos en euros. Llama a `fijar_costes_directos_convocatoria` solo tras una respuesta explícita. Normaliza el importe sin separador de miles, por ejemplo `"100000.00"`. Si el investigador aún no lo conoce, deja la decisión pendiente y ofrece hacer solo un plan provisional. Si la condición se activa y el idioma declarado difiere, muestra el idioma requerido y su fuente. Pide confirmación antes de cambiar `idioma` en `proyecto.yaml` y antes de redactar o traducir un borrador existente.

Para las reglas de `reglas_aplicables`, pide los datos con `solicitar: true` de `comprobar_ficha`. Llama a `fijar_dato_convocatoria` solo tras la respuesta explícita. Si falta un dato, señala qué regla queda pendiente. Usa las reglas con `aplica: true` para orientar el plan aunque solo puedan comprobarse en el documento final. Consulta el informe automático tras redactar.

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
