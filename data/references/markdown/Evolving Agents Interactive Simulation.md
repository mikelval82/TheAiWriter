# Evolving Agents: Interactive Simulation of Dynamic and Diverse Human Personalities

## Metadata
- **Autores**: Jiale Li, Jiayang Li, Jiahao Chen, Yifan Li, Shijie Wang, Hugo Zhou, Minjun Ye, Yunsheng Su
- **Año**: 2024
- **Keywords**: Human-AI interaction, Human-Like agents, generative AI, large language models, cognitive psychology, personality psychology

## Abstract
El artículo presenta Evolving Agents, una arquitectura de agentes que integra dos sistemas: Personalidad (Emoción, Cognición y Crecimiento del Carácter) y Comportamiento (Plan y Acción). Inspirada en teorías psicológicas (conductismo, cognición y personalidad), la arquitectura permite que agentes encarnados muestren rasgos de personalidad diferenciados y comportamientos coherentes con esos rasgos, y que sus personalidades evolucionen dinámicamente a partir de información externa en un bucle de retroalimentación conducta–personalidad. Se implementa una plataforma de simulación tipo sandbox (Unity) donde los agentes interactúan con el entorno y entre sí. La evaluación incluye análisis objetivo (BFI-44 y similitud conductual) y estudios con usuarios (30 evaluadores), además de talleres con diseñadores. Los resultados apoyan que los agentes exhiben rasgos diferenciables, evolución perceptible de la personalidad y cambios conductuales coherentes, y que el sistema sirve como sonda de diseño para inspirar a diseñadores.

## Contribuciones Principales
- Presentación de Evolving Agents, un sistema interactivo que simula personalidades humanas diversas y dinámicas de manera perceptible y verosímil.
- Nueva arquitectura con dos subsistemas: Comportamiento (Plan y Acción) y Personalidad (Emoción, Cognición y Crecimiento del Carácter), que habilita comportamientos personalizados y evolución continua de la personalidad a partir de información externa.
- Procedimiento de evaluación mixto: verificación objetiva (BFI-44 y análisis de similitud conductual), evaluación humana con 30 participantes y talleres con diseñadores para explorar su valor como sonda de diseño.
- Plataforma sandbox editable (Unity) y mecanismos de interacción social y memoria de diálogo para profundizar conversaciones y estimular la evolución de personalidad.

## Metodología
Diseño de la arquitectura: a) Sistema de Comportamiento con Plan y Acción. Plan incorpora: Plan Característico (usa rasgos, conflictos y preferencias para alinear planes con la personalidad), Mecanismo basado en metas (categorías de metas como aprendizaje, relajación, ejercicio para motivaciones explícitas) y Post-procesado específico (p. ej., lógica de citas con invitación-respuesta y priorización). Acción ejecuta planes considerando el entorno (ocupación de objetos, replanificación), genera descripciones de acciones (LLM) y activa conversaciones con memoria de diálogo que profundiza temas progresivamente y selección abstracta de interlocutores según razones.
Sistema de Personalidad: b) Estructura de Carácter de cinco dimensiones (Información básica, Estado actual, Rasgos Big Five, Conflictos internos y Preferencias de comportamiento: meta última, metas a largo/corto plazo, rutinas, hobbies, lugares). Se usan dos versiones (completa y resumen) para eficiencia. c) Emoción: clasificación en 7 estados, evaluación subjetiva en primera persona y mecanismo de ajuste del plan cuando cambios emocionales cruzan umbrales (p. ej., salto de ≥3 en escala 0–7). d) Cognición: Memoria (corto plazo: todas las acciones y emociones; largo plazo: filtrado y resumen sesgado por rasgos y conflictos, con desvanecimiento por capacidad) e Insight (síntesis holística diaria basada en eventos, memorias y toda la estructura de carácter). e) Crecimiento del Carácter: actualización encadenada y trazable de Estado, Rasgos, Contradicciones y Preferencias mediante prompts precisos, integrando emociones e insights diarios.
Plataforma de simulación: Sandbox en Unity con estructura de entorno en tres niveles (edificio–lugar–meta) para describir objetos e interacciones a LLM; ejecución de acciones con A* y reglas de ocupación; edición de entorno vía CSV; opción de chat usuario–agente registrado en memoria de diálogo.
Evaluación objetiva: 1) Big Five (BFI-44) para tres agentes (Isabella, Benjamin, Sophia) durante 7 días, comparando arquitectura completa vs ablación sin Insight ni Crecimiento del Carácter (similar a Plan–Acción–Memoria–Reflexión). Se diseña un procedimiento de cumplimentación paralela enfocada en diferencias día a día para estabilizar respuestas. Se calcula Δoverall como media de diferencias absolutas interdiarias por dimensión. 2) Similitud conductual: se codifican planes diarios por conteo de categorías de metas y se calcula distancia euclídea entre días y un índice de actividad A (promedio de distancias interdiarias), comparando arquitectura completa vs ablación.
Evaluación humana: 30 evaluadores (18–34 años, ≥grado) leen logs textuales de 3 días de 3 agentes y 3 ablaciones + grupo humano. Se aplican: a) calificaciones de verosimilitud de diferencias y de trayectorias de crecimiento (escala 0–5; pruebas de Wilcoxon frente a neutral=3) y b) ranking de cuatro grupos experimentales (G1 completo; G2 sin Emoción cognitiva/Insight/Crecimiento; G3 simplificación adicional de la Estructura de Carácter; G4 humano), analizado con TrueSkill (μ, σ), Kruskal–Wallis y Dunn con Holm–Bonferroni.
Talleres: 9 diseñadores de múltiples disciplinas, observación de logs y lluvia de ideas; cuestionario Likert sobre capacidad inspiradora.

## Resultados Clave
- Big Five (7 días, 3 agentes): la ablación mostró Δoverall=0 en todas las dimensiones y agentes; la arquitectura completa presentó cambios activos: Benjamin Δoverall=4.37; Isabella=6.52; Sophia=6.77.
- Similitud conductual (índice de actividad A): Isabella 2.293 (completo) vs 1.416 (ablado); Benjamin 2.152 vs 1.742; Sophia 1.949 vs 1.474, indicando mayores variaciones de comportamiento con evolución de personalidad.
- Evaluación humana (n=30): verosimilitud de diferencias de personalidad y comportamiento T=11.0, p<0.001 (Wilcoxon contra mediana=3); verosimilitud de trayectoria de crecimiento T=11.5, p<0.001. Soporta las hipótesis de diferenciación percibida y evolución verosímil.
- Ablación (ranking TrueSkill): G1 μ=29.89, σ=1.61 (mejor); G2 μ=23.18, σ=1.13; G3 μ=22.95, σ=1.15; G4 humano μ=21.16, σ=1.18. Cohen’s d=5.33 (G1 vs resto). Dunn posthoc (Holm–Bonferroni): G1 difiere significativamente de G2, G3 y G4; no hay diferencias significativas entre G2–G4.
- Observación cualitativa: tendencia decreciente común en Neuroticismo (posible sesgo positivo de LLM); agentes con distintos rasgos muestran patrones de cambio diferenciados (p. ej., Sophia con variaciones más rápidas en Extraversión y Neuroticismo). 
- Talleres con diseñadores (n=9): el sistema genera ideas aplicables en diseño de espacios, narrativa y servicios; valoración positiva como sonda de diseño.

## Limitaciones
- Posible sesgo positivo de los LLM que empuja evoluciones hacia menor neuroticismo y trayectorias más “armoniosas”.
- Emociones simuladas tipo role-playing: dificultad para captar sutilezas, contradicciones y afectos complejos; emociones a veces excesivamente positivas o confusas.
- Horizonte temporal corto de observación: los humanos reales muestran pocos cambios en periodos breves, dificultando comparaciones y percepción de antropomorfismo.
- Evaluaciones con pocos agentes para análisis objetivo (3) y entornos limitados; generalización a contextos más ricos no demostrada.
- Dependencia de prompts y de un modelo propietario (GPT-4/4-turbo); reproducibilidad y transparencia limitadas a pesar de la trazabilidad del flujo.
- Métricas centradas en BFI-44 y conteo de metas; faltan medidas conductuales más finas y triangulación multimodal.

## Trabajo Futuro
- Incluir trayectorias menos positivas (p. ej., estrés, recaídas), calibrando o debiasing de LLM para mayor realismo afectivo.
- Ampliar número de agentes, duración de simulaciones y variedad de entornos/tareas; incorporar señales multimodales y herramientas externas.
- Desarrollar métricas adicionales de evolución (p. ej., consistencia narrativa, redes sociales emergentes, análisis longitudinal) y validación con expertos en psicología.
- Investigar mecanismos de memoria más estructurados (event graphs, causalidad) y aprendizaje de preferencias más interpretable.
- Integración más estrecha con procesos de diseño (co-simulación, prototipado iterativo) y directrices éticas/UX para interacción humano–agente.
- Evaluar transferibilidad a dominios aplicados (salud mental, educación, juegos) con estudios controlados.

## Citas Relevantes
- "Evolving Agents can simulate the human personality evolution process."
- "Agents reflect on their behavior to reason and develop new personality traits."
- "These traits, in turn, generate new behavior patterns, forming a feedback loop-like personality evolution."
- "Agents that do not undergo continuous evolution seem to experience each day as one long moment, repeating itself repeatedly."
- "Evolving Agents, perceptible and believable simulacra of diverse and dynamic human personalities in the interactive simulation system."
- "We aim to enhance the proactivity of Agents in interacting with others, fostering more 'conscious' and 'prepared' social activities in the simulated world."
- "This straightforward strategy [...] demonstrates believable and dynamic planning capabilities."
- "Evolving Agents can construct agents with perceptible and believable differentiated personality traits."

## Notas Adicionales
El trabajo combina teoría psicológica (conductismo, cognición, Big Five, conflictos intrapersonales) con una arquitectura de agentes impulsada por LLM (GPT-4/-turbo) y un sandbox Unity. La interacción Plan–Acción–Emoción–Cognición–Crecimiento del Carácter genera un bucle de retroalimentación interpretable y trazable. Las ablaciones muestran que Insight y Crecimiento del Carácter son críticos para la evolución percibida y cambios conductuales. La edición del entorno vía CSV y la memoria de diálogo potencian estímulos y desarrollo social. Hallazgo curioso: el grupo humano fue percibido como menos antropomorfo por estabilidad y rutina, lo que sugiere ajustar horizontes y expectativas en estudios comparativos. Consideraciones éticas: evitar sobrereliance de diseñadores, mantener a humanos reales como referencia en investigación, y promover transparencia e interpretabilidad.
