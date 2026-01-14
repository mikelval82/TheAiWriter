# Applying Cognitive Design Patterns to General LLM Agents

## Metadata
- **Autores**: Robert E. Wray, James R. Kirk, John E. Laird
- **Año**: 2025
- **Keywords**: Agents, Cognitive Architecture, Large Language Models, Agentic LLM Systems, Cognitive Design Patterns, Episodic Memory, Knowledge Compilation

## Abstract
El artículo propone usar "patrones de diseño cognitivo" (mecanismos y representaciones recurrentes en arquitecturas cognitivas como ACT-R, Soar y BDI) para analizar y guiar el desarrollo de sistemas agentivos basados en LLM. Mapea patrones clásicos (p. ej., observar-decidir-actuar, memoria episódica, memoria semántica, descomposición jerárquica, memoria de contexto, conocimiento procedimental y compilación de conocimiento) a técnicas y marcos recientes de LLM-agentes. Profundiza en dos casos: ReAct como instancia parcial del patrón observar-decidir-actuar (sin compromiso explícito) y Generative Agents como aproximación parcial a la memoria episódica (con carencias en especificidad de codificación y recuperación deliberada). Identifica patrones subexplorados pero prometedores para LLM-agentes (reconsideración/compromiso y compilación de conocimiento) y sugiere un patrón potencialmente novedoso (reflexión paso a paso). Concluye que esta perspectiva comparativa puede revelar brechas actuales y orientar investigación hacia agentes LLM más generales y robustos.

## Contribuciones Principales
- Introduce y formaliza la noción de "patrones de diseño cognitivo" como unidad funcional abstracta para comparar arquitecturas y agentes LLM.
- Compila ejemplos canónicos de patrones (Tabla 1) y los mapea a sistemas agentivos LLM contemporáneos (Tabla 2), mostrando su amplia presencia.
- Estudio de caso 1: Mapea ReAct al patrón observar-decidir-actuar, señalando la ausencia de un paso de compromiso explícito y planteando la hipótesis de mejora al incorporarlo.
- Estudio de caso 2: Compara la memoria de Generative Agents con requisitos de una memoria episódica computacional, identificando coincidencias y vacíos (p. ej., especificidad de codificación, recuperación deliberada, segmentación episódica).
- Señala dos patrones relevantes pero poco explorados en LLM-agentes: reconsideración de compromisos/intenciones y compilación de conocimiento, y discute su potencial para reducir coste computacional y mejorar control.
- Propone la "reflexión paso a paso" como patrón emergente, diferenciándola de reconsideración, autocorrección y metacognición clásica.
- Deriva predicciones e interrogantes empíricos concretos (p. ej., efectos de añadir compromiso a ReAct; cómo cambia el comportamiento con triggers de recuperación más contextuales).

## Metodología
Análisis comparativo y conceptual, sin experimentación empírica directa. La metodología comprende:
- Revisión de literatura sobre arquitecturas cognitivas (ACT-R, Soar, BDI) y síntesis de funciones/representaciones recurrentes como patrones de diseño cognitivo.
- Selección de patrones clave y abstracción funcional (separando roles funcionales de implementaciones algorítmicas específicas) para facilitar comparaciones cruzadas.
- Mapeo de dichos patrones a técnicas y marcos de LLM-agentes recientes (p. ej., ReAct, Tree/Graph of Thoughts, Voyager, MemGPT, MemoryBank), resumidos en una tabla ilustrativa (Tabla 2).
- Dos estudios de caso cualitativos: (1) ReAct frente al patrón observar-decidir-actuar y la cuestión del compromiso; (2) evaluación de la memoria de Generative Agents frente a criterios de memoria episódica (adaptados de Nuxoll & Laird, 2012), detallando aprendizajes, recuperación y especificidad de codificación (Tabla 3).
- Identificación de patrones subexplorados (reconsideración, compilación de conocimiento) y de un patrón emergente (reflexión paso a paso), con discusión de implicaciones computacionales y de control (p. ej., coste de LRMs, utilidad/gestión de memoria).

## Resultados Clave
- Múltiples patrones cognitivos clásicos ya están presentes en LLM-agentes (p. ej., descomposición jerárquica, memorias de contexto/semántica/episódica, conocimiento procedimental).
- ReAct implementa una forma de observar-decidir-actuar pero carece de un paso explícito de compromiso/reconsideración; se plantea que incorporar compromiso podría mejorar el rendimiento y la robustez.
- Generative Agents satisface parcialmente criterios de memoria episódica (p. ej., autobiográfica, variabilidad de longitud, recuperación automática), pero no cumple otros (segmentación episódica flexible, recuperación deliberada, especificidad de codificación plena), lo que sugiere rutas de mejora.
- Patrones poco explorados, como reconsideración y compilación de conocimiento, son prometedores para abordar limitaciones de control y coste computacional en LLM-agentes y LRMs.
- La reflexión paso a paso emerge como patrón distinto que combina evaluación iterativa de respuestas con posibles bucles de reflexión, diferente de autocorrección externa y metarrazonamiento clásico.
- Predicción: la adopción de compromiso/reconsideración y de compilación de conocimiento en línea podría reducir coste de inferencia, mejorar adaptabilidad y fiabilidad en sistemas agentivos LLM.

## Limitaciones
- Análisis no exhaustivo; la selección de patrones y sistemas es ilustrativa, no sistemática.
- Enfoque cualitativo y conceptual sin validación empírica directa de las hipótesis/predicciones.
- Posibles sesgos hacia arquitecturas familiares a los autores (Soar, BDI, ACT-R) y ejemplos conocidos en la comunidad de LLM-agentes.
- Rápida evolución del área puede dejar fuera trabajos recientes o alternativos.
- No se especifican algoritmos concretos ni evaluaciones cuantitativas para las propuestas (p. ej., cómo implementar compromiso con garantías).

## Trabajo Futuro
- Evaluar empíricamente la incorporación de compromiso y reconsideración en marcos tipo ReAct/LangGraph y su impacto en tareas de razonamiento y actuación.
- Implementar recuperación episódica con especificidad de codificación y construcción deliberada de claves, además de segmentación episódica adaptable.
- Desarrollar compilación de conocimiento en línea (incluida en lenguaje natural y en estructuras ejecutables) con mecanismos de utilidad/expresión controlada para evitar explosión de memoria.
- Diseñar métricas y benchmarks para reflexiones paso a paso, estableciendo límites y criterios de parada para evitar recursividad no acotada.
- Integrar patrones de planificación y descomposición con ciclos explícitos de compromiso/abandonos para mejorar redirección no monótona.
- Estudiar la reducción de coste de inferencia en LRMs mediante compilación y cacheo selectivo, y estrategias de recuperación eficientes.
- Avanzar hacia una disciplina de Arquitectura Cognitiva Comparada que sistematice patrones, mapeos y guías de diseño para AGI con modelos fundacionales.

## Citas Relevantes
- "This paper outlines a few recurring cognitive design patterns that have appeared in various pre-transformer AI architectures."
- "By examining and applying these recurring patterns, enables predictions of gaps or deficiencies in today’s Agentic LLM Systems and identification of subjects of future research towards general intelligence using generative foundation models."
- "Cognitive design patterns represent a similar concept."
- "ReAct replicates a subset of the common observe-decide-act pattern."
- "The developers of Generative Agents do not describe its long-term memory as an episodic memory but it is often cited as an example of episodic memory using LLMs."
- "An exhaustive survey for each of these questions is too broad for a conference paper and, given the accelerating pace of exploration of these topics, somewhat impractical."
- "As LLM Agents make deliberate, explicit commitments, they will then also need to decide if/when those commitments should be abandoned, just as traditional agents do."
- "Given these trends, the knowledge compilation design pattern appears directly relevant to Agentic LLMs and LRMs."
- "step-wise reflection appears to be a novel pattern that integrates and combines aspects of other patterns in a unique way, driven by the need for continual and fine-grained (step-wise) assessment of LLM-driven reasoning."
- "We presented cognitive design patterns as a powerful analytic tool for organizing and understanding the explosion of research in Agentic LLM systems."

## Notas Adicionales
El artículo se centra en sistemas agentivos compuestos principalmente por LLMs (no integraciones híbridas profundas con planificadores/solvers), aunque reconoce trabajos híbridos. Incluye tres tablas: (1) patrones con ejemplos en ACT-R, Soar y BDI; (2) mapeo de patrones a sistemas LLM; (3) criterios de memoria episódica comparados con Generative Agents. Destaca implicaciones computacionales de LRMs (o1, DeepSeek R1) y la necesidad de amortizar el coste de razonamiento mediante compilación y cacheo. Diferencia la reflexión paso a paso de self-consistency, autocorrección con feedback externo y metacognición de largo horizonte (p. ej., Reflexion). Propone que patrones funcionales, independientemente de su correspondencia con cognición humana, pueden acelerar el diseño de agentes LLM hacia capacidades más generales, y aboga por una metodología comparativa integrada que complemente la investigación de implementación arquitectónica.
