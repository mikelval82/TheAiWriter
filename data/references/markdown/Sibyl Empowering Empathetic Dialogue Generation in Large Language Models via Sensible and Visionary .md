# Sibyl: Empowering Empathetic Dialogue Generation in Large Language Models via Sensible and Visionary Commonsense Inference

## Metadata
- **Autores**: Lanrui Wang, Jiangnan Li, Chenxu Yang, Zheng Lin, Hongyin Tang, Huan Liu, Yanan Cao, Jingang Wang, Weiping Wang
- **Año**: 2025
- **Keywords**: empatía conversacional, diálogo multi-turno, conocimiento de sentido común, inferencia visionaria, chain-of-thought, soporte emocional, LLMs, respuesta empática, anticipación del futuro del diálogo

## Abstract
El trabajo presenta Sibyl, un paradigma para dotar a modelos de lenguaje grandes (LLMs) de inferencias de sentido común orientadas al futuro inmediato del diálogo (visionary commonsense). Sibyl genera cuatro tipos de inferencias (causa, evento subsiguiente, estado emocional del usuario e intención del asistente) que puentean la brecha entre el historial conversacional y la respuesta deseada, actuando como pasos intermedios de razonamiento tipo chain-of-thought. Estas inferencias se obtienen primero con un LLM potente (GPT-4o) usando el historial y la respuesta de referencia, y luego se entrenan modelos abiertos para predecirlas sólo desde el historial. Al integrar estas inferencias en LLaMA y Flan-T5, así como en un esquema de prompting, se logran mejoras consistentes en métricas automáticas, evaluaciones humanas y evaluaciones con LLMs en los conjuntos EMPATHETICDIALOGUES y ESConv.

## Contribuciones Principales
- Identifica la limitación de la inferencia de sentido común basada únicamente en el historial (uno-a-muchos), que introduce ruido y reduce la empatía y el soporte emocional en las respuestas.
- Propone Sibyl, un marco de inferencia de sentido común sensible y visionaria para diálogos, que incluye factores psicológicos, emocionales y causales relevantes al futuro inmediato del diálogo.
- Demuestra, mediante extensos experimentos, que Sibyl mejora de forma significativa la generación de respuestas empáticas en múltiples modelos base, configuraciones (fine-tuning y prompting) y métricas (automáticas, humanas y con LLMs).

## Metodología
Visión general: Sibyl busca anticipar la próxima respuesta infiriendo conocimiento de sentido común orientado al futuro. El pipeline consta de: (1) adquisición de conocimiento visionario con un LLM potente, (2) entrenamiento de modelos abiertos para predecir dicho conocimiento sólo desde el historial, y (3) generación de respuesta incorporando estas inferencias.

1) Adquisición de commonsense visionario: Se usa GPT-4o para generar cuatro categorías de inferencias K a partir del historial del diálogo C y la respuesta de referencia Y: (a) Causa (posible causa en la historia que motiva la próxima respuesta), (b) Evento subsiguiente (lo que podría ocurrir a continuación), (c) Estado emocional (emoción del usuario en su último turno), (d) Intención (propósito probable del asistente). Se emplean plantillas de prompt con un ejemplo de demostración. La validez de estas categorías se verifica con cinco anotadores humanos (evaluación binaria en 400 ejemplos; puntuaciones medias > 0.893; κ de Fleiss ≈ 0.52).

2) Entrenamiento Sibyl (SFT de modelos abiertos): Se fine-tunean LLMs abiertos para predecir K sólo desde C (sin Y), aprendiendo a anticipar el futuro bajo supervisión de las inferencias oráculo de GPT-4o. Se diseñan plantillas de prompt explícitas por tipo de conocimiento. La pérdida es NLL sobre el texto de las inferencias. Implementación: LLaMA3.1-8B-Instruct y Flan-T5-XL, con HuggingFace Transformers, LR=3e-5, batch=16, hasta 5 épocas, selección por validación. Para LLaMA se usa LoRA (r=8, α=16, dropout=0.05) sobre módulos Q y V, ajustando ≈0.06% de parámetros para reducir coste.

3) Inferencia y generación de respuesta: En test, los modelos visionarios Ψ generan las cuatro inferencias Kp a partir de C con las mismas plantillas. Para generar la respuesta, se concatena C + Kp como entrada al generador. Dos estrategias: (a) Fine-tuning del generador (LLaMA3.1-8B-Instruct y Flan-T5-XL) optimizando NLL sobre la respuesta verdadera; (b) Enfoque por prompting (p. ej., GPT-4o) con C + Kp.

Evaluación: Datasets EMPATHETICDIALOGUES (ED) y ESConv. Métricas automáticas: BLEU-n, ROUGE-L, METEOR, Distinct-n, CIDEr, cosenos Average/Extrema. Comparativas con baselines: CASE, M-Cue CoT, COMET, DOCTOR, DIALeCT, además de modelos base sin conocimiento. Se realizan estudios de ablación excluyendo cada categoría (w/o Cause/Intent/Subs/Emo). Evaluaciones humanas (ED: Coherencia, Empatía, Informatividad, Engagement; ESConv: Fluidez, Comforting, Supportive, Suggestion, Overall) con 5 anotadores (200 diálogos). Evaluación con LLMs (G-Eval) para Naturalness, Coherence y métricas específicas (Empatía/Suportividad) muestreando 200 ejemplos.

## Resultados Clave
- En ED (fine-tuning con LLaMA3.1): +Sibyl logra BLEU-4=2.95, ROUGE-L=19.08, METEOR=9.61, Ave=88.36, Ext=50.90, CIDEr=26.93, superando a DIALeCT (CIDEr=22.21) y otros baselines; mejoras significativas (p<0.01).
- En ED (prompting con GPT-4o): +Sibyl alcanza BLEU-4=1.83 y ROUGE-L=17.62, con mejoras consistentes frente a COMET/DOCTOR/DIALeCT y M-Cue CoT (que incluso empeora al modelo sin conocimiento en varios casos).
- En ESConv (fine-tuning con LLaMA3.1): +Sibyl obtiene BLEU-4=1.52, ROUGE-L=16.23 y CIDEr=10.92, superando a DIALeCT (CIDEr=10.44) y otros.
- En ESConv (prompting con GPT-4o): +Sibyl mejora BLEU-4 a 1.10 y ROUGE-L a 15.20, destacando en métricas de solapamiento y diversidad.
- En Flan-T5-XL (ED, fine-tuning): +Sibyl alcanza BLEU-4=5.24 vs 3.78 del base, ROUGE-L=23.09 vs 20.73, METEOR=10.39 vs 8.92, CIDEr=43.36 vs 30.44, mostrando ganancias amplias.
- Evaluación humana (ED): Sibyl supera a CASE, COMET, DOCTOR y DIALeCT en Coherencia, Empatía, Informatividad y Engagement (diferencias estadísticamente significativas; κ≈0.4–0.6).
- Evaluación humana (ESConv): Sibyl lidera en Overall, y mejora en Fluidez, Comforting, Supportive y Suggestion frente a los baselines.
- G-Eval (ED, fine-tuning): LLaMA3.1+Sibyl obtiene Nat.=2.568, Emp.=2.396, Coh.=2.774, por encima de los otros conocimientos. En ESConv (fine-tuning): Nat.=2.387, Sup.=1.958, Coh.=2.599.
- Ablaciones (ED/ESConv): eliminar cualquier categoría degrada el desempeño; quitar Intention es lo más perjudicial (p. ej., ED CIDEr de 26.89 a 16.46), evidenciando la importancia de prever la intención futura.
- Modelos pequeños: añadir Sibyl a un Transformer básico (ED) eleva CIDEr de 15.04 a 22.41; en ESConv, Normal TRS + Sibyl y Blender/BART + Sibyl superan a sistemas previos (p. ej., MultiESC) con simple concatenación de Kp.

## Limitaciones
- La evaluación automática de empatía y soporte emocional sigue siendo problemática: las métricas tradicionales no se alinean plenamente con juicios humanos.
- Dependencia de LLMs potentes (GPT-4o) para generar las inferencias oráculo en la fase de adquisición, lo que introduce costes y potenciales sesgos/errores de dichas herramientas.
- Acuerdo interanotador moderado (κ≈0.52) en la validación humana de las categorías de conocimiento, lo que sugiere subjetividad residual.
- Posible sensibilidad del rendimiento a plantillas de prompting y a la calidad de las inferencias generadas en la fase visionaria.

## Trabajo Futuro
- El paper no establece explícitamente una sección de trabajo futuro; posibles direcciones incluyen: desarrollar métricas automáticas más fiables para empatía/soporte; reducir la dependencia de LLMs cerrados en la adquisición de conocimiento; ampliar a dominios, idiomas y contextos de mayor riesgo; integrar salvaguardas de seguridad y control de alucinaciones en la inferencia visionaria.

## Citas Relevantes
- "we present an innovative framework named Sensible and Visionary Commonsense Knowledge (Sibyl)."
- "We argue that the dialogue history does not encompass enough information to generate the intended response."
- "These inferences act as a form of chain-of-thought (CoT) prompts, aiding LLMs in effectively dealing with complex dialogue contexts, bridging the gap between dialogue history and potential response, and ultimately promoting empathy and emotional support."
- "Extensive experiments demonstrate the effectiveness of our paradigm, and detailed analyses validate our method across multiple scenarios and backbone models, showing significant improvements in automated metrics and evaluations by human and powerful LLM assessors."

## Notas Adicionales
Código disponible: https://github.com/wlr737/Sibyl. Dos autores con contribución igual; Zheng Lin es autor de correspondencia. Los cuatro tipos de conocimiento (Causa, Subsecuente, Emoción, Intención) se operacionalizan con prompts específicos (Figuras 5–6) y se incorporan al generador como pasos de razonamiento intermedios. Se usa LoRA para LLaMA con configuración ligera, haciendo el método enchufable y eficiente. Los resultados confirman que anticipar el futuro inmediato del diálogo reduce el desajuste entre historial y respuesta deseada, elevando empatía y utilidad percibida.
