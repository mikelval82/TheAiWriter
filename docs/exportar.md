# Pasar el borrador a Word

## Pandoc con bibliografía

Instala [Pandoc](https://pandoc.org/installing.html). Descarga el estilo CSL de la revista desde
[Zotero](https://www.zotero.org/styles) o el [repositorio CSL](https://github.com/citation-style-language/styles),
y deja el estilo y la plantilla oficial de Word junto al documento. Desde la carpeta del documento:

```bash
pandoc borrador/documento.md --citeproc --bibliography borrador/referencias.bib --csl <estilo>.csl --reference-doc <plantilla>.docx --resource-path borrador -M lang=es -M reference-section-title=Referencias -o exportacion/documento.docx
```

Sustituye `<estilo>` y `<plantilla>` por los nombres reales; sin plantilla, quita `--reference-doc`.
Los estilos que ya usas en Zotero están en la carpeta `styles` de sus datos (`~/Zotero/styles`).
`--resource-path` permite encontrar las figuras, `reference-section-title` titula la bibliografía y
`lang` pone el idioma del documento (`en` en inglés). `--reference-doc` toma los estilos y
las propiedades de página de la plantilla oficial, pero no su contenido. Revisa las páginas y los
campos en Word antes de entregar. Consulta el [manual de Pandoc](https://pandoc.org/MANUAL.html#option--reference-doc).

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
