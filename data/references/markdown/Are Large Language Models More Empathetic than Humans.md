# Are Large Language Models More Empathetic than Humans?

## Metadata
- **Autores**: Anuradha Welivita, Pearl Pu
- **Año**: 2024
- **Keywords**: empatía, modelos de lenguaje grandes, GPT-4, LLaMA-2-70B-Chat, Gemini-1.0-Pro, Mixtral-8x7B-Instruct, evaluación humana, estudio entre-sujetos, chi-cuadrado, EmpatheticDialogues, emociones positivas, emociones negativas, generación de respuestas, EPITOME, Prolific

## Abstract
El estudio compara la calidad empática de respuestas generadas por cuatro LLMs (GPT-4, LLaMA-2-70B-Chat, Gemini-1.0-Pro y Mixtral-8x7B-Instruct) frente a un referente humano. Con 1,000 participantes (200 por grupo) evaluando 10,000 respuestas a 2,000 prompts de diálogo que cubren 32 emociones finas (positivas y negativas), los LLMs mostraron una superioridad estadísticamente significativa respecto a humanos. GPT-4 obtuvo el mayor incremento en respuestas calificadas como Good (~31%), seguido por LLaMA-2 (~24%), Mixtral (~21%) y Gemini (~10%). A nivel fino, los modelos difieren por emoción: destacan mejoras en varias emociones positivas y en algunas negativas (p. ej., Apprehensive, Anxious). El trabajo propone un marco de evaluación escalable y extensible para futuras comparaciones sin repetir todo el estudio.

## Contribuciones Principales
- Demuestra, con evaluación humana a gran escala y diseño entre-sujetos, que varios LLMs superan a humanos en calidad empática de respuesta.
- Presenta un marco de evaluación escalable y adaptable, con datos y código públicos, que evita rehacer estudios al incorporar nuevos LLMs.
- Introduce una selección justificada de escala de 3 puntos (Bad/Okay/Good) basada en acuerdo inter-evaluador y correlación con una métrica automática (EPITOME).
- Ofrece análisis fino por 32 emociones, evidenciando variabilidad por modelo y valencia emocional.
- Aporta evidencia estadística robusta (tests χ², tamaño muestral calculado con G*Power) para diferencias entre humanos y LLMs, y entre LLMs entre sí.

## Metodología
Diseño y muestra:
- Estudio entre-sujetos con 5 grupos independientes: humano (baseline) y cuatro LLMs (GPT-4, LLaMA-2-70B-Chat, Gemini-1.0-Pro, Mixtral-8x7B-Instruct); n=200 participantes por grupo (total=1,000) reclutados en Prolific.
- Cada participante evaluó 10 respuestas del mismo origen (ciego a la fuente), totalizando 10,000 evaluaciones.

Datos y estímulos:
- 2,000 prompts de EmpatheticDialogues (≈25K diálogos originales) equilibrados en 32 emociones (positivas y negativas); se usaron los dos primeros turnos y la descripción de la situación para el baseline humano y para disparar respuestas de LLMs.

Instrucciones a LLMs:
- Prompt con definición de empatía (componentes cognitiva, afectiva y compasiva) y restricción de longitud (promedio 28 palabras, máximo 97), idéntico para todos los LLMs.

Selección de escala de evaluación:
- Piloto (n=100) comparó escala 3 puntos (Bad/Okay/Good) vs 5 puntos (Bad/Fair/Okay/Good/Excellent).
- Acuerdo (weighted Cohen’s kappa): 3 puntos=0.2817 (fair) vs 5 puntos=0.1813 (poor).
- Correlación con EPITOME (reacción emocional): 3 puntos=0.1731 vs 5 puntos=0.0811. Se adoptó la escala de 3 puntos.

Procedimiento de evaluación:
- Los participantes recibieron un tutorial sobre empatía (dimensiones cognitiva, afectiva y compasiva) con ejemplos de alta empatía del dataset.
- Calificaron cada respuesta como Bad/Okay/Good en relación con cómo responderían en situaciones similares.

Control de calidad y sesgos:
- Criterios Prolific: dominio de inglés, ≥100 tareas previas, ≥95% aprobación.
- Cuestionario TEQ (Toronto Empathy Questionnaire) para medir propensión empática; distribución comparable entre grupos.
- 8 ítems inversos en TEQ como checks de atención; 60% sin errores en ítems inversos; solo 2.3% con >50% de errores.
- Balance demográfico por género y grupos de edad; reporte de países y etnias por grupo (distribuciones comparables).

Análisis estadístico y tamaño muestral:
- Prueba chi-cuadrado de independencia para proporciones de Bad/Okay/Good (global, por valencia y por emoción).
- G*Power: efecto medio (W=0.3), α=0.05, 1-β=0.95 ⇒ mínimo total 253 (≥51 por grupo); para análisis por valencia, ≥102 por grupo. Se usaron 200 por grupo.

## Resultados Clave
- Global (32 emociones combinadas): todos los LLMs superan a humanos en Good (χ² y p significativos). Incrementos en Good vs humano: GPT-4 ≈31% (χ²=96.77, p<.001), LLaMA-2 ≈24% (χ²=54.40, p<.001), Mixtral ≈21% (χ²=42.36, p<.001), Gemini ≈10% (χ²=8.85, p<.01).
- Por valencia: positivos y negativos por separado muestran superioridad de LLMs en Good; excepción: Gemini no mejora significativamente en positivos (↑=5.95%, χ²=1.54, p>.05). En positivos: GPT-4 ≈36% (χ²=64.10, p<.001); LLaMA-2 ≈28% (χ²=38.40, p<.001); Mixtral ≈25% (χ²=29.21, p<.001). En negativos: GPT-4 ≈27% (χ²=36.78, p<.001); LLaMA-2 ≈20% (χ²=19.00, p<.001); Mixtral ≈17% (χ²=15.15, p<.001); Gemini ≈13% (χ²=8.02, p<.01).
- Comparaciones pareadas (Bad/Okay/Good): todos los LLMs difieren de humanos (p<.001) en global; GPT-4 > Gemini y > Mixtral (global y positivos); GPT-4 > LLaMA-2 (global); LLaMA-2 > Gemini (global y positivos); Gemini < Mixtral (global y positivos). En negativos, varias comparaciones entre LLMs no son significativas.
- Análisis fino por emoción (ejemplos con mejoras significativas en Good vs humanos):
  - Positivas: GPT-4 en Impressed (↑56%, χ²=10.62, p<.01), Surprised (↑79%, χ²=10.33, p<.01), Grateful (↑65%, χ²=8.36, p<.01), Proud (↑50%, χ²=7.7, p<.01), Confident (↑44%, χ²=6.86, p<.01), Joyful (↑42%, χ²=6.34, p<.05), Excited (↑47%, χ²=5.41, p<.05). LLaMA-2 en Grateful, Surprised, Proud, Excited, Hopeful, Prepared. Mixtral en Proud, Grateful, Excited.
  - Negativas: mejoras concentradas en pocas emociones: Afraid (GPT-4 ↑46%, χ²=3.91, p<.05; LLaMA-2 ↑50%, χ²=4.66, p<.05), Apprehensive (GPT-4 ↑104%, χ²=20.72, p<.001; Gemini ↑60%, χ²=6.23, p<.05; LLaMA-2 ↑52%, χ²=4.57, p<.05), Anxious (GPT-4 ↑75%, χ²=9.2, p<.01; LLaMA-2/Gemini ↑63%, χ²=6.22, p<.05; Mixtral ↑50%, χ²=3.85, p<.05), Annoyed (GPT-4 ↑59%, χ²=6.62, p<.05; Mixtral ↑52%, χ²=4.97, p<.05).
- Estudio de caso: en un prompt Sentimental, la respuesta humana fue evaluada Bad por centrarse en sí misma; las de LLMs fueron Good al reconocer y validar la emoción y aportar soporte lingüístico empático.

## Limitaciones
- Uso de una escala de 3 puntos reduce granularidad frente a 5 o 7 puntos; si bien mostró mayor acuerdo entre evaluadores y mejor alineación con EPITOME, limita la resolución de matices.

## Trabajo Futuro
- Mejorar el desempeño en emociones negativas incorporando ejemplos más diversos y matizados y/o ajustando algoritmos para captar sutilezas afectivas.
- Ampliar el marco evaluativo con nuevas versiones de LLMs sin repetir el estudio completo, aprovechando los artefactos liberados.
- Explorar métricas complementarias y escalas híbridas que mantengan acuerdo alto con mayor granularidad.
- Analizar sensibilidad por subpoblaciones y sesgos (grupos subrepresentados) y monitoreo continuo en despliegues sensibles (p. ej., salud mental).
- Evaluar contextos conversacionales más largos (más de 2 turnos) y distintos dominios de interacción.

## Citas Relevantes
- "Our findings reveal a statistically significant superiority of the empathetic responding capability of LLMs over humans."
- "GPT-4 emerged as the most empathetic, marking ≈31% increase in responses rated as Good compared to the human benchmark."
- "All four LLMs outperformed the human baseline across both positive and negative emotions in the number of Good ratings received."
- "This type of study design offers distinct advantages over a within-subjects approach."
- "The suggested evaluation framework offers a scalable and adaptable approach for assessing the empathy of new LLMs, avoiding the need to replicate this study’s findings in future research."
- "Empathy is a multifaceted construct, encompassing cognitive, affective, and compassionate counterparts."
- "The 3-point scale achieved a kappa score of 0.2817, indicating fair agreement, whereas the 5-point scale scored 0.1813, indicating poor agreement."
- "We plan to publicly release the new artifacts generated in this study, including the responses from the four LLMs and the participants’ empathy ratings, under the CC BY-NC 4.0 license."

## Notas Adicionales
Detalles adicionales: 
- Muestras: 2,000 prompts equilibrados en 32 emociones (≈44% positivas, ≈56% negativas); 10,000 evaluaciones totales; 23.24 tokens promedio por prompt; longitud de respuestas (promedio): humanos 28.37, GPT-4 34.94, LLaMA-2 53.45, Gemini 53.99, Mixtral 61.35.
- Análisis estadístico: además de χ² global por categorías, se usó binarización Good vs (Bad+Okay) para algunos contrastes de porcentaje de ganancia.
- Diseño entre-sujetos: mitiga efectos de arrastre y de orden, y permite incorporar nuevos LLMs sin invalidar resultados previos.
- Consideraciones éticas: cautela en dominios sensibles; sesgos potenciales; transparencia sobre la naturaleza de respuestas de LLMs; liberación pública de datos y ratings (CC BY-NC 4.0).
- Observación metodológica: los LLMs fueron explícitamente instruidos con una definición de empatía; el baseline humano proviene de diálogos naturales del dataset, lo que puede favorecer la consistencia empática de LLMs bajo ese prompt. Esto no se reporta como limitación formal, pero es un matiz interpretativo.
- Gemini-1.0-Pro mostró mejoras globales y en emociones negativas, pero no alcanzó significancia en positivas; GPT-4 fue consistentemente el mejor en global y positivos; en negativos las diferencias entre LLMs fueron menores (varias comparaciones no significativas).
