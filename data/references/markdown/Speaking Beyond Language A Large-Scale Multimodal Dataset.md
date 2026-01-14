# Speaking Beyond Language: A Large-Scale Multimodal Dataset for Learning Nonverbal Cues from Video-Grounded Dialogues

## Metadata
- **Autores**: Youngmin Kim, Jiwan Chung, Jisoo Kim, Sunghyun Lee, Sangkyu Lee, Junhyeok Kim, Cheoljong Yang, Youngjae Yu
- **Año**: 2025
- **Keywords**: multimodal dialogue, nonverbal communication, video-grounded conversations, dataset, VQ-VAE, LLM, SMPL-X, FLAME, facial expressions, body language, active speaker detection, tokenization, codebook, podcasts

## Abstract
El trabajo introduce VENUS, un corpus multimodal a gran escala de diálogos en video con anotaciones temporales de texto, expresiones faciales y lenguaje corporal en 3D, y MARS, un modelo de lenguaje multimodal capaz de comprender y generar texto y señales no verbales en un marco unificado. VENUS se construye a partir de podcasts de dos interlocutores, con transcripción y diarización automáticas, detección de hablante activo y recuperación de parámetros 3D (FLAME para cara, SMPL-X para cuerpo/manos). Las señales no verbales se cuantizan en tokens discretos mediante VQ-VAE y se intercalan con tokens de texto para entrenar MARS con un objetivo de predicción del siguiente token. Los análisis muestran diversidad de gestos/expresiones y alta escalabilidad del conjunto. Experimentalmente, MARS supera a LLMs en cero-shot para producir texto coherente y tokens no verbales alineados (menor PPL y NLL), y los VQ-VAE logran buena reconstrucción con fuertes tasas de compresión.

## Contribuciones Principales
- Presenta VENUS, el primer dataset conversacional multimodal a gran escala con anotaciones temporales de expresiones faciales y lenguaje corporal 3D alineadas con texto.
- Propone MARS, un LLM multimodal que entiende y genera simultáneamente texto y señales no verbales intercaladas como tokens discretos.
- Diseña cuantizadores VQ-VAE específicos para cara y cuerpo, con pérdidas de reconstrucción y de velocidad temporal para preservar dinámica natural.
- Demuestra empíricamente que intercalar tokens no verbales mejora la generación multimodal (texto + no verbal) frente a LLMs sin ajuste.
- Ofrece un análisis de diversidad y distribución de señales no verbales y una validación cuantitativa y cualitativa extensiva.

## Metodología
VENUS (Video with Nonverbal-Cues and Utterance Set):
- Recolección y filtrado: podcasts de YouTube con dos interlocutores. Filtros: personas en miniatura (YOLO), duración por segmentos de 10 min (FPS=25), eliminación del primer minuto, idioma inglés (WhisperX), diarización (PyAnnote) para garantizar exactamente dos hablantes.
- Alineación audio-video: detección de hablante activo (Light-ASD), detección de personas (YOLO) y recorte/alineación por bounding boxes y similitud coseno (MobileNet) para mapear cada enunciado a sus frames.
- Extracción de no verbal: parámetros 3D por frame para cara (EMOCA-v2/FLAME: 50 expresiones + 3 mandíbula = 53 dim) y cuerpo/manos (OSX/SMPL-X: 27 tronco superior + 45 mano izq + 45 mano der = 117 dim); suavizado temporal (Savitzky–Golay). Anotación por enunciado con índices de frames.
- Seguridad y ética: filtrado de contenido con WildGuard y publicación de IDs de video; las reconstrucciones se anonimizan como mallas plantilla.

Cuantización de señales no verbales:
- VQ-VAE separados para cara y cuerpo (encoder/decoder convolucional 1D, factor de downsampling q=8, codebook con EMA). Entradas: secuencias de longitud W=512; salida: códigos discretos por ventana temporal.
- Pérdidas: compromiso de VQ (β=0.02), reconstrucción L1 por componentes (cara: expresiones y mandíbula con ponderaciones; cuerpo: tronco superior y manos), y pérdida de velocidad temporal para continuidad dinámica.
- Selección de hiperparámetros (ablation): codebook=512; mejor embedding dim=8 (cara) y 16 (cuerpo); L1 como pérdida de reconstrucción.

MARS (Multimodal Language Model with nonveRbal-cueS):
- Base: LLaMA 3.2 Instruct y Qwen 2.5 Instruct, con SFT para entender tokens especiales no verbales.
- Representación y entrenamiento: intercalado por timestamp de tokens de palabra y códigos discretos de cara/cuerpo: [xw1, xf1, xb1, xw2, …]. Objetivo autoregresivo unificado: primero predice palabra, luego tokens de cara y cuerpo por paso temporal.
- Prompt de sistema y formato de entrada adaptados para instruir al modelo sobre el significado de <FACE_*> y <BODY_*>.
- Evaluación: texto (PPL, BERTScore, METEOR) y no verbal (NLL por cara/cuerpo), además de análisis cualitativo.

## Resultados Clave
- Escala de VENUS: 869 canales, 27,128 videos, 89,459 diálogos, 1,114,328 turnos, 7,118,654 oraciones, 527,270 palabras únicas; ~21 turnos por diálogo; ~547 frames no verbales por enunciado; ~14,910 horas. Es el mayor dataset conversacional con anotaciones 3D no verbales.
- Diversidad no verbal: clustering t-SNE/DBSCAN revela 7 clusters faciales y 8 corporales, predominio de expresiones neutras/positivas y gestos conversacionales frecuentes (p.ej., manos relajadas, movimientos expresivos).
- VQ-VAE (cuantización): mejores configuraciones con L1 y codebook=512 (cara: dim=8; cuerpo: dim=16). Mejora sobre baselines (Ng et al., 2023; Guo et al., 2024) en VMSE/LVD/w-VL2, preservando diversidad/variación.
- MARS vs LLMs zero-shot: grandes reducciones de PPL y NLL no verbal. Ejemplos: LLaMA 3B (PPL 5477.0) → MARS (926.9); Qwen 3B (PPL 56781.1) → MARS (800.0). BERTScore sube (p.ej., 0.818 → 0.835 con LLaMA 3B). NLL-F/NLL-B bajos (p.ej., 8.057/5.325 en LLaMA 3B; 7.295/4.666 en Qwen 3B), indicando generación consistente de tokens faciales y corporales.
- Cualitativo: MARS produce respuestas de oyente con texto más contextual y gestos/expresiones alineados con el contenido, a veces superando el ground truth en coherencia.

## Limitaciones
- Sesgo de dominio: los datos provienen principalmente de podcasts; escasez de patrones raros (p.ej., llanto o ira intensa).
- Pseudoetiquetado 3D: posibles inexactitudes en EMOCA/OSX; las mallas son pseudo-terreno de verdad.
- Cobertura parcial: no se utilizó todo VENUS en entrenamiento; margen para aprovechar mayor escala.
- Métricas: las actuales (VMSE, LVD, wVL2, NLL) no capturan completamente la naturalidad/adecuación pragmática de la comunicación no verbal.
- Generalización: falta evaluación en dominios fuera de podcasts, multihablante >2, o condiciones adversas (oclusiones, cámaras móviles).

## Trabajo Futuro
- Incorporar más modalidades no verbales (p.ej., prosodia/vocalizaciones) y audio crudo para enriquecer señales paralingüísticas.
- Desarrollar métricas más completas de sincronía semántica y temporal entre texto y no verbal, y evaluaciones humanas controladas.
- Ampliar fuentes y contextos (reuniones, clases, interacciones informales, más culturas) para mayor diversidad y robustez.
- Explorar decodificadores generativos 3D/neurales para síntesis directa de mallas/avatares, y acoplarlo con control de estilo/intención.
- Investigar preentrenamiento multimodal a gran escala con objetivos jerárquicos y aprendizaje de turnos para mejorar diálogo de múltiples vueltas.

## Citas Relevantes
- "Nonverbal communication is integral to human interaction, with gestures, facial expressions, and body language conveying critical aspects of intent and emotion."
- "We introduce MARS, a multimodal language model designed to understand and generate nonverbal cues alongside text, bridging this gap in conversational AI."
- "Our key innovation is VENUS, a large-scale dataset comprising annotated videos with time-aligned text, facial expressions, and body language."
- "Both textual and nonverbal tokens are trained jointly with a unified next-token prediction objective, enabling natural modeling of multimodal dialogues within a single framework."
- "Our dataset is the largest conversational dataset with annotations of nonverbal cues."
- "We believe that our VENUS dataset and MARS model will support a wide range of applications, such as virtual humans and gaming, by enabling the production of nonverbal behaviors in 3D."

## Notas Adicionales
Ética y privacidad: solo se publican IDs de YouTube; las expresiones 3D se representan como mallas plantilla (desidentificación). Se aplica filtrado de seguridad (WildGuard) y se descartan videos con >3 minutos de segmentos dañinos. Anotación: JSON con sincronía por palabra/enunciado, bboxes de hablante activo y parámetros 3D (cara/cuerpo). Entrenamiento: VQ-VAE con q=8 y W=512; MARS con SFT y tokens especiales <FACE_*>, <BODY_*>. Evaluación: VQ-VAE en 997 videos/30,390 enunciados; MARS en 1,000 enunciados de test. El código/dataset están en https://github.com/winston1214/nonverbal-conversation.
