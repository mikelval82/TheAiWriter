# Ruta de convocatorias

Estado: propuesta, pendiente de aprobación (2026-11-16).
Caso de prueba: Proyectos de Generación de Conocimiento 2026 (AEI), memoria individual tipo A, B y RTA.
Documentos de la convocatoria: `~/Documentos/TheAIWriter/convocatorias/pid-2026/`.

## Qué cambia respecto a los otros dos tipos

Una memoria de convocatoria mezcla tres clases de afirmaciones, y cada una se comprueba contra una fuente distinta:

| Afirmación | Fuente | Comprobación |
| --- | --- | --- |
| Estado del arte | PDF de Zotero | La que ya existe (citas, citas literales, juez de apoyo) |
| Equipo, resultados previos, recursos | `materiales/equipo.md`, escrito por el usuario | Regla de escritura: nada que no esté ahí; lo que falte se marca `[PENDIENTE: …]` |
| Lo que exige la convocatoria | PDF de la convocatoria | Nueva: ficha de la convocatoria y conformidad del borrador con ella |

Lo nuevo es la tercera fila. PID2026 exige una memoria de 20 páginas como máximo, con apartados fijos (justificación y novedad; objetivos, metodología y plan de trabajo; impacto; presupuesto; capacidad formativa), un campo de impacto de 3.500 caracteres, e inglés obligatorio si se piden 100.000 € o más. Se evalúa con tres criterios con puntuación y umbral (anexo I).

## Diseño

### La ficha de la convocatoria

Nada de PID2026 va escrito en el código. Cada documento de tipo `convocatoria` tiene una carpeta `convocatoria/` con los PDF oficiales (convocatoria, instrucciones de la memoria, plantilla) y una ficha `convocatoria/ficha.yaml` que Claude redacta en la sesión leyendo esos PDF y que el usuario confirma.

La ficha contiene:

- `apartados`: título, nivel, si es obligatorio o condicional (y la condición), resumen de lo que piden las instrucciones y a qué criterio alimenta.
- `limites`: páginas máximas de la memoria, caracteres máximos de campos concretos, formato (letra, márgenes).
- `idioma`: regla, si la hay.
- `criterios`: nombre, puntuación máxima, umbral y descripción.
- `plazo`.

Cada requisito de la ficha lleva `fichero`, `pagina` y una `cita` literal del documento. Una comprobación sin modelo confirma que esa cita está, palabra por palabra, en el PDF indicado (se reutiliza `_verbatim` de `verificacion.py` y `cut_pdf` de `passages.py`). Así un requisito inventado o mal leído se detecta antes de escribir.

### La conformidad del borrador

Comprobación sin modelo, `check_call(texto, ficha)`:

- apartados obligatorios que faltan, y apartados que no están en la ficha;
- orden de los apartados;
- extensión: palabras del borrador y páginas estimadas frente al máximo (ver D3);
- campos con límite de caracteres;
- marcas `[PENDIENTE: …]` que quedan.

Se integra en `verificar_documento` como quinta comprobación, solo para el tipo `convocatoria`, con su sección en `revision/verificacion.md`.

### La escritura

`commands/escribir.md` gana una sección para el tipo `convocatoria`:

- antes de planificar, comprobar que la ficha existe y está confirmada;
- el plan asigna a cada apartado un presupuesto de palabras y dice qué criterio alimenta; al final, una tabla criterio → apartados que lo cubren;
- el estado del arte sigue las reglas de citas de siempre;
- lo del equipo sale solo de `materiales/equipo.md`;
- cronograma y presupuesto se escriben con lo que el usuario haya dado, o se marcan pendientes; no se inventan cifras ni nombres.

## Fases

| Fase | Contenido | Verificación |
| --- | --- | --- |
| 1 | Tipo `convocatoria`, carpeta `convocatoria/`, esquema de la ficha y comprobación de sus citas contra los PDF | Pruebas; una ficha con un requisito inventado se rechaza |
| 2 | `check_call` e integración en la verificación; comandos `nuevo`, `escribir`, `validar` | Pruebas; borrador sin un apartado obligatorio o demasiado largo queda marcado |
| 3 | Prueba con PID2026: Claude redacta la ficha desde los PDF, escribe una memoria de prueba y se plantan errores | Ficha revisada a mano contra las instrucciones; errores plantados detectados |
| 4 | README, arquitectura y versión 0.4.0 | `pytest` entero |

Tamaño estimado: 300 a 400 líneas de código más pruebas. Las fases 1, 2 y 4 se encargan a Codex; la 3 la dirijo yo.

## Decisiones

| | Decisión | Recomendación | Por qué |
| --- | --- | --- | --- |
| D1 | Ficha genérica o código específico de PID2026 | Ficha genérica | Cada alumna tendrá su convocatoria; PID2026 es solo el caso de prueba |
| D2 | Quién redacta la ficha | Claude en la sesión, desde los PDF, y el usuario la confirma | Mantener fichas hechas por nosotros no escala y caducan cada año |
| D3 | Cómo se mide la extensión | Estimación por palabras, con aviso a partir del 90 % del máximo | Contar páginas reales exige generar el Word con la plantilla oficial; se deja para después |
| D4 | De dónde sale la información del equipo | De `materiales/equipo.md`, que escribe el usuario | Leer CV es otro proyecto, y son datos personales |
| D5 | Evaluador simulado: un juez que puntúe la memoria con los criterios del anexo I | No en esta versión | Primero hay que ver si la conformidad sin modelo ya es útil; un juez que puntúa puede dar falsa seguridad |
| D6 | Contenido de la memoria de prueba | Propuesta ficticia sobre predicción de resistencia en *E. coli*, con la colección del tutorial y un equipo inventado y marcado como ficticio | Reutiliza lo ya indexado; no es una solicitud real |

## Supuestos

1. La alumna tiene los PDF de su convocatoria; el plugin no los busca ni los descarga.
2. La memoria se escribe en Markdown y la alumna la pasa a la plantilla oficial a mano.
3. CIGE 2027 no sirve de caso de prueba: su baremo valora al grupo y no la memoria.
4. Solo memoria científico-técnica; quedan fuera el CVA, la solicitud electrónica y el presupuesto detallado.

## Sin especificar todavía

- Cómo estimar páginas a partir de palabras con figuras y tablas: se calibra en la fase 3 con la plantilla de PID2026.
- Proyectos coordinados y otros tipos de memoria: niebla; se mira si alguien lo necesita.
- Si la ruta entra en el curso (nota del curso: decidir antes del 16/12).

## Siempre / Nunca

- Siempre: cada requisito de la ficha con su página y su cita literal del documento oficial.
- Nunca: inventar datos del equipo, cifras de presupuesto o requisitos; presentar la memoria de prueba como solicitud real; escribir en Zotero.

## Progreso

| Fase | Estado |
| --- | --- |
| 1 | Hecha |
| 2 | Hecha |
| 3 | Pendiente |
| 4 | Hecha |
