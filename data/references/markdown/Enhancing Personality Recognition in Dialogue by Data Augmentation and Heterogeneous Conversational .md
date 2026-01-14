# Enhancing Personality Recognition in Dialogue by Data Augmentation and Heterogeneous Conversational Graph Networks

## Metadata
- **Autores**: Yahui Fu, Haiyue Song, Tianyu Zhao, Tatsuya Kawahara
- **Año**: 2024
- **Keywords**: Big Five, reconocimiento de personalidad, diálogo, data augmentation, interpolación, HC-GNN, redes gráficas conversacionales heterogéneas, LUKE, GATv2, RGCN, RealPersonaChat

## Abstract
El trabajo aborda dos retos en el reconocimiento de personalidad en diálogo: (1) la escasez de hablantes en los corpus existentes, que limita la robustez del modelo, y (2) la dificultad de modelar simultáneamente dependencias entre interlocutores e intra-dependencias dentro de cada hablante. Para (1), proponen un método de aumento de datos mediante interpolación de rasgos de personalidad y contenido dialógico entre dos diálogos reales, generando tanto texto sintético como etiquetas Big Five continuas. Para (2), introducen una red gráfica conversacional heterogénea (HC-GNN) que modela por separado interdependencias (influencia contextual del interlocutor) e intradependencias (rasgos intrínsecos del hablante). En el corpus RealPersonaChat (japonés), su método mejora de forma significativa a los baselines en escenarios de monólogo y diálogo.

## Contribuciones Principales
- Proponen un método de aumento de datos por interpolación que genera diálogos sintéticos y etiquetas Big Five continuas a partir de dos puntos de datos existentes.
- Presentan HC-GNN, una red gráfica conversacional heterogénea que modela de forma independiente interdependencias entre interlocutores e intradependencias dentro del hablante.
- Demuestran empíricamente, en RealPersonaChat, que aumentar la diversidad de hablantes mejora el reconocimiento de personalidad en monólogo y diálogo, y que HC-GNN supera a modelos homogéneos y heterogéneos tradicionales (GCN, GATv2, RGCN).

## Metodología
Datos y análisis preliminar: RealPersonaChat (RPC) con 14,000 diálogos (421,203 enunciados) en japonés de 233 participantes (puntuaciones Big Five 1–7 normalizadas a 0–1). Se observan correlaciones significativas entre todos los pares de rasgos (p < .05), e.g., N–E: −0.49, E–O: 0.47.
Aumento por interpolación (texto y etiquetas):
- Selección de dos diálogos D1 y D2 del entrenamiento, con etiquetas y1, y2 (vector en R^5 de Big Five del hablante iniciador).
- Segmentación de cada diálogo en chunks de t = 3 turnos: D = {c1, c2, ..., cl}.
- Fusión estocástica por ratio β ~ Uniform(0,1) a nivel de chunk: cada chunk csyn_i se toma de D1 con prob. β o de D2 con prob. 1−β. En monólogo, la unidad es el enunciado.
- Interpolación de etiquetas continuas: y_syn = β y1 + (1−β) y2.
- Variantes: (i) β fijo=0.5 vs β aleatorio (mejor diversidad); (ii) D1 y D2 del mismo hablante (y1=y2) vs de distintos hablantes (y1 iid∼ y2; crea "nuevos" hablantes sintéticos); (iii) truncado de longitud l' ~ Uniform(t_min=2, |D_syn|) para entrenamiento con contextos variables y permitir reconocimiento temprano.
Modelado conversacional heterogéneo (HC-GNN):
- Codificación de enunciados con LUKE (BERT-like); se usa el CLS: h_u = LUKE(u) ∈ R^d.
- Grafo dirigido y etiquetado con 4 tipos de relación: spk a→a, spk b→b (intra; rasgos innatos) y spk b→a, spk a→b (inter; rasgos adquiridos por influencia del interlocutor). En experimentos de diálogo sólo se usan spk a→a y spk b→a para predecir al iniciador.
- Para cada tipo de relación: GATv2 con atención multi-cabeza para agregar vecinos, seguido de GCN para profundizar la interacción. Cada relación se modela con parámetros independientes (no compartidos entre tipos), a diferencia de RGCN tradicional.
- Fusión entre grafos (innatos vs adquiridos) con self-attention sobre las salidas por relación.
Predicción multitarea de Big Five:
- Cinco cabezas lineales (una por rasgo) sobre la representación fusionada; tareas de regresión con pérdida MAE, optimización con Adam (lr 1e−5), scheduler lineal (warmup=150), early stopping (3 épocas sin mejora). Batch: 128 (MLP) y 32 (GNN). Métricas: Accuracy, Balanced Accuracy, Pearson, Spearman. Umbral binario por rasgo = mediana del entrenamiento.
Particionado:
- Monólogo: split estricto por hablante (8:1:1) repetido 100 veces; se fija el mejor aproximado.
- Diálogo: sólo el hablante iniciador no se repite entre splits; se predice sólo su personalidad.

## Resultados Clave
- Monólogo (MLP + LUKE): el aumento de datos mejora notablemente. Accuracy promedio: 57.4% (original) → 61.2% (+500k sintéticos). Balanced Accuracy: 55.6% → 60.4%.
- Correlaciones (monólogo): aumento mejora Pearson/Spearman en varios rasgos, especialmente N y A. E (Extraversión) sigue siendo difícil (p.ej., Pearson cercano a 0 en varios tamaños), atribuido a diálogos de primer encuentro.
- Variantes de aumento:
  - β aleatorio supera a β=0.5 (accuracy 61.2% vs 59.3%; balanced 60.4% vs 58.4%).
  - Combinar diálogos de distintos hablantes supera a mismo hablante (accuracy 61.2% vs 57.3%; balanced 60.4% vs 58.1%); además, induce distribución de etiquetas más continua.
  - Entrenar con longitudes de contexto variables mejora reconocimiento temprano: con sólo 2 turnos de test, balanced 58.2% (entrenando con contextos variables) vs 55.5% (entrenando con contextos completos); el desempeño con contexto completo sigue siendo el mejor (balanced 60.4%).
- Diálogo (concatenación simple de contexto): usar diálogo sin modelado gráfico tiende a degradar frente a monólogo (p.ej., MLP diálogo avg balanced 54.3% vs 55.6% en monólogo).
- Diálogo (modelos gráficos): HC-GNN supera a GCN, GATv2 y RGCN. En datos originales, avg balanced: HC-GNN 56.4% (vs RGCN 54.5%, GAT 53.2%, GCN 47.7%).
- Diálogo + aumento: con HC-GNN, el mejor balanced alcanza 58.6% (+50k), aunque por debajo de monólogo +500k (60.4%). El recorte de datos (sólo personalidad del iniciador) limita ganancias máximas.
- Correlaciones (diálogo): HC-GNN mejora con aumento, p.ej., con +500k: Pearson (N .426, O .411, C .223) y Spearman (N .439, O .315), varios con p < .05.

## Limitaciones
- Dificultad persistente para predecir Extraversión en escenarios de primer encuentro (baja señal conductual explícita).
- El contexto conversacional no aporta grandes mejoras de forma consistente; concatenar turnos sin modelado adecuado puede perjudicar.
- En el setting de diálogo se predice sólo al hablante iniciador, reduciendo a la mitad los datos útiles para aumento.
- Tamaño y dominio del corpus (japonés, 233 hablantes) limitan la generalización a otros idiomas y dominios.
- Resultados sensibles a la aleatoriedad del proceso de síntesis (β y muestreo de chunks); los mejores tamaños de aumento varían por rasgo y métrica.
- Experimentos de una sola ronda por configuración; ausencia de desviaciones estándar/intervalos de confianza.

## Trabajo Futuro
- Profundizar en el modelado de contexto en diálogo para obtener beneficios consistentes (p.ej., enriquecer relaciones, dinámicas temporales, memoria a largo plazo).
- Abordar específicamente la detección de Extraversión en interacciones de primer encuentro (señales paralingüísticas, multimodalidad).
- Investigar estrategias de aumento que eviten pérdida de datos al enfocarse sólo en el iniciador (p.ej., formulaciones multitarea o co-predicción con desambiguación de hablante).
- Evaluar en más corpora e idiomas y estudiar la transferencia/robustez cross-domain.
- Análisis ablation y sensibilidad más exhaustivos sobre β, tamaño de chunk t y políticas de truncado.

## Citas Relevantes
- "We propose a data augmentation method for personality recognition by interpolation from any two existing data points."
- "This bridges the gap between the discrete distribution in the corpus and the continuous distribution in reality."
- "We propose a heterogeneous conversational graph neural network (HC-GNN) to independently model both the interdependencies among interlocutors, as well as the intra-dependencies within the speaker in dialogues."
- "We believe this may be due to our dataset being based on first-meeting spontaneous situations, where people tend not to exhibit extrovert traits explicitly."
- "Merely concatenating utterances between two speakers is not an effective method for modeling the interactions between interlocutors."
- "Experimental results using the RealPersonaChat corpus demonstrate that increasing speaker diversity significantly improves personality recognition in both monologue and dialogue settings."

## Notas Adicionales
Código disponible: https://github.com/fuyahuii/Personality-Recognition-on-RealPersonaChat. Se utiliza LUKE japonés para la codificación de enunciados; HC-GNN emplea GATv2 por relación + GCN y fusión por self-attention. Las correlaciones entre rasgos en el dataset (p < .05) motivan el enfoque multitarea. Métricas de clasificación se derivan con umbral mediano; la tarea primaria es regresión con MAE. En diálogo, sólo se usan relaciones spk a→a y spk b→a para predecir al iniciador.
