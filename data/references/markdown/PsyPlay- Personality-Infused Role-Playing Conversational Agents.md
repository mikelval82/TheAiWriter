# PsyPlay: Personality-Infused Role-Playing Conversational Agents

## Metadata
- **Autores**: Tao Yang, Yuhua Zhu, Xiaojun Quan, Cong Liu, Qifan Wang
- **Año**: 2025
- **Keywords**: role-playing conversational agents, LLMs, personalidad, Big Five, AutoGen, GPT-3.5, Higgs-Llama-3 70B, RLHF, evaluación con LLM, detección de personalidad, generación de diálogos, PsyPlay-Bench

## Abstract
El trabajo introduce PsyPlay, un marco de generación de diálogos que infunde rasgos de personalidad (Big Five) en agentes conversacionales basados en LLM. PsyPlay crea roles con atributos y experiencias consistentes con rasgos de personalidad, extrae temas realistas desde un corpus de estrés humano y genera diálogos multi-turno entre agentes usando AutoGen. La validez se comprueba con un back-testing automático de personalidad (vía GPT-3.5) que detecta la personalidad expresada en los diálogos y la compara con los rasgos predefinidos, logrando una tasa de éxito global del 80.31% con GPT-3.5. El estudio observa que LLMs alineados con valores positivos representan mejor personalidades positivas que negativas. Se libera PsyPlay-Bench, un corpus de 4745 diálogos correctamente interpretados para investigación en role-playing personalizado y detección de personalidad.

## Contribuciones Principales
- Propone PsyPlay, un marco de tres etapas (creación de tarjetas de rol, extracción de temas, generación de diálogos) para infundir rasgos de personalidad en agentes LLM.
- Introduce un método de back-testing automático de personalidad basado en LLM (GPT-3.5) que evalúa rasgos expresados en diálogos, evitando sesgos de autoinforme.
- Construye el corpus PsyPlay-Bench con 4745 diálogos correctamente interpretados, útil como tarea de instrucción y conjunto de evaluación para personalidad en diálogos.
- Evidencia empíricamente que la alineación con valores positivos (p. ej., por RLHF) favorece la representación de rasgos positivos y perjudica la de rasgos negativos.
- Análisis ablatorios que muestran el valor complementario de inyectar rasgos explícitos y experiencias personalizadas en los prompts.
- Estudios sobre el efecto de la intensidad del rasgo (a bit/very/extremely) y el número de turnos en la fidelidad de la personalidad.
- Evaluación en múltiples LLMs (GPT-3.5, Higgs-Llama-3 70B, Gemma-2-27b-it, Llama-3.1-405b-instruct), mostrando que backbones más potentes mejoran el desempeño.

## Metodología
PsyPlay consta de tres etapas:
1) Creación de tarjetas de rol: Se muestrean combinaciones de rasgos Big Five (Agreeableness, Conscientiousness, Extraversion, Neuroticism, Openness) del dataset WASSA 2022 (puntajes 1–7 mapeados a niveles: a bit, very, extremely). Se generan roles con atributos (nombre, género, edad) y experiencias coherentes con los rasgos. La inyección de personalidad se hace por dos vías: (i) rasgos explícitos en el prompt de diálogo; (ii) "shaping" mediante descriptores de personalidad (lista de 104 adjetivos para extremos alto/bajo por facetas) combinados con intensidad para redactar experiencias que refuercen el estilo del rol.
2) Extracción de temas: Se usa GPT-3.5 para extraer temas concisos y generalizables de Human Stress Prediction (con restricciones para evitar sesgos como edad/género). Se obtiene un conjunto de 161 temas sobre problemas reales (empleo, salud mental, relaciones, etc.).
3) Generación de diálogos: Se emplea AutoGen para orquestar diálogos multi-turno entre dos agentes. Los prompts obligan a: mantener estilo acorde a rasgos e intensidad, alinear el discurso con la experiencia del rol, no revelar que son LLM ni los rasgos, y respuestas naturales y concisas (≤30 palabras). Se usa una variante de prompt para turnos no iniciales.
Back-testing de personalidad: En lugar de cuestionarios de autopercepción, GPT-3.5 evalúa, a partir del contenido del diálogo y el tema, si el rol expresa alto/bajo/indeterminado en cada dimensión Big Five. Se compara con los rasgos predefinidos para computar tasas de éxito. Se valida la confiabilidad de GPT-3.5 frente a anotación humana en un subconjunto de 200 diálogos.
Construcción de PsyPlay-Bench: Se crean colecciones de rasgos (307 combinaciones), 132 tarjetas de rol y 161 temas. Se generan 8750 diálogos crudos (PsyPlay-Bench-Raw) y se dividen en: Eval (200), Test (550) y Clean (4745 tras filtrar fallos por back-testing). Evaluación en distintos LLMs con métrica de tasa de éxito de representación de rasgos preasignados.

## Resultados Clave
- Back-testing con GPT-3.5 vs humanos (PsyPlay-Bench-Eval): acuerdo global 88.01%; por rasgo: AGR 93.15%, CON 90.27%, EXT 79.02%, NEU 93.10%, OPN 81.63%.
- Desempeño de PsyPlay con GPT-3.5 (Test): éxito global 80.31%; por rasgo (overall): AGR 82.29%, CON 89.62%, EXT 73.83%, NEU 80.19%, OPN 74.87%.
- Sesgo positivo/negativo (GPT-3.5): éxito en roles positivos 90.71% vs negativos 61.57% (NEU tratado como rasgo invertido para comparación).
- Higgs-Llama-3 70B (sin alineación explícita de valores positivos): mejora en roles negativos (78.69%) y descenso en positivos (77.68%); global 78.04%.
- Otros LLMs (Apéndice F): Gemma-2-27b-it 80.64% y Llama-3.1-405b-instruct 85.77% (mejor desempeño global), corroborando que backbones más potentes ayudan.
- Ablaciones (GPT-3.5): quitar rasgos explícitos reduce negativos en −2.55 pts (59.02%) y apenas afecta positivos (−0.10); quitar experiencias reduce positivos en −2.63 (88.08%) y casi no afecta negativos (−0.18).
- Intensidad de rasgos: niveles altos ("very", "extremely") elevan notablemente el éxito (p. ej., positivos hasta ≈94.64% en "extremely"); "a bit" rinde peor.
- Número de turnos: más turnos benefician a personalidades positivas (más oportunidades de expresar rasgos) pero pueden desviar a negativas por influencia del interlocutor.
- Diversidad: además de los rasgos predefinidos, el back-testing detecta mezcla de otros rasgos (p. ej., roles de AGR también muestran CON), sugiriendo perfiles más ricos en los diálogos.

## Limitaciones
- Dependencia de la capacidad y alineación del LLM subyacente; la alineación hacia valores positivos dificulta representar rasgos negativos fielmente.
- El estudio se limita a diálogos entre dos personajes; no aborda interacciones multi-agente más complejas.
- Reglas de prompt (p. ej., límite de 30 palabras) pueden afectar la naturalidad/fluidez del diálogo.
- Temas provenientes de escenarios de salud psicológica podrían sesgar la manifestación de ciertos rasgos (EXT/OPN) y la evaluación.
- El back-testing automático depende de GPT-3.5 como juez, con desacuerdos residuales (especialmente en EXT y OPN).

## Trabajo Futuro
- Extender PsyPlay a diálogos multi-parte y escenarios colaborativos o competitivos.
- Mitigar el sesgo de alineación (p. ej., técnicas de de-biasing o modelos sin RLHF positivo) para mejorar la representación de rasgos negativos.
- Refinar prompts y reglas para equilibrar fidelidad de personalidad y fluidez conversacional.
- Diversificar fuentes y dominios de temas para reducir sesgos temáticos y mejorar cobertura de rasgos.
- Desarrollar evaluadores de personalidad más robustos (multi-juez LLM/humano, calibración por rasgo, control de longitud) y métricas continuas de intensidad.
- Publicar y ampliar PsyPlay-Bench con anotaciones adicionales (turnos, grados de rasgo, señales paralingüísticas).

## Citas Relevantes
- "We then propose PsyPlay, a dialogue generation framework that facilitates the expression of rich personalities among multiple LLM agents."
- "Validation on generated dialogue data demonstrates that PsyPlay can accurately portray the intended personality traits, achieving an overall success rate of 80.31% on GPT-3.5."
- "Notably, we observe that LLMs aligned with positive values are more successful in portraying positive personality roles compared to negative ones."
- "Moreover, we construct a dialogue corpus for personality-infused role-playing, called PsyPlay-Bench."
- "The use of GPT-3.5 for automatic back-testing proves to be an accurate method for evaluating role personality in dialogues."
- "Utilizing higher-level words such as 'very' and 'extremely' results in an elevated success rate of portrayal, whereas the lower-level word 'a bit' diminish the success rate in infusing personality."

## Notas Adicionales
Datos y recursos: 307 combinaciones únicas de personalidad; 132 tarjetas de rol; 161 temas; 8750 diálogos crudos; splits: Eval (200), Test (550), Clean (4745) tras filtrado por back-testing; diálogos con ~2.5 turnos y ~31 tokens por turno. Inyección de rasgos vía: (i) rasgos en prompt y (ii) experiencias redactadas con descriptores Big Five (104 adjetivos). Generación y orquestación con AutoGen. Back-testing: GPT-3.5 como evaluador por rasgo (alto/bajo/NS), NEU tratado como rasgo invertido para análisis positivo/negativo. Resultados por rasgo muestran mejor desempeño en CON/AGR/NEU y menor en EXT/OPN, posiblemente por sesgo temático. PsyPlay-Bench se liberará públicamente; uso previsto para entrenamiento (instrucción) y evaluación de personalidad en diálogo.
