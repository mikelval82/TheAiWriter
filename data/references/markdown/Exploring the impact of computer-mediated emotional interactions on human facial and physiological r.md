# Exploring the impact of computer-mediated emotional interactions on human facial and physiological responses

## Metadata
- **Autores**: Nastaran Saffaryazdi, Nikita Kirkcaldy, Gun Lee, Kate Loveys, Elizabeth Broadbent, Mark Billinghurst
- **Año**: 2024
- **Keywords**: Emotion recognition, Remote communication, Physiological signals, Facial expressions, Empathy

## Abstract
El estudio compara cómo las conversaciones emocionales cara a cara y por videollamada afectan las respuestas faciales (unidades de acción), fisiológicas (EDA y PPG/HRV) y la empatía percibida. Con 15 participantes en un diseño intra-sujeto, se recogieron señales EDA y PPG y vídeo facial mientras conversaban sobre recuerdos emocionales inducidos por 16 imágenes IAPS (4 cuadrantes de valencia-arousal). Se aplicaron ANOVA de medidas repetidas con ART para evaluar efectos de condición (presencial vs remota), arousal y valencia. Hallazgos clave: (1) diferencias significativas en múltiples AUs según la condición (más AUs de emoción positiva en remoto y más AUs negativas en presencial); (2) mayor componente fásico de EDA en presencial, y mayor variabilidad de frecuencia cardiaca (HRV) en remoto; (3) menor empatía percibida por parte del entrevistador en remoto; (4) los modelos de reconocimiento emocional mejoran notablemente al preentrenarse con datos de una condición y evaluarse en la otra (incrementos del 20%–45%). Los resultados ofrecen implicaciones para optimizar HCI y comprender las respuestas emocionales en interacciones mediadas por tecnología.

## Contribuciones Principales
- Demostrar cuantitativamente diferencias en respuestas fisiológicas y conductuales entre conversaciones presenciales y videomediadas en contextos emocionales.
- Identificar qué aspectos de EDA, HRV y AUs faciales varían con la condición de interacción, valencia y arousal.
- Evaluar estrategias de reconocimiento emocional entre condiciones, mostrando que el preentrenamiento cruzado mejora sustancialmente la precisión.
- Crear un dataset multimodal (EDA, PPG, vídeo facial) de conversaciones presenciales y remotas y anunciar su disponibilidad pública.

## Metodología
Estudio experimental intra-sujeto con 15 participantes (7 mujeres, 8 hombres; 21–36 años). Dos condiciones: conversación cara a cara y remota (Zoom), orden contrabalanceado. Inducción emocional mediante 16 imágenes IAPS (4 categorías: HAHV, HALV, LAHV, LALV), con protocolo por imagen: 3 s de fijación, 6 s de imagen, seguido de 2–3 min de conversación guiada sobre recuerdos y sensaciones asociados. Medidas: EDA (Shimmer3 EDA+), PPG (derivación HRV), vídeo facial (Intel RealSense/Logitech), audio; EEG intentado (OpenBCI) pero excluido por fallos de registro. Sincronización con Octopus-sensing. Autoinformes SAM (1–9) de valencia y arousal tras cada conversación; codificación binaria (baja/alta) usando el punto medio. Preprocesado: extracción de ventanas de conversación excluyendo 9 s iniciales (con 3 s de línea base); EDA limpiado con neurokit2, componentes fásico/tónico y picos; PPG filtrado (0.5–4 Hz), normalización de línea base y extracción de HRV en dominio temporal con neurokit2/heartpy; vídeo facial con OpenFace (18 AUs), presencia por voto mayoritario por ventana. Normalización [0,1] por participante. Análisis estadístico: ANOVA de medidas repetidas con ART (no paramétrico) de 3 factores (condición, arousal, valencia) para EDA/PPG/AUs; ANOVA de 2 factores (condición×género) para empatía. Reconocimiento emocional: Random Forest (200 árboles), ventanas de 20 s; evaluación 5-fold intra-condición, LOSO, y modelos preentrenados entre condiciones.

## Resultados Clave
- Actividad facial (AUs): La condición afectó significativamente 10/18 AUs (p<0.04). En presencial se observaron más AUs asociadas a emociones negativas (AU20, AU05, AU09, AU15, AU25). En remoto, mayor presencia de AUs vinculadas a emociones positivas (AU45, AU06, AU12, AU14). Efectos de valencia: aumentan AU06, AU10, AU12, AU25 con valencia alta; AU04 y AU45 más frecuentes con valencia baja. Efectos de arousal: AU10 y AU12 menores en bajo arousal (p≈0.03–0.05).
- EDA: El promedio del componente fásico fue mayor en presencial (phasic_mean, p=0.026), indicando respuestas más rápidas/intensas ante estímulos. Con valencia baja, aumentaron frecuencia de picos, derivadas positivas y varianza de picos (p≈0.037–0.049). Arousal afectó tonic_min (mayor en bajo arousal; p=0.042). Hubo interacciones C:V y C:A/A:V sobre métricas fásicas.
- PPG/HRV: En remoto mayores HRV_MadNN, HRV_MCVNN, HRV_IQRNN (p≤0.033), sugiriendo mejor regulación emocional/menor estrés. HRV_TINN fue mayor en valencia baja (p=0.042). Sin efectos significativos de arousal en HRV.
- Empatía: Disminuyó la empatía percibida desde el entrevistador hacia el participante en remoto (p=0.04). Otros factores (empatía propia, reflexión afectiva/cognitiva, facilidad de interacción) no fueron significativos, aunque las tendencias favorecieron el presencial.
- Reconocimiento emocional: El preentrenamiento cruzado elevó marcadamente la precisión LOSO. Ejemplos (promedios LOSO): EDA arousal remoto: 54.9% (desde cero) vs 99.8% (preentrenado); PPG arousal remoto: 55.6% vs 99.2%; Face valencia remoto: 54.2% vs 100%. En general, incrementos del 20%–45% frente a modelos sin preentrenar.

## Limitaciones
- Tamaño muestral reducido (n=15), limitando generalización (variabilidad por personalidad, cultura, género).
- EEG no utilizable por fallo de hardware; se pierde una modalidad relevante para fusión multimodal.
- Pocos temas de conversación; posible sesgo por efectos psicológicos del contenido y recuerdo.
- Muestra sesgada: personal/estudiantes universitarios familiarizados con videoconferencias; resultados pueden no extrapolar a novatos digitales.
- Un único entrevistador (mujer); posible efecto de género y de la personalidad del entrevistador.
- Interacciones con desconocidos; la familiaridad con el interlocutor podría alterar las respuestas.
- Entorno de laboratorio controlado; puede no reflejar completamente contextos reales y plataformas diversas.

## Trabajo Futuro
- Ampliar la muestra y diversidad cultural/etaria y nivel de alfabetización digital.
- Incluir más canales (EEG fiable, mirada, postura, gestos corporales) y evaluar su aporte incremental.
- Variar género y número de entrevistadores; incluir interacciones con parejas/amigos para estudiar la familiaridad.
- Evaluar diferentes plataformas y configuraciones (disposición de pantallas, latencia, calidad de audio/vídeo) y su impacto en presencia social.
- Desarrollar sistemas adaptativos en tiempo real que monitoricen rasgos significativos (AUs, EDA fásica, HRV) y retroalimenten al interlocutor.
- Investigar procedimientos de evaluación más estrictos que eviten fugas de información entre condiciones en el preentrenamiento.

## Citas Relevantes
- "Remote communication has become pervasive, yet its impact on human emotions, empathy, and physiological responses remains unclear."
- "Our findings reveal significant differences in physiological responses between face-to-face and remote conversation and variations in perceived empathy based on interaction setting."
- "We also show that we can recognize emotions more accurately when we pre-train a random forest classifier with one condition’s data (an increase of 20% to 45% for various modalities)."
- "Data will be made available on request."
- "I feel more connected to the other person when I see her sitting close to me"

## Notas Adicionales
Diseño intra-sujeto con contrabalanceo y uso de IAPS para homogeneizar contenido emocional. La mayor HRV en remoto podría relacionarse con menor estrés/presencia social al hablar con un desconocido a través de pantalla. La métrica de reconocimiento con preentrenamiento entre condiciones, aunque alta, implica que el modelo ha visto ensayos del sujeto en la otra condición (no es un LOSO estricto), por lo que la interpretación de generalización debe ser cauta. Se anuncia dataset público (URL de nota al pie), pero la sección de disponibilidad indica acceso bajo petición; posible inconsistencia editorial. EEG se intentó pero se excluyó. La interfaz remota reservó media pantalla para rostro del entrevistador y media para la imagen IAPS. Los hallazgos sugieren que monitorizar phasic_mean (EDA), HRV en dominio temporal y AUs específicas (AU06, AU12, AU14, AU20, AU04, AU45) puede ser útil para soportar empatía y presencia social en sistemas remotos.
