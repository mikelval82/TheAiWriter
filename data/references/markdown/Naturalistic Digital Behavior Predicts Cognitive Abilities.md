# Naturalistic Digital Behavior Predicts Cognitive Abilities

## Metadata
- **Autores**: Tung Vuong, Giulio Jacucci, Tuukka Ruotsalo
- **Año**: 2024
- **Keywords**: cognitive ability, cognitive modeling, digital behavior, human-computer interaction, information processing, selective attention, working memory, fluid intelligence, psychomotor speed, machine learning, structural equation modeling, screenomics

## Abstract
El estudio investiga cómo el comportamiento digital naturalista (capturado 24/7 durante 14 días en portátiles personales) se asocia con y puede predecir habilidades cognitivas. Con datos de 20 adultos (pantallas, registros del SO, teclado y ratón) y una batería de tests cognitivos (velocidad psicomotora, velocidad de procesamiento, atención selectiva, memoria de trabajo e inteligencia fluida), los autores muestran, mediante regresión, modelado de rutas y aprendizaje automático, que ciertas características de interacción (p. ej., cambios de pestaña, visitas de páginas/sitios, texto acumulado en pantalla, velocidad de tecleo en la Omnibox) se asocian con diferencias cognitivas y permiten predecir dichas habilidades con bajos errores. Se propone el uso de datos de interacción naturalista como nueva fuente para modelar diferencias cognitivas y para personalización adaptativa.

## Contribuciones Principales
- Evidencia empírica, en entornos naturalistas (in the wild), de asociaciones entre comportamiento digital y cinco habilidades cognitivas clave.
- Extracción y validación de medidas generales y no intrusivas del comportamiento digital: texto acumulado, entropía acumulada, cambios de pestaña, visitas de páginas/sitios y velocidad de tecleo en Omnibox.
- Análisis estadístico y causal (regresión y modelos de ecuaciones estructurales) que detallan vínculos específicos: atención selectiva con procesamiento de información; inteligencia fluida con percepción de información; memoria de trabajo con velocidad de entrada.
- Modelos predictivos (Random Forest y regresión múltiple) que estiman habilidades cognitivas a partir de comportamiento digital con errores bajos y significativos frente a controles (permutación y azar).
- Identificación de la importancia relativa de características (feature importance) por habilidad cognitiva, coherente con los análisis de asociación y de ruta.
- Discusión de implicaciones para sistemas adaptativos y consideraciones éticas de privacidad en la recolección y uso de datos conductuales.

## Metodología
Diseño: estudio naturalista con monitoreo continuo de actividad digital durante 14 días en portátiles personales (Windows 10). Instrumentación: captura de pantalla cada 2 s, registros del SO (títulos de ventana, apps activas, URLs), eventos de teclado y ratón (clics, scroll) con marcas de tiempo. Participantes: 20 adultos (19–71 años; 10 mujeres, 10 hombres), trabajadores del conocimiento con alta experiencia informática; criterios de elegibilidad estrictos (instalación de software, conocimientos y uso habitual del portátil). Privacidad: almacenamiento local durante el monitoreo, posterior transferencia segura; opción de pausar el registro; aprobación ética; compensación.
Variables conductuales (normalizadas por hora):
- Percepción de información: texto acumulado (nuevas palabras por captura vía OCR, sumadas con diferencia respecto a captura previa) y entropía acumulada (Shannon, imágenes en escala de grises con diferencia de pantalla para considerar solo píxeles nuevos).
- Procesamiento de información: cambios de pestaña por hora; visitas de páginas únicas (URLs) por hora; visitas de sitios únicos (dominios) por hora.
- Conducta de entrada: velocidad de tecleo en Omnibox (ms/caracter en barra de direcciones y cajas de búsqueda).
Medidas cognitivas (tests estandarizados):
- Velocidad psicomotora: Digit Symbol Substitution Test (nº aciertos/120 s).
- Velocidad de procesamiento: NIH Toolbox Pattern Comparison (nº aciertos/90 s).
- Atención selectiva: Stroop color-word (nº correctos/45 s).
- Memoria de trabajo: Operation Span (puntuación absoluta normalizada por aciertos de series completas).
- Inteligencia fluida: Trail Making con alternancia número-letra (tiempo de finalización correcta).
Análisis: pruebas de normalidad (Shapiro–Wilk); regresión lineal (DV: conducta; IV: habilidad; p ajustados Bonferroni); modelado de rutas (SEM) con habilidades como variables exógenas, factores conductuales como mediadores. Predicción: Random Forest y Regresión Lineal Múltiple con validación leave-one-user-out; métrica RMSE. Controles: permutación de características y objetivos (1.000 repeticiones) y predicción aleatoria (1.000 repeticiones). Ajuste de hiperparámetros (RF: nº árboles y profundidad por CV en training; MLR: intercepto habilitado, sin normalización) evitando fuga de datos.

## Resultados Clave
- Percepción de información: el texto acumulado por hora se asoció significativamente con velocidad psicomotora (F(1,18)=19.42, R²=0.533, p<0.001) e inteligencia fluida (F(1,18)=13.21, R²=0.43, p=0.002). La entropía acumulada no mostró asociaciones significativas con las cinco habilidades.
- Procesamiento de información:
  - Cambios de pestaña/hora se asociaron con velocidad de procesamiento (F(1,18)=8.604, R²=0.34, p=0.0093), atención selectiva (F(1,18)=8.61, R²=0.34, p=0.0092) e inteligencia fluida (F(1,18)=6.28, R²=0.35, p=0.023).
  - Visitas de páginas/hora se asociaron con velocidad de procesamiento (F(1,18)=5.98, R²=0.26, p=0.026).
  - Visitas de sitios/hora se asociaron con atención selectiva (F(1,18)=5.18, R²=0.23, p=0.036).
- Conducta de entrada: la velocidad de tecleo en Omnibox se asoció con memoria de trabajo (F(1,18)=5.033, R²=0.23, p=0.038).
- Modelado de rutas (SEM):
  - Atención selectiva → procesamiento de información (coef=7.73, p=0.009); Procesamiento → Percepción (coef=0.44, p=0.024).
  - Inteligencia fluida → percepción de información (coef=0.17, p=0.03); Velocidad psicomotora → inteligencia fluida (coef=0.51, p=0.004; efecto indirecto sobre percepción).
  - Memoria de trabajo → velocidad de tecleo (coef=-0.29, p=0.035; mayor MW implica tecleo más rápido).
- Predicción: Random Forest superó a modelos de control (permutación y azar) para todas las habilidades (p<0.007), con los menores RMSE. La regresión múltiple también mejoró significativamente a los controles para velocidad psicomotora y atención selectiva (p<0.007), pero no para todas las habilidades.
- Importancia de características (RF):
  - Texto acumulado fue clave para predecir velocidad psicomotora, velocidad de procesamiento e inteligencia fluida.
  - Variables de procesamiento (cambios de pestaña, visitas de páginas/sitios) fueron más importantes para atención selectiva.
  - Velocidad de tecleo destacó para memoria de trabajo.

## Limitaciones
- Muestra pequeña (n=20) y no representativa (trabajadores del conocimiento), si bien con amplio rango de edad; resultados significativos pese a correcciones conservadoras.
- Señales conductuales solo de ordenador personal (Windows), sin integrar móviles u otros dispositivos; posibles efectos de contexto y hardware (tamaño de pantalla, ergonomía) no modelados explícitamente.
- Conjunto limitado de factores conductuales; la entropía se calculó solo con Shannon y en escala de grises; la métrica de texto acumulado presupone exposición, no necesariamente lectura profunda.
- La velocidad de tecleo se midió únicamente en la Omnibox (autocompletado puede sesgar), por lo que no generaliza a toda escritura.
- Posible sesgo por pausas voluntarias del monitoreo (si bien <5% del tiempo). Podría requerirse mayor duración para estabilizar señales en entornos no controlados.

## Trabajo Futuro
- Ampliar la muestra y diversidad de perfiles (no solo trabajadores del conocimiento) y realizar campañas a gran escala.
- Integrar datos de smartphones, tabletas y señales contextuales para mejorar la predicción multimodal.
- Explorar métricas adicionales: patrones de revisita, secuencias entre aplicaciones, entropía de color/luminancia, scroll y clics, e incluso eye tracking de bajo coste.
- Investigar la reducción del tiempo de monitoreo necesario preservando precisión (privacidad) y estudiar trade-offs.
- Evaluar sistemas adaptativos reales basados en estimación cognitiva, con diseños centrados en privacidad y control del usuario.
- Analizar la predicción de edad y otras variables demográficas asociadas a las habilidades cognitivas.

## Citas Relevantes
- "naturalistic behavioral data can predict the cognitive abilities of individuals with small error rates."
- "Our findings suggest naturalistic interaction data as a novel source for modeling cognitive differences."
- "—RQ1: How is cognitive ability associated with naturalistic digital behaviors? —RQ2: Can we predict cognitive abilities from naturalistic digital behaviors?"
- "The Random Forest model that leveraged all available features produced the lowest RMSE in all cognitive abilities."
- "the finding that simple behavioral data can predict cognitive ability raises severe privacy concerns."
- "we should be careful about the kind of data we allow service providers to collect via Web browsers or other applications."
- "All in all, our research demonstrates the possibility of predicting cognitive abilities from everyday digital activity."

## Notas Adicionales
Datos: 1.44 millones de capturas (media ~75.9k por participante) y 38.1 h de uso total medio en 2 semanas; uso de navegador ~80% del tiempo. Normalidad comprobada (Shapiro–Wilk) para métricas clave; p ajustados por Bonferroni. Los hallazgos respaldan la personalización cognitiva (p. ej., reducir densidad de texto para baja inteligencia fluida, layouts menos distractores para baja atención selectiva, atajos y navegación simplificada para baja memoria de trabajo). La asociación negativa entre memoria de trabajo y tiempo por carácter en Omnibox contextualiza que la tarea requiere recuerdo de URLs/consultas. Los modelos de control por permutación muestran RMSE relativamente bajos debido al rango natural de las puntuaciones, pero aun así inferiores a modelos entrenados sobre datos no permutados.
