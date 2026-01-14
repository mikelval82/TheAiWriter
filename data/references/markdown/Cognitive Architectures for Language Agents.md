# Cognitive Architectures for Language Agents

## Metadata
- **Autores**: Theodore R. Sumers, Shunyu Yao, Karthik Narasimhan, Thomas L. Griffiths
- **Año**: 2024
- **Keywords**: cognitive architectures, language agents, large language models, CoALA, memoria, grounding, recuperación, razonamiento, aprendizaje, planificación, toma de decisiones, production systems, Soar

## Abstract
El trabajo propone CoALA, un marco conceptual inspirado en la ciencia cognitiva y la IA simbólica para diseñar y analizar agentes de lenguaje. CoALA especifica agentes con memorias modulares, un espacio de acciones estructurado (acciones internas y externas) y un procedimiento general de toma de decisiones para elegir acciones. El marco permite organizar retrospectivamente una gran cantidad de trabajos recientes y señalar direcciones prácticas hacia agentes más capaces y generalistas, contextualizando a los agentes de lenguaje dentro de la historia más amplia de la IA.

## Contribuciones Principales
- Propone CoALA, una arquitectura cognitiva para agentes de lenguaje con tres ejes: memoria (trabajo y largo plazo), acciones (internas y externas) y toma de decisiones (planificación y ejecución).
- Establece una analogía formal entre sistemas de producción y LLMs, y muestra cómo principios de arquitecturas cognitivas clásicas (p. ej., Soar) guían el diseño de agentes basados en LLM.
- Unifica y organiza la literatura reciente de agentes bajo CoALA, clarificando terminología y comparando mecanismos internos.
- Presenta estudios de caso (SayCan, ReAct, Voyager, Generative Agents, Tree of Thoughts) mapeados al marco para ilustrar similitudes y diferencias.
- Ofrece recomendaciones prácticas y acciones concretas para construir agentes modulares (memoria, razonamiento estructurado, decisión deliberativa, seguridad del espacio de acciones).
- Identifica vacíos y oportunidades (p. ej., recuperación adaptativa, aprendizaje de procedimientos y del propio proceso de decisión, borrado/desaprendizaje) y plantea preguntas abiertas.

## Metodología
Metodología predominantemente conceptual y de síntesis teórica: (1) contextualiza sistemas de producción y arquitecturas cognitivas (con énfasis en Soar) como antecedentes; (2) desarrolla la analogía LLM ↔ sistemas de producción (LLMs como sistemas de producción probabilísticos) y el encadenamiento de prompts como flujo de control; (3) define CoALA con módulos de memoria (trabajo, episódica, semántica, procedimental), acciones internas (recuperación, razonamiento, aprendizaje) y externas (grounding), y un ciclo de decisión con planificación (propuesta, evaluación, selección) y ejecución; (4) organiza y revisa trabajos existentes mapeándolos a estos componentes; (5) profundiza en estudios de caso para mostrar cómo CoALA describe agentes reales; (6) deriva recomendaciones prácticas y líneas de investigación futuras (modularización, integración de planificación basada en código, metarazonamiento, seguridad y calibración).

## Resultados Clave
- Formalización de CoALA como arquitectura cognitiva para agentes de lenguaje, con diagramas de módulos y ciclo de decisión.
- Demostración de que múltiples agentes recientes se expresan limpiamente bajo el marco (tabla comparativa y cinco estudios de caso), facilitando comparación y diseño.
- Evidencia conceptual de que acciones internas (razonamiento, recuperación, aprendizaje) complementan y mejoran las acciones externas (grounding) en la toma de decisiones.
- Propuestas de diseño accionables: agentes modulares, razonamiento estructurado más allá del prompt engineering, memoria a largo plazo que escribe y lee (más allá de RAG), aprendizaje como acción de primera clase, seguridad del espacio de acciones y decisión deliberativa (proponer–evaluar–seleccionar).
- Identificación de vacíos (p. ej., aprendizaje de recuperación, actualización de código del agente, unlearning) y de desafíos clave (calibración, alineación, límites interno/externo, costes computacionales del razonamiento).

## Limitaciones
- Trabajo principalmente conceptual, sin evaluación cuantitativa unificada ni nuevos benchmarks experimentales.
- Dependencia de LLMs opacos y probabilísticos, lo que dificulta el análisis y el control fino del comportamiento.
- Componentes críticos como aprendizaje de procedimientos de recuperación y de la propia decisión, así como borrado/modificación de memoria, están poco explorados en agentes actuales.
- Consideraciones de seguridad y alineación se discuten a nivel de recomendaciones, no como soluciones validadas.
- La frontera entre acciones internas y externas puede ser ambigua en entornos digitales, afectando el diseño y la evaluación.

## Trabajo Futuro
- Implementar marcos y bibliotecas modulares estandarizados (clases de Memory, Action, Agent) y benchmarks para CoALA.
- Integrar razonamiento en lenguaje con planificación basada en código y simulación; extender búsqueda deliberativa (ToT/MCTS) a tareas con grounding y memoria de largo plazo.
- Desarrollar metarazonamiento para asignar cómputo adaptativamente y mejorar eficiencia; mejorar calibración y alineación para decisiones fiables.
- Aprendizaje autónomo de procedimientos (mejor recuperación, prompts, habilidades de grounding) y fine-tuning selectivo de submodelos para subtareas.
- Habilitar escritura, modificación y borrado en memorias a largo plazo; estudiar mecanismos de unlearning seguros.
- Diseñar y auditar espacios de acción seguros, con protocolos de intervención humana y controles de riesgos.
- Explorar agentes multimodales (LLMs vs VLMs) y el impacto de LLMs más potentes y contextos más largos en la necesidad de memoria y planificación.

## Citas Relevantes
- "CoALA describes a language agent with modular memory components, a structured action space to interact with internal memory and external environments, and a generalized decision-making process to choose actions."
- "Taken together, CoALA contextualizes today’s language agents within the broader history of AI and outlines a path towards language-based general intelligence."
- "LLMs can thus be viewed as probabilistic production systems that sample a possible completion each time they are called."
- "CoALA organizes agents along three key dimensions: their information storage...; their action space...; and their decision-making procedure..."
- "Language agents move beyond pre-defined prompt chains and instead place the LLM in a feedback loop with the external environment."
- "Present agents have just scratched the surface of more deliberate, propose-evaluate-select decision-making procedures."

## Notas Adicionales
El paper combina una teoría organizadora con una revisión extensa de agentes LLM, conectando IA simbólica (productions, Soar) con prácticas actuales (prompt chaining, RAG, herramientas). Introduce una definición clara de memoria de trabajo como estructura persistente entre llamadas LLM y distingue acciones internas/externas, elevando la recuperación, el razonamiento y el aprendizaje a acciones explícitas. Los estudios de caso muestran cómo CoALA normaliza comparaciones entre agentes con diferentes memorias y procedimientos de decisión. El trabajo enfatiza modularidad, seguridad del espacio de acciones y decisión deliberativa como palancas clave para avanzar hacia agentes más capaces y alineados.
