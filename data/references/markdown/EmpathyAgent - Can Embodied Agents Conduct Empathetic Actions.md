# EmpathyAgent: Can Embodied Agents Conduct Empathetic Actions?

## Metadata
- **Autores**: Xinyan Chen, Jiaxin Ge, Hongming Dai, Qiang Zhou, Qiuxuan Feng, Jingtong Hu, Yizhou Wang, Jiaming Liu, Shanghang Zhang
- **Año**: 2025
- **Keywords**: empatía, agentes encarnados, benchmark, VirtualHome, evaluación de empatía, planificación de tareas, multimodal, LLM, VLM, RLHF, LoRA, HRI

## Abstract
El trabajo presenta EmpathyAgent, el primer benchmark para evaluar y potenciar acciones empáticas en agentes encarnados. Incluye 10,000 muestras multimodales (video, lenguaje y antecedentes del personaje) con planes y secuencias de acciones empáticas y menos empáticas. Define tres desafíos alineados con el proceso humano de empatía: comprensión del escenario, planificación empática y acciones empáticas ejecutables en VirtualHome. Propone una suite de métricas de evaluación de referencia (BLEU, ROUGE-L, CIDEr, SPICE, BERTScore; y Overlap, TF-IDF, LCS para acciones) y sin referencia (ocho dimensiones inspiradas en psicología y HRI). Los modelos actuales (GPT-4o, GPT-4-vision, LLaVA, etc.) aún muestran dificultades para realizar acciones empáticas concretas; sin embargo, el fine-tuning de Llama3-8B con EmpathyAgent mejora sustancialmente su comportamiento empático, alcanzando resultados comparables o superiores a GPT-4-turbo en varias configuraciones.

## Contribuciones Principales
- Presenta EmpathyAgent, un benchmark escalable de 10k muestras para evaluar y mejorar acciones empáticas de agentes encarnados, alineado con el proceso humano de empatía.
- Propone un marco de evaluación sistemático con métricas de referencia y sin referencia (ocho dimensiones inspiradas en psicología/HRI) para los tres pasos: comprensión del escenario, planificación y acciones ejecutables.
- Realiza un benchmarking de LLMs/VLMs (GPT-4o, GPT-4-vision, GPT-4-turbo, GPT-3.5, LLaVA, Qwen) y demuestra que el fine-tuning de Llama3-8B con EmpathyAgent mejora notablemente las acciones empáticas (superando a GPT-4-turbo en varias métricas y en preferencia humana/GPT).

## Metodología
Tarea y entradas/salidas: Dado un escenario (antecedentes del personaje, video de acciones y diálogo), el agente debe: (1) describir el escenario (comprensión), (2) planificar de forma empática (alto nivel), y (3) generar acciones empáticas ejecutables en VirtualHome (bajo nivel). Benchmark (10k pares; 9k train/1k test): Se construye sobre VirtualHome. Pipeline de generación: (a) Generación de escenarios: i) pool de personajes (personalidad, profesión, hobbies, relaciones, experiencias), ii) pool de secuencias de acciones de entrada, iii) creación del escenario y diálogo con GPT-4-turbo usando RAG con EmpatheticDialogues para diversidad. (b) Generación de respuestas empáticas: para cada escenario se recuperan 2 ejemplos de EmpatheticDialogues y se generan 2 secuencias de acciones; selección de la más empática mediante ejemplos con preferencia humana y GPT-4o (con explicación). Evaluación: Métricas de referencia para comprensión y planificación (BLEU1–4, ROUGE-L, CIDEr, SPICE, BERTScore); para acciones (Overlap, TF-IDF, LCS). Métricas sin referencia: ocho dimensiones (Asociación acción/diálogo, Comprensión individual, Comunicación emocional, Regulación emocional, Utilidad, Adaptabilidad, Coherencia, Legalidad) puntuadas por GPT-4-turbo (1–10), validadas con evaluación humana (ICC promedio 74.76%, IC 95%). Entrenamiento: (i) Fine-tuning instruccional de Llama3-8B con LoRA usando las respuestas etiquetadas como "más empáticas" como objetivo; (ii) RLHF: entrenamiento de un reward model con datos pareados y posterior optimización de Llama3-8B con PPO y LoRA. Implementación: prompts unificados, temperatura 0 para evaluación; subset de testmini (100 muestras) para eficiencia; para video, muestreo de frames (1 cada 5) en GPT y frame medio en LLaVA.

## Resultados Clave
- Comprensión del escenario (testmini): GPT-4o obtiene Bleu-1 19.1, Bleu-4 5.3, ROUGE-L 23.7, CIDEr 8.8, SPICE 14.8, BERTScore 0.622 (mejor entre modelos evaluados).
- Planificación empática: GPT-4o alcanza Bleu-1 30.8, Bleu-4 12.0, ROUGE-L 26.1, CIDEr 25.9, SPICE 16.7, BERTScore 0.641 (mejor desempeño).
- Acciones empáticas (entrada video): GPT-4-vision-preview supera en grounding con Overlap 35.20, TF-IDF 27.69, LCS 29.58; GPT-4o queda por detrás (p. ej., Overlap 27.60).
- Acciones empáticas (entrada texto): Llama3-8B instruccional (IFT) entrenado en EmpathyAgent logra Overlap 55.87, TF-IDF 47.34, LCS 49.83 (mejor), superando GPT-4-turbo (Overlap 40.00) y GPT-4-vision (34.93).
- Métricas sin referencia (promedios): GPT-4o > LLaVA en todos los pasos; p. ej., Comprensión del escenario 7.79 vs 7.10; Planificación 5.35 vs 4.29; Acciones 7.43 vs 6.87; Legalidad ~10 para ambos en acciones.
- Preferencia de evaluadores: Llama3-8B IFT vence a GPT-4-turbo en elección GPT-4o (69% vs 31%) y en humanos (66% vs 39%) en una muestra pareada.
- Efecto del entrenamiento: Llama3-8B base apenas ejecuta acciones antes del FT; tras IFT/RLHF produce secuencias empáticas coherentes y diálogos más empáticos (RLHF mejora, pero menos que IFT).

## Limitaciones
- Dependencia de un entorno simulado (VirtualHome); la transferencia a robots y hogares reales no está demostrada.
- Generación y etiquetado asistidos por GPT (escenarios, selección de respuestas) pueden introducir sesgos y errores sutiles.
- Cobertura limitada del espacio de acciones (≈50 acciones) y dominios domésticos específicos.
- Evaluación sin referencia automatizada (GPT-4-turbo) pese a validación parcial humana (ICC ~74.8%), aún sujeta a discrepancias.
- RLHF mostró menor eficacia que IFT, posiblemente por un reward model insuficientemente robusto.
- Debilidades detectadas en Comprensión individual y Adaptabilidad de los modelos.

## Trabajo Futuro
- Diseñar reward models más sólidos y criterios de RLHF específicos de empatía.
- Ampliar acciones, objetos y contextos; evaluar en robots físicos y escenarios del mundo real.
- Reducir la dependencia de LLMs para generar/etiquetar datos (más anotación humana y auditoría de sesgos).
- Mejorar módulos de perfilado de persona y razonamiento de perspectiva (theory of mind) para Comprensión individual y Adaptabilidad.
- Integrar señales multimodales más ricas (prosodia, microexpresiones) y grounding sensoriomotor.
- Evaluaciones humanas a mayor escala y longitudinales de percepción de empatía y bienestar del usuario.

## Citas Relevantes
- "Empathy is fundamental to human interactions, yet it remains unclear whether embodied agents can provide human-like empathetic support."
- "We propose an empathy-specific evaluation suite that evaluates the agents’ empathy process."
- "We benchmark current models and found that exhibiting empathetic actions remains a significant challenge."
- "By establishing a standard benchmark for evaluating empathetic actions, we hope to advance research in empathetic embodied agents."
- "No quality of human nature is more remarkable... than that propensity we have to sympathize with others..." — David Hume.

## Notas Adicionales
Datos: 10k muestras; 100 personajes; 20 videos de acciones de entrada; 2 respuestas por muestra (más/menos empática); espacio de acción ~50; duración media de video ~16.3 s. Entrada: antecedentes del personaje, video y diálogo; salida: descripción del escenario, plan empático y acciones ejecutables. Evaluación: subset testmini de 100 para benchmarking; frames muestreados para VLMs. Confiabilidad: ICC humano–GPT 74.76% (IC 95%). Código/datos: https://github.com/xinyan-cxy/EmpathyAgent. Resultados clave: GPT-4o lidera en comprensión/planificación; GPT-4-vision en grounding de acciones con video; Llama3-8B IFT entrenado en EmpathyAgent lidera en acciones con entrada textual y es preferido por GPT-4o y humanos frente a GPT-4-turbo.
