# Emotional RAG: Enhancing Role-Playing Agents through Emotional Retrieval

## Metadata
- **Autores**: Le Huang, Hengzhi Lan, Zijun Sun, Chuan Shi, Ting Bai
- **Año**: 2024
- **Keywords**: Emotional RAG, Role-playing agent, Large language models, Retrieval Augmented Generation, Mood-Dependent Memory

## Abstract
El trabajo propone Emotional RAG, un marco de recuperación de memoria consciente de las emociones para agentes de role-playing basados en LLM. Motivado por la teoría psicológica de la Memoria Dependiente del Estado de Ánimo, el enfoque recupera recuerdos que son simultáneamente semántica y emocionalmente congruentes con la consulta del usuario. Para ello, codifica por separado semántica y emoción tanto de la consulta como de los fragmentos de memoria, y fusiona ambas señales mediante dos estrategias de recuperación (combinación y secuencial). En tres datasets de role-playing, Emotional RAG mejora la fidelidad de la personalidad (BFI y MBTI) frente a RAG convencional, ofreciendo evidencia computacional a favor de la teoría de la congruencia emocional.

## Contribuciones Principales
- Introduce una formulación de recuperación de memoria con conciencia emocional para agentes de role-playing, inspirada en la teoría de Memoria Dependiente del Estado de Ánimo de Bower.
- Propone Emotional RAG, que combina relevancia semántica y congruencia emocional mediante dos estrategias de recuperación: combinación (suma y multiplicación) y secuencial (primero semántica o primero emoción).
- Demuestra empíricamente en tres datasets (InCharacter, CharacterEval y Character-LLM) que incorporar señales emocionales en RAG mejora el mantenimiento de los rasgos de personalidad de los agentes, reforzando la validez de la teoría psicológica subyacente.

## Metodología
Arquitectura general con cuatro componentes: (1) Codificación de la consulta: se obtiene un vector semántico con un modelo de embeddings (bge-base-zh-v1.5, 768d) y un vector emocional de 8 dimensiones (alegría, aceptación, miedo, sorpresa, tristeza, disgusto, ira, anticipación) puntuado por GPT-3.5 con una plantilla de evaluación; las intensidades van de 1 a 10. (2) Codificación de memoria: cada fragmento de memoria (pares QA históricos por personaje) se codifica de forma análoga con un embedding semántico y un vector emocional de 8 dimensiones (vía GPT-3.5 y la misma plantilla). (3) Recuperación emocional: se calcula similitud semántica (distancia euclídea o coseno) y similitud emocional (1 − coseno). Se define un puntaje final con dos familias de estrategias: combinación (C-A: suma de distancias; C-M: multiplicación) y secuencial (S-S: seleccionar por semántica y reordenar por emoción; S-E: seleccionar por emoción y reordenar por semántica). Se seleccionan los 10 fragmentos con menor puntaje final (mayor similitud conjunta). (4) Generación de respuesta: se construye un prompt con el perfil del personaje, la consulta y los fragmentos recuperados, y se genera la respuesta con el LLM. Evaluación: tres LLMs (ChatGLM-6B, Qwen-72B, GPT-3.5) y tres datasets; las personalidades ground truth provienen de Personality Database. Los agentes responden cuestionarios abiertos para BFI y MBTI; GPT-3.5 evalúa las respuestas para obtener predicciones de personalidad, comparadas con ground truth mediante Acc(Dim), Acc(Full), MSE y MAE.

## Resultados Clave
- InCharacter (BFI, Qwen-72B): Emotional RAG mejora Acc(Dim) de 0.6815 a 0.7261, Acc(Full) de 0.0938 a 0.2500, MSE de 0.1433 a 0.1269 y MAE de 0.3024 a 0.2878.
- InCharacter (MBTI, Qwen-72B): mejora Acc(Dim) de 0.7438 a 0.7934, Acc(Full) de 0.3438 a 0.4688, MSE de 0.1230 a 0.1156 y MAE de 0.2920 a 0.2900.
- InCharacter (BFI, GPT-3.5): mantiene Acc(Dim) y Acc(Full), pero reduce MSE (0.1496→0.1475) y MAE (0.3121→0.3082).
- InCharacter (MBTI, GPT-3.5): Acc(Full) desciende (0.5000→0.4375); MAE mejora levemente (0.2965→0.2927); MSE varía mínimo.
- InCharacter (MBTI, ChatGLM-6B): Acc(Full) mejora (0.2188→0.2812); MSE/MAE cambian marginalmente.
- CharacterEval (MBTI, ChatGLM-6B): Acc(Dim) sube de 0.5161 a 0.5887 y Acc(Full) de 0.0323 a 0.0645; MAE mejora (0.3757→0.3736).
- CharacterEval (MBTI, Qwen-72B): Acc(Dim) de 0.5968 a 0.6210 y Acc(Full) de 0.0968 a 0.1290; ligeros aumentos en MSE/MAE.
- CharacterEval (MBTI, GPT-3.5): Acc(Full) se duplica (0.0645→0.1290) con mejoras en MSE (0.1720→0.1560) y MAE (0.3655→0.3477), aunque Acc(Dim) baja levemente.
- Character-LLM (MBTI, ChatGLM-6B): mejoras sustanciales en Acc(Dim) (0.5556→0.6944), Acc(Full) (0.1111→0.3333), MSE (0.1330→0.1125) y MAE (0.3277→0.2987).
- Character-LLM (MBTI, Qwen-72B): Acc(Dim) crece (0.6667→0.6944); Acc(Full) estable; MSE/MAE ligeramente mejores.
- Character-LLM (MBTI, GPT-3.5): Acc(Full) mejora (0.2222→0.3333) y MSE/MAE se reducen.
- Análisis de estrategias (Qwen-72B, InCharacter): todas las variantes de Emotional RAG superan a RAG convencional salvo C-A en BFI; S-S (secuencial, primero semántica) rinde mejor en BFI, mientras C-A (combinación por suma) es superior en MBTI.
- Casos cualitativos: la recuperación congruente con el estado emocional produce respuestas más empáticas y naturales (p. ej., ante una ruptura o la emoción por ver el mar), evitando inconsistencias emocionales que surgen al considerar solo la semántica.

## Limitaciones
- El marco opera sobre un mecanismo de memoria "intuitivo"; no se exploran organizaciones de memoria más avanzadas (reconocido por los autores).
- La extracción de emoción depende de GPT-3.5 y de una escala de 8 dimensiones discretas; no se analizan variabilidad, costo o alternativas de modelado emocional.
- La selección de top-10 fragmentos y la elección de métricas/distancias no se ablan detalladamente.
- En algunos escenarios con GPT-3.5, las mejoras son marginales o mixtas (p. ej., caída en Acc(Full) de MBTI en InCharacter), lo que sugiere sensibilidad al backbone.
- No se discuten explícitamente posibles sesgos de las etiquetas de personalidad (provenientes de un sitio de votación) ni del uso de GPT-3.5 como evaluador.

## Trabajo Futuro
- Incorporar el factor emocional en organizaciones y esquemas de recuperación de memoria más avanzados (expresado por los autores).
- No especificado explícitamente más allá de lo anterior.

## Citas Relevantes
- "people recall an event better if they somehow reinstate during recall the original emotion they experienced during learning"
- "we propose a novel emotion-aware memory retrieval framework, termed Emotional RAG, which recalls the related memory with consideration of emotional state in role-playing agents"
- "Two kinds of flexible retrieval strategies, i.e., combination strategy and sequential strategy, are proposed to fuse memory semantic and emotional states during the retrieval process."
- "Extensive experiments on three representative role-playing datasets demonstrate that our Emotional RAG framework significantly outperforms the method without considering the emotional factor in maintaining the personality traits of role-playing agents."
- "This provides evidence to further reinforce the Mood-Dependent Memory theory in psychology."

## Notas Adicionales
Arquitectura: cuatro componentes (codificación de consulta, codificación de memoria, recuperación emocional, generación de respuesta). Emociones: vector de 8 dimensiones (Plutchik) con intensidades 1–10, obtenidas por GPT-3.5 mediante prompt diseñado. Semántica: embeddings bge-base-zh-v1.5 (768d). Similitudes: distancia euclídea/coseno para semántica; 1−coseno para emociones; fusión por combinación (suma/multiplicación) o re-ranqueo secuencial. Recuperación: top-10 fragmentos con mayor similitud conjunta. LLMs: ChatGLM-6B, Qwen-72B, GPT-3.5. Datasets: InCharacter (32 roles; memoria media 337), CharacterEval (31 roles; memoria media 113), Character-LLM (9 roles; memoria 1000). Evaluación: BFI y/o MBTI; ground truth de Personality Database; GPT-3.5 evalúa respuestas de los agentes a cuestionarios. Hallazgos: Emotional RAG mejora especialmente Acc(Full) en varias combinaciones dataset-modelo; Qwen-72B muestra ganancias más consistentes; GPT-3.5 presenta mejoras más sutiles o mixtas. Código: https://github.com/BAI-LAB/EmotionalRAG. Relación con psicología: resultados ofrecen respaldo computacional a la teoría de Memoria Dependiente del Estado de Ánimo. Aspectos no aclarados: detalles de idioma/dominio en embeddings frente a datasets bilingües; sensibilidad a hiperparámetros como k=10.
