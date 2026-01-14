# Performance Analysis of Unimodal and Multimodal Models in Valence-Based Empathy Recognition

## Metadata
- **Autores**: Adria Mallol-Ragolta, Maximilian Schmitt, Alice Baird, Nicholas Cummins, Björn Schuller
- **Año**: 2019
- **Keywords**: empathy recognition, valence prediction, multimodal fusion, unimodal models, BLSTM, eGeMAPS, facial action units, OpenFace, openSMILE, OMG-Empathy Prediction Challenge, personalised models, generalised models, CCC

## Abstract
El trabajo aborda la predicción continua de la empatía basada en valencia del oyente durante interacciones actor-oyente semiescriptas, como contribución al OMG-Empathy Prediction Challenge. Se extraen rasgos acústicos (eGeMAPS) de las voces del actor y del oyente y rasgos visuales (FAUs) del rostro del oyente, para alimentarlos a una red recurrente BLSTM que modela dependencias temporales. Se entrenan modelos unimodales (audio o video) y multimodales (fusión a nivel de características) bajo configuraciones generalizadas y personalizadas por sujeto. La evaluación con el coeficiente de correlación de concordancia (CCC) muestra que la multimodalidad supera a las modalidades individuales y que existen dependencias intra-sujeto en la percepción de empatía. El mejor resultado se obtiene con un modelo multimodal personalizado (CCC = 0.11 en test).

## Contribuciones Principales
- Propuesta de un sistema de reconocimiento de empatía basada en valencia empleando BLSTM con fusión multimodal de audio y video.
- Comparación sistemática entre modelos unimodales y multimodales, y entre enfoques generalizados vs. personalizados por oyente.
- Pipeline de preprocesamiento que alinea modalidades: reducción de video/etiquetas a 5 fps y segmentación de audio con solapamiento (ventanas de 0.4 s).
- Extracción de rasgos acústicos eGeMAPS (openSMILE) y rasgos visuales de FAUs (OpenFace) con normalización z para audio.
- Demostración de que la multimodalidad mejora el rendimiento (CCC) frente a cada modalidad por separado.
- Evidencia empírica de dependencias intra-sujeto en la percepción de empatía (modelos personalizados superan a generalizados en test).
- Publicación del código del sistema para su reproducción.

## Metodología
Datos: OMG-Empathy Prediction Dataset con 80 interacciones (422 min 34 s) entre 4 actores y 10 oyentes sobre 8 temas. Audio a 16 kHz, video a 25 fps; anotaciones continuas de valencia a 25 Hz. División: 40/10/30 (train/dev/test). Se registran audio de actor y oyente y video de ambos; el sistema usa video del oyente y audio de actor+oyente.
Preprocesamiento: Para acelerar el entrenamiento y alinear modalidades, se reduce el video del oyente y las anotaciones a 5 fps (seleccionando 1 de cada 5 frames). Para mantener la riqueza acústica, se segmenta el audio en marcos de duración equivalente a 5 frames de video (0.4 s), con 50% de solapamiento entre marcos consecutivos. Se aplica zero-padding en los extremos cuando es necesario.
Extracción de características: Visuales (OpenFace): 35 rasgos por frame del oyente (17 intensidades de FAUs en [0.00, 5.00] y 18 presencias binarias). Acústicos (openSMILE): 88 rasgos eGeMAPS por marco de audio. Normalización: audio con z-normalización; visuales sin normalizar por rango acotado.
Arquitectura de aprendizaje: Red recurrente BLSTM con una capa bidireccional con M ∈ {30, 40, 50} unidades LSTM (ajustado en dev), seguida de una capa densa lineal de 1 unidad para salida continua por paso temporal. Activaciones: tanh (BLSTM) y lineal (salida). Optimización: pérdida basada en CCC y optimizador Adam. Tamaño de lote = 5; early stopping con paciencia de 3 épocas sin mejora.
Fusión: A nivel de características (concatenación audio+video) para modelos multimodales. Modelos unimodales entrenados por separado con audio o video.
Estrategia de entrenamiento: Modelos generalizados entrenados con todas las interacciones de entrenamiento sin distinguir sujetos. Modelos personalizados entrenados por oyente (solo con sus interacciones) para capturar dependencias intra-sujeto.
Postprocesamiento: Suavizado de las predicciones con un filtro de mediana (tamaño de ventana = 301 muestras). Reescalado temporal por replicación (x5) para volver a 25 Hz y comparar con las anotaciones originales.

## Resultados Clave
- En validación (dev), los modelos multimodales generalizados superan a los unimodales: con 40 LSTM units, CCCmultimodal = 0.07 frente a CCCacoustic = −0.00 y CCCvisual = −0.02; con 50 units, CCCmultimodal = 0.06 frente a CCCacoustic = 0.03 y CCCvisual = −0.01.
- Los rasgos visuales por sí solos rinden peor que los acústicos en este setup, pese a evidencia previa de utilidad de lo visual en valencia.
- En modelos personalizados (50 units): CCCmultimodal = 0.06, CCCacoustic = 0.05, CCCvisual = 0.04 en dev; la multimodalidad vuelve a ser superior.
- En test (modelos entrenados con train+dev):
  - Generalizado multimodal (40 units): CCCdev = 0.07, CCCtest = 0.05.
  - Generalizado multimodal (50 units): CCCdev = 0.06, CCCtest = 0.06.
  - Personalizado multimodal (50 units): CCCdev = 0.06, CCCtest = 0.11 (mejor resultado).
- Ningún modelo alcanza el baseline del desafío para la pista generalizada (CCC = 0.111), aunque el mejor personalizado se aproxima (0.11).

## Limitaciones
- CCC bajos en general, lo que sugiere posible modelado de ruido y/o señal débil frente a la complejidad del fenómeno.
- La filtración por mediana (ventana grande) puede suavizar en exceso y degradar picos o variaciones útiles.
- Datos limitados por sujeto: los modelos personalizados se evalúan en una sola instancia por oyente en dev, dificultando conclusiones robustas.
- Posible inadecuación del conjunto de rasgos visuales (FAUs tal como se extrajeron) para captar empatía basada en valencia en este contexto.
- Dudas sobre la capacidad de generalización debido a cantidad de datos de entrenamiento y representación reducida del conjunto de desarrollo.
- Downsampling de video/anotaciones a 5 fps implica pérdida de resolución temporal potencialmente relevante.

## Trabajo Futuro
- Compensación de retardo de anotaciones para realinear señales y etiquetas (annotation delay compensation).
- Diarización de hablantes para aislar contribuciones del actor y del oyente en la señal acústica.
- Explorar espacios de características alternativos (p. ej., representaciones profundas de cara/voz) y aprendizaje auto-supervisado.
- Profundizar en arquitecturas personalizadas más complejas (capas adicionales, redes más profundas) y estrategias de regularización.
- Transfer learning para ampliar datos efectivos y estudiar la dependencia de la tarea.
- Entrenamiento con ventanas deslizantes (data augmentation temporal) para aumentar datos de entrenamiento.
- Reevaluar métodos de postprocesamiento/upsampling y el impacto de la reducción a 5 fps.

## Citas Relevantes
- "The results support the suitability of employing multimodal data to recognise participants’ valence-based empathy during the interactions, and highlight the subject-dependency of empathy."
- "we obtained our best result with a personalised multimodal model, which achieved a CCC of 0.11 on the test set."
- "the labelled valence scores seem to be listener dependent."
- "the CCC scores measured are low, which suggests that we might be modelling noise."
- "This result supports the suitability of employing personalised models to automatically predict empathy, and it also suggests the existence of intra-subject dependencies on the perception of empathy"

## Notas Adicionales
El sistema usa video únicamente del oyente y audio de ambos participantes, bajo la hipótesis de que la paralingüística del actor influye en la empatía del oyente. La fusión se realiza a nivel de características. El filtrado mediano (ventana 301) y la replicación para upsampling son decisiones simples y podrían ser sustituidas por métodos más sofisticados. Se publica el código del sistema (https://github.com/EIHW/OMGempathy2019). La tabla de datos muestra una fuerte reducción de frames tras el preprocesamiento (p. ej., train: de 309,875 a 61,975). Aunque la multimodalidad supera a las modalidades individuales, los valores de CCC son modestos y no alcanzan el baseline de la pista generalizada del desafío.
