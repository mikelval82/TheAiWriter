# Exploring behavior patterns in human and machine interactions

## Metadata
- **Autores**: Ping Zhao, Yunjie Wei, Shouyang Wang
- **Año**: 2025
- **Keywords**: Machine behavior, Narratives, Social dilemma, Multivariable Granger causality, Frequency response

## Abstract
El artículo propone un marco basado en la teoría de la dependencia de la respuesta para analizar patrones de comportamiento en interacciones humano‑máquina. Modela la interacción como un sistema de múltiples entradas y salidas (MIMO) que procesa señales de decisión en múltiples canales, comparando la conectividad (narrativas interactivas) y la magnitud de la respuesta (frecuencia) entre agentes. En un estudio empírico con partidas de Go, contrasta AlphaGo y jugadores profesionales humanos, hallando estructuras de conectividad similares pero diferencias en magnitudes de respuesta, especialmente en pares estímulo‑respuesta específicos. Integrando el análisis estático y dinámico, concluye que AlphaGo es más sensible a cambios de payoff de largo plazo que los profesionales humanos. El marco muestra cómo técnicas transdisciplinarias (análisis espectral, causalidad de Granger multivariable y respuesta en frecuencia) pueden ofrecer interpretaciones objetivas y útiles para ética de IA y comprensión del comportamiento de máquinas.

## Contribuciones Principales
- Propone un marco operativo para identificar patrones de comportamiento en HMI que sintetiza teoría de decisiones, ciencia de la información e implicaciones físicas.
- Introduce metodologías de análisis de señales (espectral, Granger multivariable, respuesta en frecuencia) para estudiar procesos de interacción y revelar diferencias de patrones y relaciones entre agentes.
- Extiende líneas de investigación en comportamiento de máquinas hacia límites de racionalidad, mecanismos de emoción y análisis cuantitativo de ética de IA.

## Metodología
Plantea tres preguntas de investigación (RQ): RQ1, naturaleza narrativa de decisiones intertemporales (individual e interactiva); RQ2, comparación de magnitudes de respuesta; RQ3, análisis de dilemas sociales (dirección de relaciones). Datos: partidas de Go en cuatro conjuntos: Tipo A (AGM vs AGZ, 20 juegos), Tipo B (AGM vs profesionales, 63), submuestra Tipo B (AGM vs 7 profesionales, 26), Tipo C (humanos vs humanos entre 7 profesionales, 84). Proxies y variables (todas en primera diferencia): STPs (proceeds de corto plazo del agente), STPs-oppo (corto plazo del oponente afectado por la decisión del agente), NPs (net proceeds), LTPs (proceeds de largo plazo: tasa de victoria). Se construyen dos sistemas: MIMO de 6 variables (distingue payoff propio y del oponente) y MIMO de 4 variables (integra NPs), y dos subsistemas por juego (cada jugador como respondiente). Preprocesamiento: pruebas ADF (estacionariedad al 5%). RQ1 (estático individual): análisis espectral multitaper (NW=4, K=7) con prueba F al 5% para detectar periodos significativos. RQ1 (interactivo): causalidad de Granger par-condicional multivariable (MVGC toolbox) con permutaciones (1000, 5%) y su versión espectral (spwcgc) para conectividad primaria. RQ2: respuesta en frecuencia (System Identification, Matlab) para trasladar respuestas a banda unificada (0–0.5 Hz, muestreo 1 Hz); comparación de magnitudes mediante prueba t pareada en los límites inferior y superior del IC 95% por par estímulo‑respuesta. RQ3: análisis de fase (Bode) y coherencia de fase para caracterizar dirección (co-movimiento vs contramovimiento) como indicador de cooperación vs conflicto. Las evaluaciones de payoff provienen del bot Jueyi/FineArt (Tencent), análogo a AlphaGo en valoración de estados; no se dispone de probabilidades de movimiento.

## Resultados Clave
- Descriptivo: diferencias claras entre cambios de corto y largo plazo (LTPs competitivo, anti-correlacionado entre jugadores); AlphaGo (AGM/AGZ) muestra ventaja en índices asociados a LTPs y, en Tipo B, AGM supera a profesionales en media y asimetría de LTPs.
- RQ1 (estático individual): humanos presentan menor estructura periódica en LTPs frente a AI; en Tipo B, AGM y pros muestran patrón plano en LTPs, mientras que en Tipo C persisten periodos significativos en LTPs para humanos, sugiriendo menor sensibilidad humana a variaciones de largo plazo frente a AlphaGo.
- RQ1 (interactivo/vertical): estructuras de conectividad principales coinciden entre sistemas: en 6‑var MIMO, bidireccionalidad entre STPs y STPs-oppo y fuerte LTPs→LTPs; en 4‑var MIMO, NPs→NPs y LTPs→LTPs. En Tipo B, la respuesta LTPs de humanos es más predecible que la de AGM (p. ej., 91.94% vs 22.58% en 6‑var; 93.55% vs 29.03% en 4‑var), mientras que en corto plazo AlphaGo es más predecible en juegos máquina‑máquina y humano‑humano.
- RQ2 (magnitud/parallel): las respuestas LTPs→STPs (y LTPs→NPs) abarcan escalas más amplias en todos los jugadores. En Tipo B, AGM exhibe mayor magnitud de respuesta que pros ante señales de pros en pares STPs→STPs y LTPs→STPs (sobre‑reacción propia), y menor magnitud en STPs-oppo→STPs-oppo y LTPs→STPs-oppo (infra‑reacción al oponente). En 4‑var, AGM muestra límites superiores mayores en NPs→NPs y LTPs→NPs frente a pros.
- Pruebas t pareadas (IC 95%): diferencias significativas y consistentes en los límites superiores apoyan sobre‑reacción de AGM a cambios propios de corto/medio plazo y menores respuestas a cambios del oponente; en Tipo C, respuestas humanas son similares entre sí (pocas diferencias estables).
- RQ3 (relación/“dilema social”): la fase indica que LTPs‑LTPs tiende a conflicto (≈ ±180°) a bajas frecuencias (competencia por el resultado), mientras que STPs↔STPs-oppo converge a dirección idéntica (≈ 0°) a bajas frecuencias (creciente influencia mutua hacia el final). En 4‑var, LTPs‑LTPs y NPs‑NPs también evolucionan hacia conflicto a baja frecuencia. Patrón común: de neutralidad de corto plazo a conflicto o alineación marcada en el largo plazo.

## Limitaciones
- Dominio limitado al juego de Go; generalización a otros contextos de HMI no demostrada.
- Uso de valoraciones de Jueyi/FineArt como proxy del estado (sin acceso a arquitectura ni a probabilidad de movimiento), lo que puede inducir sesgos.
- Falta de datos de probabilidad de movimiento (complejidad subjetiva de la decisión), relevantes para interpretar estrategias.
- Número reducido de juegos en Tipo A y exclusión de una partida por inestabilidad VAR en análisis espectral de Granger.
- Supuestos de estacionariedad y linealidad en métodos espectrales/VAR pueden no capturar no linealidades/heterocedasticidad.
- Reestructuración en sub‑sistemas por respondiente puede afectar análisis de adelanto/atraso (fase).

## Trabajo Futuro
- Replicar con múltiples AIs y dominios (otros juegos, diálogo, robótica) para robustez y generalización.
- Incorporar variables ausentes (p. ej., probabilidad de movimiento, medidas de complejidad) y datos humanos adicionales (tiempo de pensamiento, biométricos).
- Extender a métodos no lineales y causales robustos (p. ej., VAR no lineal, transfer entropy) y bandas de frecuencia adaptativas.
- Conectar métricas dinámicas (magnitud/fase) con modelos de prospección y metacognición humanos.
- Desarrollar indicadores cuantitativos de ética/alineamiento basados en patrones de respuesta y relaciones interacciónales.
- Explorar contextos no competitivos y colaborativos para mapear transiciones de cooperación‑conflicto con el mismo marco.

## Citas Relevantes
- "We find a similar connectivity structure in vertical analysis and coincidences with the interaction relationship in the game."
- "we find AlphaGo is more sensitive to long-term payoﬀchanges than human professional players."
- "The interaction relationship will emerge in frequency response comparison."
- "Every faculty in one man is the measure by which he judges of the like faculty in another. I judge of your sight by my sight, of your ear by my ear, of your reason by my reason, of your resentment by my resentment, of your love by my love. I neither have, nor can have, any other way of judging about them."

## Notas Adicionales
El estudio conceptualiza la HMI como sistema complejo de intercambio de señales con un proceso de utilidad interno, y usa la teoría de dependencia de respuesta como base filosófica (vinculada al Test de Turing). El diseño MIMO (6 vs 4 variables) permite contrastar efectos tipo contabilidad mental (separar payoff propio/oponente vs neto). Los análisis se realizan en banda unificada (0–0.5 Hz, muestreo por jugada=1 Hz) para comparabilidad. Hallazgos clave: sensibilidad superior de AlphaGo a cambios de largo plazo y divergencias sistemáticas de magnitud de respuesta (sobre‑/infra‑reacción) frente a humanos. Las direcciones de fase proveen una lectura operativa de dilemas sociales (cooperación temporal vs conflicto competitivo). Se recomienda comparar múltiples sistemas de IA para reforzar la robustez y definir claramente pares estímulo‑respuesta en futuros experimentos.
