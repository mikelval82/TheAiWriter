# Empathetic Conversational Agents: Utilizing Neural and Physiological Signals for Enhanced Empathetic Interactions

## Metadata
- **Autores**: Nastaran Saffaryazdi, Tamil Selvan Gunasekaran, Kate Loveys, Elizabeth Broadbent, Mark Billinghurst
- **Año**: 2025
- **Keywords**: agentes conversacionales, digital humans, empatía, reconocimiento de emociones neurofisiológico, EEG, EDA, PPG, HRV, fusión multimodal, interacción humano–computador

## Abstract
El estudio integra señales neurales y fisiológicas (EEG, EDA y PPG) en el módulo perceptual de un agente conversacional encarnado (digital human, DH) para detectar emociones en tiempo real y adaptar expresiones faciales y respuestas empáticas mediante espejado emocional. En un experimento dentro de sujetos, 23 participantes conversaron sobre temas emocionales con dos versiones del DH (neutral vs. empática). La condición empática produjo emociones más intensas y mayor involucramiento, reflejado en aumentos de HRV y EDA, y puntuaciones superiores de empatía percibida, agrado y rapport. Aunque la fusión multimodal mejoró la detección (arousal 69%, valencia 57%), persisten retos en precisión de reconocimiento, temporización de transiciones emocionales, diferencias individuales y limitaciones de prosodia y rango expresivo del avatar.

## Contribuciones Principales
- Integra señales neurales y fisiológicas (EEG, EDA, PPG) en el módulo de percepción de un agente conversacional para interacción empática en tiempo real
- Demuestra un pipeline de reconocimiento emocional (ventana deslizante) y orquestación que controla expresiones y respuestas empáticas de un DH
- Publica un dataset multimodal de interacciones con agentes neutrales y empáticos (video facial, audio, EEG, EDA, PPG)
- Evidencia empírica (autoinformes y biomarcadores) de mayor empatía, compromiso y regulación emocional con el DH empático
- Identifica desafíos prácticos: precisión de reconocimiento, temporización de transiciones, variabilidad individual, prosodia vocal limitada, diversidad de avatar y falta de calibración individual

## Metodología
Diseño del agente: Se utilizó un Digital Human (DH) de Soul Machines con un servidor de orquestación propio que deshabilitó las funciones nativas de reconocimiento y gestionó flujo conversacional, selección de respuestas predefinidas y generación de expresiones. Se implementaron dos condiciones: DH neutral (sin reconocimiento emocional, respuestas neutrales) y DH empático (reconocimiento en tiempo real y espejado emocional de acuerdo con arousal/valencia). Sensado y adquisición: Octopus-Sensing coordinó video facial, audio, EEG (OpenBCI), EDA y PPG (Shimmer3). Las señales EEG, EDA y PPG alimentaron el reconocimiento en tiempo real. Reconocimiento emocional: Modelos entrenados con un dataset previo de 16 participantes (conversaciones diádicas), etiquetado en arousal/valencia a partir de SAM (5 puntos binarizado). Preprocesamiento y extracción de características: EEG (potencias PSD por bandas), PPG (HRV en dominio temporal), EDA (métricas tónicas y fásicas). Clasificador: Random Forest por modalidad. Esquema temporal: ventana deslizante de 20 s con paso de 5 s (superpuestas) para equilibrar fidelidad de características (p.ej., HRV) y latencia. Fusión de decisiones: ponderada; valencia con pesos iguales (EEG, EDA, PPG), arousal con mayor peso para EDA y PPG (2) que EEG (1). Mapeo A-V a expresiones: cuatro estados (HAHV→alegría intensa; LAHV→alegría leve; LALV→tristeza; HALV→ira/miedo) priorizando claridad expresiva. Estudio de usuarios: 23 participantes (21–44 años), diseño intra-sujetos, contrabalanceo de condición y estímulos. Ocho imágenes IAPS (2 por cuadrante A-V) como disparadores conversacionales. Tras cada tema: autoinformes de estado emocional (A/V), empatía percibida (global, cognitiva y afectiva) y adecuación/temporización de expresiones; tras cada condición: cuestionario de rapport (QoI, DoR, DoL, DSP). Análisis estadístico: métodos no paramétricos (Aligned Rank Transform) con ANOVA de medidas repetidas (1–3 vías). Comparación neurofisiológica entre condiciones con ANOVA ART por rasgos de EEG/PPG/EDA.

## Resultados Clave
- Empatía percibida: mayor en condición empática para empatía global (F(1,166)=27, p<0.001), empatía cognitiva (F=4.7, p<0.03) y afectiva (F=5.4, p<0.02)
- Modulación por estado emocional: puntuaciones de empatía más altas en alta valencia y alto arousal (p<0.001 en múltiples factores)
- Rapport: aumentos significativos en Grado de Rapport (DoR) (F(1,42)=8.38, p=0.006) y Grado de Agrado (DoL) (F(1,42)=6.64, p<0.01); tendencias al alza en QoI y DSP
- Porcentaje de participantes que prefirieron el DH empático: DoR 82%, DoL 86%, DSP 59%, QoI 63%
- PPG/HRV: incrementos significativos en la mayoría de métricas (p.ej., SDNN, RMSSD, SDSD, CVNN, HTI, TINN; p<0.01–0.05), indicando mayor regulación emocional y atención/compromiso
- EDA: picos de amplitud y derivadas positivas mayores, y cambios tónicos significativos con el DH empático (p<0.02–0.005), reflejando mayor activación/compromiso
- EEG: sin diferencias significativas entre condiciones (ruido por habla y procesos cognitivos compartidos)
- Adecuación de expresiones en tiempo real: mejores en condición empática para adecuación (F(1,166)=10, p<0.002) y temporización (F=6, p<0.01); más efectivas en alta valencia y alto arousal
- Reconocimiento en tiempo real: fusión multimodal superó a modalidades individuales (arousal 69.1%, valencia 57.3%; EEG 64.8/57.1; PPG 65.4/58.1; EDA 58.2/52.7)
- Inducción emocional: los autoinformes de arousal/valencia se alinearon con el objetivo emocional de los temas (p<0.05), validando el protocolo

## Limitaciones
- Tamaño muestral moderado, limitando la generalización
- Precisión del reconocimiento modesta (especialmente en valencia); necesidad de modelos y fusión más robustos
- Falta de control de prosodia/tono de voz en el DH; posible disonancia audio–visual
- Sin integración con LLMs: repertorio verbal limitado a respuestas predefinidas
- Diversidad de avatar restringida (género/apariencia únicos)
- Rango emocional del avatar acotado (negativos poco diferenciables; ira/miedo agrupados)
- Diferentes latencias entre modalidades para transiciones emocionales (EEG más rápido, PPG más lento)
- Variabilidad interindividual (rasgos de personalidad/empatía) no modelada; sin calibración por participante
- Señales EEG ruidosas durante conversación hablada; posibles falsos negativos
- Múltiples comparaciones univariadas en análisis exploratorio (riesgo de falsos positivos sin corrección estricta)

## Trabajo Futuro
- Integrar LLMs para diálogo dinámico y contextual
- Incorporar modulación de prosodia vocal en tiempo real alineada al estado del usuario
- Mejorar el reconocimiento con deep learning, fusión temporal/atencional y aprendizaje multimodal
- Añadir modalidades conductuales (voz y rostro) de forma respetuosa con privacidad para complementar señales fisiológicas
- Ampliar rango y granularidad emocional (p.ej., distinguir ira vs. miedo) y expresividad del avatar
- Aumentar tamaño y diversidad muestral; análisis de potencia y muestreo estratificado
- Calibración personalizada y/o adaptación online para reducir variabilidad intersujeto
- Modelar y evaluar transiciones emocionales y latencias multimodales
- Depuración avanzada de EEG y extracción de rasgos más ricos
- Explorar efectos de características del avatar (género/edad/cultura) en empatía y aceptación

## Citas Relevantes
- "Results showed that users experienced stronger emotions and greater engagement during interactions with the Empathetic DH, highlighting the benefits of these signals for enhancing empathy."
- "Addressing these issues is key to advancing empathetic digital agents."
- "We used a digital human (DH) developed by Soul Machines Ltd to create an empathetic conversational agent."
- "The empathic condition was weird and I could not be able to connect with it. I usually expect a neutral reaction from a stranger or a machine."
- "Empathetic Condition was realistic but weird."
- "The empathetic DH tended to use reflected expressions that were more appropriate and at the correct timing."

## Notas Adicionales
Artículo open access (CC BY-NC) publicado online el 07 Ago 2025 (IJHCI, Taylor & Francis). Diseño intra-sujetos con 23 participantes; ética aprobada (U. Auckland, ref. 023799). Reconocimiento en ventanas de 20 s cada 5 s; fusión con pesos mayores para EDA/PPG en arousal. Mapeo A-V a cuatro estados expresivos; negativas diferenciadas principalmente vía discurso compasivo. Cuestionarios: autoinforme de A/V y empatía (8 ítems) y rapport (QoI, DoR, DoL, DSP). Dataset multimodal público: https://pegconv.nastaran-saffar.me#peghmconv. Limitaciones prácticas de la plataforma: sin prosodia dinámica ni LLMs en la versión usada.
