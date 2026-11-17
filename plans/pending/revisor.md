# Revisor por criterios

Estado: aprobado (2026-11-17). Rama: `convocatorias`.
Origen: idea de la revisión con evaluador simulado de PaperOrchestra (arXiv 2604.05018), cambiada para que no reescriba.

## Qué es

Una operación que lanza el usuario (`/theaiwriter:revisar`) y que le dice dónde trabajar más. Evalúa el borrador con los criterios de la convocatoria o de la revista y escribe `revision/revision.md`. No toca el borrador.

## Diseño

- **Criterios.** Convocatoria: los de `convocatoria/ficha.yaml`, que ya llevan citas literales comprobadas. Revista: el usuario deja las normas de autores o la guía de revisores en `revista/`, y Claude redacta `revista/ficha.yaml` (solo criterios, con citas literales comprobadas contra esos PDF y confirmada por el usuario). Sin revista: criterios genéricos por tipo, como datos del paquete.
- **Resultado.** Por criterio: nivel (bien, mejorable o flojo), fortalezas, carencias con su apartado y trabajo que haría falta. Al final, las tres prioridades. Sin nota numérica.
- **Quién revisa.** Una llamada aparte a Claude, sin el contexto de la sesión que escribió, en segundo plano como el juez.
- **Qué ve.** El borrador, los criterios y el resumen de la verificación (apoyo de las citas, cobertura, conformidad y pendientes). No vuelve a juzgar las citas.

## Decisiones

| | Decisión | Por qué |
| --- | --- | --- |
| R1 | El revisor no reescribe | Si el agente reescribe para subir la nota, esconde limitaciones e infla las fuentes (le pasó a PaperOrchestra) |
| R2 | Sin nota numérica | Una nota invita a perseguirla y da falsa seguridad |
| R3 | Llamada aparte, sin el contexto de la escritura | Que no se evalúe a sí misma |
| R4 | Criterios con cita literal cuando vienen de un documento | La misma garantía que la ficha de la convocatoria |
| R5 | `revista/` es opcional | Los artículos sin revista elegida usan los criterios genéricos |

Descartado: el banco de pruebas con artículos publicados (decisión del usuario, 2026-11-17).

## Verificación

- Pruebas con un modelo falso: criterios de cada origen, ficha de revista con cita inventada rechazada, borrador intacto tras la revisión, informe en Markdown.
- Prueba real con la memoria PID2026 y lectura del informe a mano.

## Siempre / Nunca

- Siempre: cada carencia señala el apartado; los `[PENDIENTE]` cuentan como información que falta.
- Nunca: reescribir el borrador, dar una nota, sugerir que se inventen datos o que se quiten limitaciones.

## Progreso

| Paso | Estado |
| --- | --- |
| Implementación (Codex) | Hecha |
| Prueba con la memoria PID2026 | Hecha (2026-11-17): 5 criterios evaluados, una llamada de 40 s, borrador intacto |
