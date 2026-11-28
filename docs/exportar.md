# Pasar el borrador a Word

## Exportación estándar

Instala Pandoc y comprueba que `/theaiwriter:diagnostico` lo encuentra. Si ya lo tienes en otro
entorno, añade su carpeta al `PATH` o define `THEAIWRITER_PANDOC` con la ruta al ejecutable antes de
abrir Claude Code. [Instalar Pandoc](https://pandoc.org/installing.html)

Usa `/theaiwriter:exportar` cuando hayas revisado el borrador. El comando escribe
`exportacion/documento.docx` e indica los avisos de Pandoc. Puedes pedir «provisional» para obtener
una copia mientras sigues revisando. Si el archivo de Word ya existe, pide «reemplazar» para
actualizarlo. Guarda aparte cualquier cambio que hayas hecho en Word antes de reemplazarlo.

La exportación usa la bibliografía de `/theaiwriter:comprobar sin juez`. Busca las figuras en
`borrador/`, la raíz del proyecto y `resultados/`. Si quieres un estilo de citas concreto, copia su CSL al
proyecto y pásale su nombre al comando. Para aplicar los estilos de una revista, indica también la
plantilla DOCX. La plantilla aporta sus estilos y propiedades de página. Revisa en Word las
figuras, las citas, los campos y los límites de páginas. [Manual de Pandoc](https://pandoc.org/MANUAL.html#option--reference-doc)

Para convertir manualmente desde la carpeta del proyecto, puedes usar:

```bash
pandoc borrador/documento.md --citeproc --bibliography borrador/referencias.bib --strip-comments --resource-path borrador:.:resultados -M lang=es -M reference-section-title=Referencias -o exportacion/documento.docx
```

En Windows, usa punto y coma como separador de las carpetas de recursos, entre comillas.
Para elegir formato, añade `--csl estilo.csl` o `--reference-doc plantilla.docx`.

## Citas vivas de Zotero

1. Instala [Better BibTeX](https://retorque.re/zotero-better-bibtex/installation/) en Zotero 8 o
   posterior, desde Herramientas → Extensiones (*Tools → Plugins*). Al instalarse genera las claves de
   todas las obras y las guarda en Zotero; haz antes una copia de la carpeta de datos. Si a alguna obra
   le falta la clave, selecciónala y usa su menú de Better BibTeX.
2. Descarga su [filtro `zotero.lua` para Pandoc](https://retorque.re/zotero-better-bibtex/exporting/pandoc/)
   y déjalo en la carpeta del documento.
3. Pide a Claude que prepare las citas vivas. Escribe `exportacion/documento-zotero.md`, una copia del
   borrador con las claves de Zotero, y dice qué obras no la tienen. Las claves del borrador no cambian.
4. Con Zotero abierto, genera el fichero en el formato de tu procesador: `.docx` para Word u `.odt` para
   LibreOffice. No sirven cruzados: en LibreOffice, el complemento de Zotero no encuentra las citas de
   un `.docx` («Debes insertar una cita…»). `--reference-doc` debe ser del mismo formato.

```bash
pandoc exportacion/documento-zotero.md --lua-filter zotero.lua --resource-path borrador -o exportacion/documento.odt
```

```bash
pandoc exportacion/documento-zotero.md --lua-filter zotero.lua --reference-doc <plantilla>.docx --resource-path borrador -o exportacion/documento.docx
```

5. Abre el fichero, entra en las preferencias del documento de Zotero, elige estilo e idioma, acepta y
   pulsa Refresh. Hasta entonces las citas se ven como `<Do Zotero Refresh: …>`. El `.odt` trae ya el
   hueco de la bibliografía; en Word se añade con el botón de Zotero.

Si algo falla:

- «Styles not yet loaded»: Zotero acaba de arrancar. Espera un momento y repite.
- «Ya se está ejecutando un comando de integración»: Zotero se ha quedado con una orden a medias. Cierra
  sus ventanas pendientes (pueden estar detrás) o reinícialo.

Se ha probado con Zotero 10.0.8, Better BibTeX 9.0.77 y LibreOffice. En Word solo se ha comprobado que el
`.docx` lleva los campos. Según [este hilo del foro](https://forum.obsidian.md/t/how-do-i-use-enhancing-export-better-bibtex-zotero-citations-in-group-libraries/84248),
no convierte las citas de bibliotecas de grupo; es un problema reportado, aunque la documentación
del filtro contempla indicar una biblioteca de grupo.
