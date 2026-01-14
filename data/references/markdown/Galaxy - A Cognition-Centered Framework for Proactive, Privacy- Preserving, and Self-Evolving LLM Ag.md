# Galaxy: A Cognition-Centered Framework for Proactive, Privacy-Preserving, and Self-Evolving LLM Agents

## Metadata
- **Autores**: Chongyu Bao, Ruimin Dai, Yangbo Shen, Runyang Jian, Jinghan Zhang, Xiaolan Liu, Kunpeng Liu
- **Año**: 2025
- **Keywords**: LLM agents, asistentes personales inteligentes, proactividad, privacidad, metacognición, auto-evolución, arquitectura cognitiva, Cognition Forest, KoRa, Kernel, Spaces, Agenda, Persona, Privacy Gate

## Abstract
El trabajo presenta Galaxy, un marco de agentes LLM diseñado para asistentes personales inteligentes (IPA) que combina proactividad, preservación de la privacidad y auto-evolución. Propone Cognition Forest, una estructura semántica en forma de bosque de subárboles que integra arquitectura cognitiva y diseño de sistema en un bucle de refuerzo mutuo. Sobre esta base, implementa dos agentes cooperativos: KoRa (agente generativo con pipeline cognición→acción para habilidades reactivas y proactivas) y Kernel (meta-agente metacognitivo que supervisa, protege la privacidad mediante Privacy Gate y impulsa la auto-evolución). Galaxy soporta interacciones multidimensionales vía módulos Spaces, y realiza modelado de usuario a corto y largo plazo mediante Agenda y Persona. En evaluaciones públicas (AgentBoard, PrefEval y PrivacyLens) Galaxy supera varios referentes del estado del arte; los estudios de ablación y casos reales demuestran mejoras en consistencia, retención de preferencias y gestión de privacidad.

## Contribuciones Principales
- Propuesta de Cognition Forest, una estructura semántica que integra arquitectura cognitiva y diseño de sistema, habilitando un bucle de co-optimización.
- Diseño del marco Galaxy para ejecución proactiva de tareas, preservación de privacidad y adaptación continua.
- Implementación de dos agentes cooperativos: KoRa (asistente generativo cognición→acción) y Kernel (meta-agente metacognitivo para estabilidad, privacidad y auto-evolución).
- Validación empírica que muestra mejoras frente a benchmarks SOTA, con análisis de ablación y casos de interacción del mundo real.

## Metodología
Galaxy se organiza en tres capas (Percepción/Interacción, Análisis, Ejecución) y un meta-agente externo (Kernel), todo ello unificado por Cognition Forest.
- Cognition Forest: Bosque estructurado F = {Tuser, Tself, Tenv, Tmeta} que asocia cada nodo a tres dimensiones: Semantic (significado), Function (mapeo funcional) y Design (implementación de código). Une la cognición (qué y cómo hacer) con el diseño del sistema (cómo está implementado), extendiendo la metacognición más allá de arquitecturas cognitivas tradicionales.
- Spaces (protocolo de interacción): Encapsulan fuentes heterogéneas en módulos cognoscibles e interactuables, cada uno como subárbol en F y contenedor local de ejecución. Componentes: (1) Perception Window (observa acciones y señales, convierte en TimeEvent y snapshots temporales), (2) Interaction Component (UI y nodos de interacción para usuario y KoRa), (3) Cognitive Protocol (estándar de desarrollo para traducir intenciones en operaciones del sistema e incrustar el Space en F).
- Modelado de usuario: Agenda usa TimeEvent para Schedules explícitos y Behaviors observados (triple tiempo/herramienta/intent semántico), clusteriza patrones (Behavior Patterns) y sugiere planes diarios para confirmación del usuario. Persona mantiene el User Cognition Tree (Tuser) como insights semánticos agregados (con embeddings), promueve nodos estables, fusiona y decae nodos según uso; registra identidad estable.
- KoRa (agente generativo): Arquitectura tipo Generative Agents con memoria, planificación, reflexión y un state stack estructurado para manejar interrupciones. Mantiene FKoRa = {Tuser, Tself^KoRa, Tenv^KoRa, Tdialogue}. Pipeline cognición→acción: (1) Enrutamiento semántico por el bosque según la intención M; (2) Recuperación de nodos relevantes en los subárboles; (3) Construcción de cadenas de acción (generación de contenido, alineación de intenciones, invocación de funciones de sistema, respuestas en lenguaje natural). Si faltan parámetros o evidencia, suspende y alinea con el usuario antes de reanudar.
- Kernel (meta-agente): Mantiene Tmeta para supervisar razonamientos, detectar fallos y ajustar tanto la lógica funcional como dependencias arquitectónicas. Tres mecanismos: (1) Oversee (monitorización continua de pipelines y LLM calls, meta-reflexión y rutinas de recuperación), (2) User-Adaptive System Design (identifica necesidades latentes, confirma y modifica/expande Spaces; cuenta con intérprete local de código y motor de reglas, operativo offline), (3) Contextual Privacy Management mediante Privacy Gate (máscaras L1–L4 sobre atributos sensibles antes del envío a la nube y desmascarado selectivo a la vuelta). Kernel también mantiene un Autonomous Avatar alineado con Tuser.
- Bucle de co-optimización cognición↔diseño: Comprensión guiada por la cognición → reflexión sobre límites de capacidad → traducción a objetivos de diseño e implementación de nuevas capacidades → nuevo diseño refuerza y enriquece la arquitectura cognitiva.
- Ejemplo real: Detecta uso repetido de traducción en horario laboral; alinea requisitos con el usuario; genera automáticamente un Space de traducción y lo despliega proactivamente en los periodos habituales.

## Resultados Clave
- Benchmarks: Galaxy y Galaxy (w/o Kernel) superan a múltiples agentes SOTA en AgentBoard, PrefEval y PrivacyLens.
- Impacto de Kernel: retención de preferencias mejora de 11.0% a 94.0% (PrefEval, condición zero-shot) y la filtración de privacidad baja de 50.5% a 18.5% (PrivacyLens) gracias a Privacy Gate y al mantenimiento evolutivo de Cognition Forest.
- Coste y latencia: con Kernel=Qwen2.5-14B y KoRa=GPT-4o-mini, la extracción de intención one-shot alcanza 81.5% de éxito; latencia desglosada en una llamada compleja: 1.34 s total, con 0.87 s dedicados a recuperación cognitiva por Kernel (paso dominante para seleccionar y fundamentar acciones de herramienta).
- Sensibilidad al tamaño del modelo: tareas simples dominadas por inferencia local; en tareas complejas predomina la inferencia en la nube; los modelos más grandes mejoran la tasa de éxito pero incrementan la latencia (hasta 6.3 s en Space Design con 14B local).
- Estudio de caso: Kernel diagnosticó y resolvió un ModuleNotFoundError (PYTHONPATH) fuera del entrypoint principal, restaurando la ejecución sin intervención humana.
- Ablación: sin Agenda, planes menos estructurados y mayor dependencia de realimentación; sin Persona, KoRa interpreta erróneamente la continuidad del hábito de traducción. La capa de Análisis (Agenda+Persona) integra señales heterogéneas y estabiliza la asistencia proactiva.

## Limitaciones
- Riesgo de overfitting de alineación: señales de alineación de corto plazo pueden sobreponderarse frente a hábitos de largo plazo.
- Expansión de Spaces dependiente de humanos: la automatización existe, pero Spaces complejos requieren múltiples rondas de guía humana.
- Errores en cadenas de ejecución: fallos por parámetros incompletos, secuencias incorrectas o errores de implementación pueden persistir pese a la supervisión de Kernel.
- Trade-offs entre privacidad y utilidad: el enmascaramiento puede eliminar señales útiles si se aplica con niveles altos (L3–L4).
- Dependencia de modelos locales y de nube: modelos locales pueden alucinar; la inferencia en la nube introduce latencia y consideraciones de exposición de datos.

## Trabajo Futuro
- Mecanismos de regularización para evitar el sobreajuste de alineación (p. ej., suavizado temporal y priorización probabilística de hábitos persistentes).
- Mayor automatización en la generación y verificación de Spaces complejos (herramientas de testing y síntesis programática guiada por especificaciones).
- Evaluaciones end-to-end más amplias y longitudinales, incluyendo escenarios multi-usuario y multi-dispositivo.
- Integración de salvaguardas formales en Privacy Gate (políticas verificables y auditorías reproducibles).
- Optimización de latencia con planificación híbrida local–nube y cachés cognitivos/funcionales en Kernel.

## Citas Relevantes
- "We propose the Cognition Forest, a semantic structure that integrates cognitive architecture with system design."
- "We take a step forward of IPAs by arguing that an agent’s understanding of its users should not be constrained by a fixed cognitive architecture, but should evolve through continuous reflection on and refinement of its own system design."
- "Cognition Forest F is an structured forest consisting of four subtrees F = {Tuser, Tself, Tenv, Tmeta}."
- "Kernel maintains an Autonomous Avatar aligned with the User Cognition Tree to represent user context, and regulates data exposure through an LLM-based Privacy Gate."
- "This reveals a key insight for design of LLM agents: cognitive architecture and system design are co-constructive—evolving requirements from cognition drive system design advancements, while improved system design in turn enriches cognition."

## Notas Adicionales
Repositorio de código: https://github.com/Kilo377/GalaxyIPA. El artículo (arXiv:2508.03991, 6 Aug 2025) enfatiza la integración profunda entre cognición y diseño de sistema, materializada en Cognition Forest y operacionalizada por KoRa y Kernel. Las métricas clave reportadas incluyen grandes ganancias con Kernel en retención de preferencias y reducción de filtraciones de privacidad. Los experimentos se ejecutan en macOS con M3 Max, Kernel local Qwen2.5-14B y KoRa en la nube con GPT-4o-mini. Algunas columnas detalladas de tablas de benchmarks no se describen por completo en el texto, pero las conclusiones principales están respaldadas por comparativas y el análisis cualitativo.
