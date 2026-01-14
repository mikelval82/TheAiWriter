# Designing Gaze Analytics for ELA Instruction: A User-Centered Dashboard with Conversational AI Support

## Metadata
- **Autores**: Eduardo Davalos, Yike Zhang, Shruti Jain, Namrata Srivastava, Trieu Truong, Nafees-ul Haque, Tristan Van, Jorge A. Salas, Sara McFadden, Sun-Joo Cho, Gautam Biswas, Amanda Goodwin
- **Año**: 2025
- **Keywords**: Gaze Analytics, Educational Technology, Learning Analytics, Conversational Agents, User-Centered Design

## Abstract
El trabajo presenta el diseño iterativo y la evaluación de un panel de analíticas de mirada (gaze) para la enseñanza de Lengua Inglesa (ELA), desarrollado con metodologías centradas en el usuario y principios de data storytelling. A través de cinco estudios con docentes y estudiantes, muestran que las analíticas de mirada pueden ser accesibles y pedagógicamente útiles cuando se apoyan en visualizaciones familiares (p. ej., heatmaps), explicaciones en capas y andamiajes narrativos. Además, integran un agente conversacional basado en un LLM que permite consultas en lenguaje natural sobre analíticas multimodales, reduciendo barreras de interpretación. Concluyen con implicaciones de diseño para integrar modalidades de datos novedosas en contextos de aula.

## Contribuciones Principales
- Demuestran, mediante cinco estudios con docentes y estudiantes, la viabilidad y utilidad pedagógica de analíticas de mirada en ELA.
- Aplican principios de data storytelling (resúmenes, leyendas, tooltips, estructura narrativa) para mejorar la interpretabilidad de dashboards de gaze.
- Integran un agente conversacional (LLM) que habilita interacciones en lenguaje natural con analíticas multimodales y genera reportes interpretables.
- Proponen principios de diseño: familiaridad (priorizar heatmaps), divulgación progresiva, personalización, ayudas narrativas, XAI y consulta bajo demanda.
- Ofrecen implicaciones para investigación en la intersección gaze–LLM–HCI y para la adopción de MMLA en aulas.

## Metodología
Enfoque de investigación: Design-Based Research (DBR) con User-Centered Design (UCD), iterando sobre prototipos Figma y evaluaciones con actores educativos.
- Estudio 1: Despliegue inicial en aula (mayo 2024)
  • Participantes: 1 docente (5.º grado) y 38 estudiantes (22 niños, 16 niñas) en escuela pública del sudeste de EE. UU.
  • Tarea: Prueba de comprensión lectora (~500 palabras) en el sistema RedForest con eye-tracking por webcam.
  • Instrumentos: Recolección en línea de datos de mirada; dashboard post-evaluación (v1) con heatmap del texto, tabla de desempeño por pregunta y gráfica de trayectoria de puntaje; cuestionario breve a estudiantes; entrevista de salida al docente.
  • Medidas: Percepciones de usabilidad, claridad y compromiso; interpretabilidad docente.
- Estudio 2: Entrevistas en profundidad (noviembre 2024)
  • Participantes: 4 docentes y 14 estudiantes (30 min, por Zoom).
  • Materiales: Prototipo de alta fidelidad (capturas de RedForest); guiones de entrevista diferenciados (docente/estudiante).
  • Objetivo: Identificar barreras de interpretación y necesidades de características (p. ej., leyendas, agrupamiento de estudiantes, resúmenes generados por IA).
- Estudio 3: Taller interactivo de co-diseño (en persona)
  • Participantes: 20 estudiantes y 4 docentes.
  • Materiales: Prototipo Figma interactivo (v2) con acordeones por pregunta, resúmenes de clase, heatmaps embebidos en PDF y chatbot contextual.
  • Protocolo: Observe → Action → Feedback; tareas sobre Course Overview, Assignment Editing/Activity y Post-Assessment Dashboard.
  • Objetivo: Validar interpretabilidad de visualizaciones (heatmap, scanpaths crudos y segmentados por comportamiento), estructura de interfaz, densidad informativa y utilidad del chatbot.
- Estudio 4: Reportes generados por LLM (febrero 2025)
  • Participantes: 5 docentes.
  • Pipeline: Agregación de datos de mirada, desempeño, texto de la tarea, ítems y estándares ELA; prompting a LLM para generar reportes con estado del aula, metas, clústeres conductuales, outliers y recomendaciones.
  • Evaluación: Encuesta Likert por sección y retroalimentación abierta.
- Estudio 5: Agente conversacional (junio 2025)
  • Participantes: 2 docentes.
  • Materiales: Dashboard con agente conversacional capaz de responder en lenguaje natural sobre gráficos, tendencias y métricas de mirada.
  • Objetivo: Usabilidad, interpretabilidad y confianza (trazabilidad, validación de respuestas).
Ética y datos: Protocolos IRB de Vanderbilt, consentimientos (incluyendo tutela), almacenamiento seguro de datos.

## Resultados Clave
- Estudio 1 (aula): 62% de estudiantes reportó no enfrentar desafíos significativos; 38% reportó dificultades menores (navegación, localización de elementos, fatiga visual, formato). 90% expresó opiniones positivas; 76% destacó el rastreo ocular como atractivo. El docente valoró el potencial para retroalimentación y adaptaciones instruccionales, pero señaló complejidad y sobrecarga informativa.
- Estudio 2 (entrevistas): Demanda fuerte de ayudas de interpretación: leyendas, descripciones de figuras, resúmenes por IA. Docentes solicitaron agrupamiento flexible (p. ej., ESL; niveles de dominio) y etiquetado personalizable.
- Estudio 3 (taller): Preferencia clara por heatmaps como visualización más intuitiva; scanpaths y segmentaciones conductuales percibidas como complejas sin andamiaje. Relevancia de principios de storytelling: títulos descriptivos, tooltips, resúmenes conductuales, vínculos a estándares/capacidades. Estudiantes prefirieron trayectorias personales y recomendaciones específicas; docentes pidieron estructura top-down (resumen de clase → detalles), mejor tipografía/legibilidad, zoom y control de anotaciones.
- Estudio 4 (reportes LLM): Docentes evaluaron positivamente estructura y relevancia pedagógica de secciones (estado, clústeres conductuales, alineación a estándares, recomendaciones). Señalaron verbosidad y pidieron resúmenes breves y escaneables.
- Estudio 5 (agente): El agente facilitó la interpretación de visualizaciones y métricas de mirada mediante preguntas en lenguaje natural. Preocupaciones sobre confiabilidad y verificación de afirmaciones; demanda de trazabilidad a datos/figuras y capacidades de análisis bajo demanda (p. ej., agrupar por criterios, generar visualizaciones ad hoc).
- Síntesis RQ1–RQ3: RQ1: Gaze es percibido como valioso y accionable, pero requiere soporte interpretativo. RQ2: Data storytelling mejora usabilidad y utilidad pedagógica (personalización, explicaciones contextuales, divulgación progresiva). RQ3: El agente conversacional reduce carga interpretativa, siempre que ofrezca transparencia, verificación y XAI.

## Limitaciones
- Tamaños muestrales modestos (especialmente en entrevistas y pruebas del agente), limitando generalización.
- Eye-tracking por webcam menos preciso que equipos de laboratorio; limita granularidad de rasgos de mirada.
- Fiabilidad de salidas LLM variable; riesgo de opacidad y alucinaciones sin mecanismos de verificación.
- Evaluaciones centradas en usabilidad/interpretabilidad percibida; falta evidencia longitudinal de impacto en aprendizaje o práctica docente.

## Trabajo Futuro
- Estudios longitudinales para medir efectos en resultados de comprensión y cambios en práctica pedagógica.
- Integración robusta de XAI: trazabilidad a fuentes, indicadores de confianza, citación de visualizaciones/subconjuntos de datos.
- Capacidades de análisis bajo demanda en el agente (definir grupos personalizados, generar comparativas y visualizaciones a pedido).
- Mejores andamiajes de alfabetización visual (tutoriales, walkthroughs, tooltips guiados) y etiquetado de contenido/competencias.
- Implementaciones a escala en aulas diversas y evaluación de uso en tiempo real durante la instrucción.
- Refinar visualizaciones avanzadas (p. ej., scanpaths segmentados) con explicaciones pedagógicas y control de complejidad.

## Citas Relevantes
- "Our findings demonstrate that gaze analytics can be approachable and pedagogically valuable when supported by familiar visualizations, layered explanations, and narrative scaffolds."
- "We further show how a conversational agent, powered by a large language model (LLM), can lower cognitive barriers to interpreting gaze data by enabling natural language interactions with multimodal learning analytics."
- "RQ1: Would teachers and students find gaze-based analytics approachable and capable of offering actionable insights?"
- "RQ2: How can we apply data storytelling principles to the design of gaze analytics tools for ELA instruction?"
- "RQ3: Could the use of a conversational agent assist in the navigation and interpretation of gaze data within an analytics dashboard?"
- "Heatmaps emerged as the most intuitive and well-received gaze visualization across both groups."
- "Teachers requested a mechanism to validate agent outputs and suggested the possibility of using the agent to conduct on-demand analysis in natural language, such as defining custom student groups or generating custom visualizations based on user-defined criteria."

## Notas Adicionales
Artículo orientado a IUI ’26 (31st International Conference on Intelligent User Interfaces); disponible también en arXiv:2509.03741 (3 Sep 2025). Se apoya en RedForest para tareas y captura de mirada. El proceso de diseño utilizó Figma como artefacto central de co-diseño. El panel final (v3) integra reportes de clase y estudiante con analíticas multimodales y un agente conversacional. Incluye declaración de uso de GenAI (GitHub Copilot para co-escritura de código). Las implicaciones de diseño enfatizan familiaridad (heatmaps), divulgación progresiva, personalización y XAI para construir confianza en agentes LLM.
