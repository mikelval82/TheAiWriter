# Digital Twin and Wearables Unveiling Pedestrian Comfort Dynamics and Walkability in Cities

## Metadata
- **Autores**: Marcel Ignatius, Joie Lim, Ben Gottkehaskamp, Kunihiko Fujiwara, Clayton Miller, Filip Biljecki
- **Año**: 2024
- **Keywords**: Thermal Walks, Urban Digital Twin, Smart Wearable, Street View Imagery, Computer Vision

## Abstract
El estudio analiza la interacción entre el confort térmico exterior, la caminabilidad y la morfología urbana 3D mediante la integración de datos heterogéneos en un gemelo digital urbano (UDT). Combina wearables (Apple Watch con microencuestas y biometría), una estación meteorológica móvil y segmentación de imágenes de calle panorámicas (SVI) para captar, sincronizar y visualizar la experiencia térmica durante "thermal walks" en un campus de Singapur. Se desarrollan métodos de visión por computador (Mask2Former) y mapeo de la posición solar (pvlib) para relacionar variables morfológicas (cielo, edificios, vegetación, etc.) con microclima y sensaciones térmicas. El trabajo aporta un caso de uso novedoso para UDTs y evidencia el potencial de estas analíticas para comprender y mejorar la caminabilidad, destacando el papel clave de la geoinformación 3D. Se discuten retos: diversidad de participantes, experiencia técnica para UDT/visión por computador, y la necesidad de más datos para modelos predictivos robustos.

## Contribuciones Principales
- Presenta un UDT de prueba de concepto que integra wearables, SVI y sensores meteorológicos móviles para estudiar confort térmico peatonal y caminabilidad.
- Introduce un flujo de trabajo completo: adquisición (Apple Watch + Cozie, GoPro Max, estación meteorológica), segmentación semántica (Mask2Former) y mapeo solar (pvlib), sincronización temporal-espacial y visualización interactiva (deck.gl + react-plotly).
- Aporta a la literatura de gemelos digitales un nuevo caso de uso y una combinación de datos poco explorada.
- Contribuye a la climatología urbana al relacionar microclima, morfología urbana 3D y confort térmico a nivel peatonal.
- Desarrolla una interfaz que correlaciona métricas morfológicas (p. ej., Sky View Factor aproximado, proporciones de cielo/edificio/vegetación) con mediciones microclimáticas y respuestas subjetivas/biométricas en tiempo real.

## Metodología
Diseño del estudio y área: Thermal walks en un campus universitario de Singapur atravesando tipologías diversas (vías, pasarelas cubiertas, aceras arboladas, espacios abiertos y con desniveles). Participación de un sujeto (prueba de concepto) con registro simultáneo de datos ambientales, fisiológicos y percepciones.

Sensado microclimático (estación móvil): Estación empujada manualmente, con aclimatación de 10 minutos. Variables: temperatura y humedad del aire (HD9009TRR + escudo HD9007A-1; ±0.2 °C, ±2%), temperatura de globo de 50 mm (TP876.1.I; ±0.1 °C), viento (HD4V3TS2; ±0.2 m/s + 3%), irradiancia global horizontal (LPPYRA03S; ±20 W/m2, ±2%). Data logger HD33MT.4, intervalo de medida 10 s y registro 1 min.

SVI y segmentación: Video panorámico 360° con GoPro Max; extracción de frames cada 5 s y nivelación del horizonte (GoPro Player). Segmentación semántica con Mask2Former preentrenado en CityScapes (mIoU 84.5%, 19 clases). Cálculo de proporciones de píxeles para cielo, edificios, vegetación, acera, terreno y calzada. Transformaciones a vista ojo de pez: equisólida (mitad superior) para proporciones de edificios/árboles y ortográfica para una representación precisa del cielo (apoyo a SVF).

Posición solar: Cálculo de elevación y acimut con pvlib (coordenadas, fecha y hora) y mapeo en imágenes panorámicas equirectangulares a coordenadas de píxel, permitiendo evaluar obstrucciones por copas arbóreas/edificaciones y exposición solar directa.

Wearables y microencuestas: Apple Watch con Cozie V3 (iOS). Registro de ubicación para trazado de ruta; microencuestas dependientes de respuesta sobre percepción térmica y contexto; biometría (frecuencia cardiaca), presión arterial, saturación de oxígeno, y actividad (velocidad de marcha, pasos). Las encuestas se gatillan a lo largo de la ruta y entre segmentos.

Integración y UDT: Sincronización por timestamp y localización de tres fuentes (GoPro, estación móvil, smartwatch). Exportación a dos archivos JSON: (1) geometría de la ruta (lat/lon/alt) y lecturas/respuestas puntuales (visualizadas con PathLayer e IconLayer en deck.gl), y (2) series para gráficos (proporciones segmentadas: cielo/edificio/vegetación; variables microclimáticas: temperatura, GHI, viento; lecturas del reloj: FC, percepción térmica) mostradas con react-plotly.js. Contexto 3D de edificios, terreno y arbolado para navegación a lo largo del recorrido mediante control deslizante y pop-ups.

## Resultados Clave
- Demostración de una interfaz UDT que integra y sincroniza datos heterogéneos (SVI segmentada, microclima, biometría y percepciones) en 3D, permitiendo navegar el recorrido y comparar métricas locales.
- Identificación visual de patrones: en la pista y campo deportivo (área abierta) se observó alta proporción de cielo y baja de vegetación/edificios (sombra), correlacionando con mayor temperatura y percepción de “calor” pese a velocidades de viento más altas.
- Visualización y trazado de la posición solar sobre imágenes panorámicas para inferir exposición a radiación directa y obstrucciones por morfología (árboles/edificios).
- Prueba de viabilidad técnica: la integración de wearables, SVI y sensores en un UDT resultó factible y comprensible para la exploración de confort térmico durante caminatas.
- Pipeline reproducible de procesamiento y sincronización temporal-espacial con salidas JSON para capas interactivas y gráficos.

## Limitaciones
- Muestra de un solo participante; datos no representativos para inferencias generalizables.
- El uso de carrito para la estación incrementa el esfuerzo físico y puede sesgar la percepción/biometría; se sugiere sistema en mochila.
- Cobertura temporal limitada (un recorrido); falta variación por horas del día y estaciones.
- Conjunto de métricas fisiológicas reducido (no incluye tasa metabólica, temperatura central/cutánea, sudoración).
- Modelo 3D incompleto del entorno (faltan arbustos y pasarelas cubiertas) respecto a lo captado por SVI.
- Integración de datos aún no estandarizada en formatos 3D (p. ej., CityJSON) y requiere mayor robustez.
- Necesidad de diversidad de participantes y perfiles demográficos; cuestionario adaptado a climas, pero no validado en múltiples regiones.

## Trabajo Futuro
- Aumentar número y diversidad de participantes y repetir recorridos en distintos horarios/estaciones para mejorar la robustez estadística.
- Incorporar sensores fisiológicos adicionales (tasa metabólica, temperatura central y de piel, tasa de sudoración) y adoptar estación meteorológica en mochila.
- Actualizar e integrar un modelo 3D más fidedigno (incluyendo vegetación baja y estructuras de sombra) en el UDT.
- Estandarizar la integración en modelos 3D (p. ej., CityJSON) y fortalecer la gestión de datos temporales y multimodales.
- Clasificar trayectos por distribuciones morfológicas y detectar hotspots de disconfort térmico y rutas preferidas.
- Desarrollar y entrenar modelos de aprendizaje automático para predecir confort térmico peatonal y apoyar decisiones de diseño urbano.
- Extender la metodología a otros climas y adaptar el flujo de encuestas a diferentes regímenes térmicos.

## Citas Relevantes
- "This research contributes to (1) digital twins, providing a novel combination of data integration and a new use case, and to (2) urban climatology, advancing our understanding of the relationship among microclimate, urban environment, and outdoor thermal comfort." 
- "In this work, we developed a proof of concept of an urban digital twin that integrates emerging forms of urban data (e.g., wearables, street view imagery) to sense outdoor thermal comfort and influence of the built environment..."
- "How can a methodological framework be developed for the quantification and evaluation of comprehensive thermal comfort factors, facilitating their seamless integration into an urban digital twin?"
- "What potential use cases can be identified for the integrated data and the implemented UDT?"
- "Understanding the impact of direct solar radiation is essential in assessing urban thermal comfort."
- "The novel integration of data turned out to be relatively straightforward and ended up being represented in a clear manner in the interface (Figure 1)."

## Notas Adicionales
Artículo de prueba de concepto, revisado por pares en ISPRS Annals (3D GeoInfo 2024), centrado en la integración y visualización más que en análisis inferencial. La segmentación SVI usa Mask2Former (CityScapes, mIoU 84.5%) y la posición solar se calcula con pvlib; la interfaz se implementa con deck.gl y react-plotly. La metodología es, en general, agnóstica al clima, ajustando el cuestionario Cozie según el contexto. A falta de más participantes y repeticiones temporales, no se reportan modelos predictivos cuantitativos ni métricas de desempeño; el énfasis es la viabilidad técnica y el valor de la geoinformación 3D para estudiar confort térmico y caminabilidad.
