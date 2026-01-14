# HEART-felt Narratives: Tracing Empathy and Narrative Style in Personal Stories with LLMs

## Metadata
- **Autores**: Jocelyn Shen, Joel Mire, Hae Won Park, Cynthia Breazeal, Maarten Sap
- **Año**: 2024
- **Keywords**: empathy, narrative style, personal narratives, HEART taxonomy, large language models, GPT-4, Llama 3, LIWC, narrative transportation, structural equation modeling, crowdsourcing, mixed-effects modeling

## Abstract
El trabajo investiga cómo la forma de contar (estilo narrativo) influye en la empatía hacia historias personales. Propone HEART, una taxonomía teórico‑informada de elementos de estilo narrativo relacionados con la empatía, y muestra que LLMs (especialmente GPT‑4) pueden anotar estos elementos a un nivel razonablemente cercano al humano, superando enfoques léxicos en varias dimensiones. Con un estudio de crowdsourcing (N=2,624) y un corpus de 874 historias, el análisis revela que la viveza emocional, el volumen de trama y, en menor medida, el desarrollo de personajes y la acción, se asocian con mayor empatía. Mediante modelos de ecuaciones estructurales, se evidencia que la viveza emocional incrementa la “transportación” narrativa, que a su vez impulsa la empatía. La empatía no es uniforme: varía sustancialmente entre lectores del mismo texto y depende de características del lector (p. ej., empatía rasgo y experiencias similares).

## Contribuciones Principales
- Introduce HEART (Human Empathy and Narrative Taxonomy), una taxonomía teórico‑fundada de estilo narrativo vinculado a la empatía.
- Evalúa la capacidad de LLMs (GPT‑4, Llama 3 8B Instruct) para extraer elementos de HEART y compara con métodos léxicos (LIWC‑22), mostrando ventajas de LLMs en varias dimensiones.
- Recopila el HEART‑felt Stories Dataset: 874 historias personales y 2,624 juicios de empatía, con medidas de estilo, variables del lector y reacciones narrativas.
- Demuestra vías empíricas por las que el estilo narrativo (p. ej., viveza emocional y volumen de trama) promueve la empatía, considerando además transporte narrativo, similitud de experiencias y empatía rasgo.

## Metodología
1) Taxonomía HEART: cuatro categorías de estilo narrativo que pueden inducir empatía: a) Identificación con el personaje (planitud/rotundidad y vulnerabilidad; sujeto emocional: tono y viveza emocional; sujeto cognitivo; sujeto moral/evaluativo; sujeto de acción; percepción corporal/sensorial; referencias temporales); b) Trama (volumen de trama, cambios emocionales, resolución); c) Punto de vista; d) Ambientación/escenario (viveza de la descripción). 2) Corpus: 874 historias personales (filtradas por seguridad y longitud >200 palabras) provenientes de EMPATHICSTORIES y EMPATHICSTORIES++. 3) Anotación experta: 50 historias muestreadas para anotar 12 elementos de HEART con un codebook iterado; métricas de acuerdo: Krippendorff’s alpha (KA), acuerdo par a par (PPA), y correlación de Spearman (ρ). Elementos con bajo acuerdo humano (KA<0.2), como sensaciones corporales y referencias temporales, se excluyen de análisis posteriores. 4) LLMs para extracción de estilo: GPT‑4 (gpt‑4‑0613) y Llama 3 8B Instruct reciben las mismas instrucciones que los anotadores humanos (codebook, Apéndice C). Se compara su acuerdo con el promedio humano en las 50 historias. 5) Comparación con léxicos: mapeo de algunas dimensiones a LIWC‑22 (optimismo, cognición, viveza emocional aproximada, vulnerabilidad del personaje) y contraste de correlaciones con las anotaciones humanas. 6) Estudio con humanos (N=2,624, Prolific): cada participante lee 1 historia y reporta empatía estado (State Empathy Scale), transporte narrativo (TS‑SF), similitud percibida con el narrador, experiencia similar previa, y variables del lector (edad, género, etnia, lectura por placer, empatía rasgo vía SITES y TEQ, estado afectivo previo). Cada historia recibe ≥3 evaluaciones. 7) Análisis estadístico: a) pruebas U de Mann‑Whitney sobre empatía media por historia con corrección Benjamini‑Hochberg; b) modelos mixtos para variación intra‑historia; c) modelos de ecuaciones estructurales (SEM, semopy) para vías desde estilo narrativo → transporte → empatía, controlando por experiencia similar y empatía rasgo; d) prueba de interacción entre empatía rasgo y viveza emocional.

## Resultados Clave
- Concordancia LLMs vs. humanos: GPT‑4 alcanza acuerdos sustanciales en varios rasgos (p. ej., vulnerabilidad del personaje KA≈0.63, ρ≈0.80; tono optimista KA≈0.51, ρ≈0.68; resolución KA≈0.45, ρ≈0.62; desarrollo de personaje KA≈0.44, ρ≈0.62). Llama 3 8B muestra correlaciones positivas pero menores en general.
- LLMs vs. LIWC: GPT‑4 supera a LIWC‑22 en tono optimista, viveza emocional y vulnerabilidad del personaje (esta última con diferencia significativa), mientras que LIWC es competitivo en cognición. Llama 3, aun con menor alineación global, supera sistemáticamente a LIWC en las dimensiones comparadas.
- Efectos del estilo narrativo en empatía: historias con mayor desarrollo de personaje y mayor volumen de trama presentan empatía significativamente más alta (U‑tests con corrección BH; p=0.03 en ambos casos).
- Vías mediadas por transporte: el SEM muestra que la viveza de emociones incrementa significativamente la transportación narrativa, que a su vez impulsa la empatía; la experiencia similar del lector y la empatía rasgo también predicen empatía, aunque la transportación es el mediador más fuerte.
- Personalización: alta variabilidad de empatía entre lectores para la misma historia (desviación estándar > 0; p<0.001). Los modelos mixtos mejoran ajuste al incluir grupos demográficos (LR test p=0.002). Existe interacción significativa Empatía rasgo × Viveza emocional sobre empatía estado (est=0.252, p<0.001): la relación viveza→empatía aumenta con mayor empatía rasgo.
- Error analysis: GPT‑4 tiende a sobre‑estimar evaluaciones y cognición, confundiendo reacciones emocionales con juicios/atribuciones, y recuerdos con procesos cognitivos; Llama 3 sub‑valora rasgos de imaginería (viveza).

## Limitaciones
- Inconsistencias de anotación en ciertos rasgos: sensaciones corporales y referencias temporales muestran bajo acuerdo humano; LLMs muestran errores sistemáticos en cognición y evaluaciones.
- Diseño del estudio humano: cada participante calificó solo una historia; la muestra de Prolific es mayormente blanca; se requiere replicación en poblaciones y formatos narrativos más diversos (texto vs. audio, literario vs. cotidiano).
- Modelado estadístico: se priorizaron modelos interpretables (SEM, mixtos) sobre maximizar rendimiento predictivo; la anotación a nivel global de historia (Likert) podría beneficiarse de granularidad por ocurrencias/frecuencia.
- Generalización de LLMs: aunque cercanos al humano en varias dimensiones, aún fallan en dispositivos estilísticos sutiles (p. ej., lenguaje figurado complejo, distinción fino‑graneada de procesos mentales).

## Trabajo Futuro
- Mejorar el protocolo de anotación (granularidad por frecuencia/segmento, desambiguación de irrealis y múltiples sujetos para sensaciones/tiempo).
- Replicar hallazgos en poblaciones más diversas y con múltiples historias por participante; comparar formatos narrativos (escrito vs. hablado; literario vs. historias personales en línea).
- Integrar los rasgos HEART en modelos transformadores para predicción de empatía y realizar ablaciones sistemáticas.
- Desarrollar herramientas interactivas para apoyar la escritura empática, aprovechando señales de estilo que incrementan transportación y empatía.
- Estudiar personalización: adaptar recomendaciones de estilo al perfil del lector (p. ej., empatía rasgo) y al contexto.
- Profundizar en rasgos difíciles (cognición, evaluaciones) con mejores prompts, señales de cadena de pensamiento y anotación multi‑nivel.

## Citas Relevantes
- "We introduce a novel, theory-based taxonomy, HEART (Human Empathy and Narrative Taxonomy) that delineates elements of narrative style that can lead to empathy with the narrator of a story." 
- "[P]rompting with our taxonomy leads to reasonable, human-level annotations beyond what prior lexicon-based methods can do." 
- "We show that narrative elements extracted via LLMs, in particular, vividness of emotions and plot volume, can elucidate the pathways by which narrative style cultivates empathy towards personal stories." 
- "We additionally show that empathy is personalized, with high variability even for the same story." 
- "LLMs – in particular, GPT-4 – can approximate extracting narrative elements relevant to empathy." 
- "Our work is, to the best of our knowledge, the first to empirically test the effect of character development and plot volume on narrative empathy." 
- "This indicates that the relationship between vividness of emotions and state empathy increases as trait empathy increases."

## Notas Adicionales
El paper presenta HEART como un puente entre teoría narratológica/psicológica y análisis computacional de estilo con LLMs. El corpus total incluye 874 historias y 2,624 evaluaciones de lectores; se usaron medidas validadas (State Empathy Scale, TS‑SF, SITES, TEQ). Métricas de acuerdo entre anotadores humanos y LLMs: KA, PPA, ρ. Comparaciones con LIWC‑22 muestran ventajas de LLMs en varias dimensiones relacionadas con estilo (p. ej., vulnerabilidad y viveza), pero LIWC sigue competitivo en cognición. Los análisis (U‑tests, modelos mixtos, SEM) indican que la viveza emocional impulsa transportación y empatía; el volumen de trama y el desarrollo del personaje también se asocian con mayor empatía. Se observan fuertes diferencias inter‑lector y efectos de personalización (interacciones con empatía rasgo). Recursos: anotaciones, resultados y prompts están disponibles públicamente en https://github.com/mitmedialab/heartfelt-narratives-emnlp. Fecha/arXiv: arXiv:2405.17633v2 (1 Oct 2024). Consideraciones éticas: datos y protocolos con aprobación IRB; el uso responsable de técnicas que potencian la empatía es fundamental para evitar manipulación.
