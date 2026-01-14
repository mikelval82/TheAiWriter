# Towards Empathetic Open-domain Conversation Models: a New Benchmark and Dataset

## Metadata
- **Autores**: Hannah Rashkin, Eric Michael Smith, Margaret Li, Y-Lan Boureau
- **Año**: 2019
- **Keywords**: empathetic dialogue, open-domain conversation, dataset, benchmark, emotion recognition, retrieval models, generative models, Transformer, BERT, human evaluation

## Abstract
El trabajo introduce un nuevo benchmark y un conjunto de datos llamado EMPATHETICDIALOGUES (ED) con ~25k diálogos sobre situaciones personales asociadas a 32 emociones, diseñados para evaluar y entrenar modelos de conversación que respondan con empatía. Muestran que modelos de diálogo preentrenados en grandes corpus de Internet resultan poco empáticos, y que emplear ED como candidatos de respuesta o realizar fine-tuning en ED mejora de forma clara las valoraciones humanas de empatía, relevancia y fluidez. Además, exploran adaptaciones simples (p. ej., prepender etiquetas de clasificadores externos de emoción o tema) que pueden aumentar la empatía sin reentrenamiento extenso.

## Contribuciones Principales
- Presentan EMPATHETICDIALOGUES, un conjunto de 24,850 diálogos uno-a-uno basados en situaciones reales con 32 etiquetas emocionales balanceadas.
- Proponen un benchmark para evaluar la capacidad de los sistemas de diálogo de responder con empatía.
- Demuestran que usar ED como pool de candidatos o hacer fine-tuning en ED mejora sustancialmente la empatía percibida por humanos frente a modelos solo preentrenados en Reddit.
- Evalúan arquitecturas de recuperación (Transformer, BERT) y generativas (Transformer), con técnicas simples de adaptación: candidates in-domain, fine-tuning y prepending de predicciones externas (emoción/tema).
- Analizan costos computacionales, mostrando que el fine-tuning en ED requiere recursos mínimos comparado con el preentrenamiento masivo.

## Metodología
Diseño del dataset: diálogos crowdsourced en ParlAI/MTurk con 810 trabajadores (EE. UU.). Para cada conversación, un 'Speaker' escribe una breve descripción de una situación personal asociada a una emoción (entre 32 etiquetas agregadas de esquemas previos) y luego inicia un diálogo; un 'Listener' responde sin ver la etiqueta ni la descripción original. Cada diálogo tiene 4–8 turnos (media 4.31), longitud media de turno 15.2 palabras; las descripciones de situación tienen ~19.8 palabras. Se asegura cobertura balanceada de emociones mediante selección guiada de etiquetas menos usadas. Partición sin fugas por situación: train/val/test = 19,533 / 2,770 / 2,547 conversaciones.
Modelos: (1) Recuperación: dos encoders (Transformer o BERT) para contexto y candidatos; selección por producto punto hx·hy. Candidatos en inferencia: ED, DailyDialog (DD) o 1M de Reddit (R). (2) Generativo: Transformer encoder–decoder con búsqueda por beams diversos. Preentrenamiento: dump de 1.7B conversaciones de Reddit; BERTbase para variantes BERT. Fine-tuning: sobre ED con ventana de 4 turnos (media del corpus). (3) Señales externas: prepending del top-1 (y variantes top-3/5) de un clasificador de emociones entrenado con descripciones de ED (fastText) o de un clasificador de temas (20-Newsgroups). También se exploran variantes multitarea y ensembling con DeepMoji (en apéndice).
Evaluación: métricas automáticas (retrieval P@1,100; BLEU; generativo: perplexity, BLEU) y evaluación humana en MTurk (≥100 juicios/modelo) con escalas Likert (1–5) para Empatía, Relevancia y Fluidez.

## Resultados Clave
- Pretrained (retrieval, candidatos R): baja empatía humana (2.82) y baja relevancia (3.03); generativo preentrenado aún peor en empatía (2.31).
- Usar solo candidatos ED con modelo preentrenado mejora de inmediato: empatía 3.45 (Transformer) y 3.49 (BERT), relevancia ~3.5–3.6.
- Fine-tuning en ED: mejora en todas las métricas. Retrieval (Transformer): P@1,100 = 56.90 (vs 43.25 solo candidatos ED), AVG BLEU = 5.88; empatía humana 3.76. Retrieval (BERT): P@1,100 = 65.92; empatía 3.71. Generativo: PPL 21.24 (vs 27.96 preentrenado), AVG BLEU 6.27; empatía 3.25.
- Variantes de mayor capacidad: generativo 5 capas obtiene PPL 16.55 y BLEU 8.06 tras fine-tuning; retrieval Transformer grande P@1,100 60.44; empatía humana 3.81.
- Señales externas (prepended labels) con BERT: TopicPrepend-1 alcanza empatía 4.03 y EmoPrepend-5 4.08, aproximándose a la respuesta humana (4.19). En modelos pequeños, el efecto es menor/inconsistente.
- Generalización: fine-tuning en ED mejora P@1,100 en DailyDialog (+5–7 pp) y disminuye ligeramente en Reddit (−2–3 pp). BLEU sube +0.2–0.5 en DD y R.
- Coste computacional: el fine-tuning en ED requiere ~0.5–1 h y 1–8 GPUs, comparado con días y múltiples GPUs para el preentrenamiento masivo.

## Limitaciones
- Datos crowdsourced con hablantes de EE. UU.; posible sesgo demográfico/estilístico y dominio.
- Diálogos cortos y sólo texto; no se consideran señales multimodales ni prosodia.
- Cobertura emocional balanceada artificialmente; distribución no refleja frecuencias naturales.
- La empatía se infiere sin acceso a la etiqueta ni a la descripción de situación; puede limitar el techo de desempeño.
- Métricas automáticas (p. ej., BLEU) correlacionan pobremente con juicios humanos en diálogo.
- Dependencia de candidatos in-domain en retrieval; transferibilidad fuera de dominio es limitada.
- Idioma inglés únicamente; posibles cuestiones éticas y de seguridad no profundizadas.

## Trabajo Futuro
- Integrar empatía con objetivos informativos y mantenimiento de tema en sistemas mixtos (task-oriented + chit-chat).
- Extender a contextos multimodales y diálogos más largos/persistentes con memoria de usuario/persona.
- Mejorar control explícito de señales afectivas (detección conjunta de emoción + generación controlada) con menor sesgo.
- Ampliar cobertura lingüística y demográfica; estudiar robustez y equidad.
- Evaluaciones humanas más ricas (p. ej., usuarios finales, escenarios sensibles) y métricas automáticas mejor correlacionadas.
- Investigar seguridad y mitigación de respuestas inapropiadas en presencia de emociones intensas.

## Citas Relevantes
- "This work proposes a new benchmark for empathetic dialogue generation and EMPATHETICDIALOGUES, a novel dataset of 25k conversations grounded in emotional situations."
- "Our experiments indicate that dialogue models that use our dataset are perceived to be more empathetic by human evaluators, compared to models merely trained on large-scale Internet conversation data."
- "We propose two simple ways to leverage our dataset to improve those models: use utterances from our training data as candidate responses in a retrieval model at inference time, and fine-tune the model on our task."
- "A desirable trait in a human-facing dialogue agent is to appropriately respond to a conversation partner that is describing personal experiences... a skill we refer to as empathetic responding."
- "The distribution of emotion label prompts is close to evenly distributed, with a few that are selected slightly more/less often."
- "Fine-tuning on ED data improves performance on DAILYDIALOG ... [and] the slight decrease of performance on R is not surprising..."

## Notas Adicionales
Datos: 24,850 conversaciones, 32 emociones; media 4.31 turnos/diálogo; 810 participantes; splits 19,533/2,770/2,547. Modelos no reciben etiqueta ni descripción de situación, solo contexto textual previo. Arquitecturas: Transformers (4–5 capas), BERTbase (768-d), preentrenados en 1.7B conversaciones de Reddit. Incluir ED como pool de candidatos en retrieval y el fine-tuning en ED son intervenciones simples y efectivas. Código y datos públicos en ParlAI/GitHub. Los resultados muestran mejoras consistentes en empatía percibida, con recursos adicionales mínimos para el fine-tuning.
