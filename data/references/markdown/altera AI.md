# Project Sid: Many-agent simulations toward AI civilization

## Metadata
- **Autores**: Andrew Ahn, Nic Becker, Manuel Cortes, Arda Demirci, Melissa Du, Peter Y Wang, Guangyu Robert Yang, Shuying Luo, Feitong Yang, Stephanie Carroll, Nico Christie, Frankie Li, Mathew Willows
- **Año**: 2024
- **Keywords**: PIANO, multi-agent systems, AI civilization, Minecraft, concurrent architecture, cognitive controller, coherence, specialization, collective rules, taxation, cultural transmission, memes, religion, Pastafarianism

## Abstract
El trabajo presenta Project Sid y la arquitectura PIANO para simular y evaluar el progreso civilizatorio de 10–1000+ agentes de IA en entornos abiertos (Minecraft). PIANO introduce concurrencia entre módulos y un controlador cognitivo con cuello de botella para asegurar coherencia entre múltiples salidas (acción, habla, etc.) en tiempo real. Se diseñan métricas inspiradas en procesos civilizatorios humanos: especialización profesional, adhesión y modificación de reglas colectivas, y propagación cultural (memes y religión). Los resultados muestran que los agentes: (i) progresan individualmente en tareas complejas (adquisición de ítems), (ii) infieren y usan estados mentales sociales en grupos, (iii) se especializan en roles persistentes y heterogéneos, (iv) siguen y enmiendan leyes (p. ej., impuestos) mediante procesos democráticos, y (v) transmiten cultura y religión en sociedades de hasta 500 agentes. Se discuten limitaciones (visión/razonamiento espacial, motivaciones intrínsecas) y oportunidades para escalar hacia civilizaciones de IA más robustas.

## Contribuciones Principales
- Introducción de PIANO (Parallel Information Aggregation via Neural Orchestration), una arquitectura con módulos concurrentes y un controlador cognitivo con cuello de botella para coherencia multimodal.
- Mecanismos arquitectónicos que mejoran el progreso de agentes individuales (p. ej., módulo de conciencia de acción) y la dinámica multiagente (p. ej., conciencia social).
- Nuevos benchmarks de progreso civilizatorio en simulaciones a gran escala: especialización de roles, reglas colectivas (impuestos y enmiendas), y transmisión cultural (memes y religión).
- Demostraciones en Minecraft con sociedades de 50–100 agentes y civilizaciones de 500–1000, con interacción en tiempo real entre agentes y humanos.

## Metodología
Arquitectura: PIANO se basa en dos principios: (1) concurrencia entre módulos (memoria, conciencia de acción, generación de metas, conciencia social, habla, ejecución de habilidades) que leen/escriben a un estado de agente compartido y operan a diferentes escalas temporales; (2) coherencia mediante un Cognitive Controller (CC) que toma decisiones de alto nivel a través de un cuello de botella informacional y las difunde a módulos motores y de habla.
Entorno: Minecraft como mundo abierto y escalable, con capacidades de conversación y acción. Evaluaciones automatizadas por LLMs sobre resúmenes y trazas (p. ej., inferencia de sentimientos, roles, memes).
Experimentos y métricas:
- Progreso individual: 25 agentes aislados por 30 min (ítems únicos/tiempo); corrida extendida con 49 agentes por 4 h para techo de desempeño. Comparaciones: PIANO completo vs. arquitectura base y ablación del módulo de conciencia de acción.
- Habilidades sociales en grupos pequeños: experimentos en sala cerrada con 1 agente y 3 personajes (dinámica afectiva cambiante), y una tarea de reparto de comida guiada por percepciones afectivas; ablación de conciencia social como control.
- Sociedades (50 agentes, >4 h): agentes con personalidades distintas, acciones libres y conversación. Métricas: precisión de percepción social (pendiente/correlación entre "likeability" verdadera y percibida), evolución temporal de precisión, conectividad por rasgos (extroversión), reciprocidad de sentimientos.
- Especialización (30 agentes, 20 min): misma aldea y metas comunitarias, con memorias de ubicaciones clave. Inferencia de roles mediante ventanas deslizantes de metas sociales generadas por los agentes (LLM). Condiciones: normal con/ sin módulos sociales, y aldeas con objetivos "marcial" y "artístico". Métrica: entropía de distribución de roles y mapeo de roles a acciones de bajo nivel.
- Reglas colectivas (impuestos): 29 agentes (25 constituyentes, 3 influencers pro o anti impuestos, 1 gestor electoral remoto). Simulación de 20 min con 5 temporadas de impuestos antes y después de una enmienda constitucional a mitad del experimento. Flujo: feedback ciudadano (almacenado), propuesta de enmiendas (gestor), votación, actualización constitucional y observación de cumplimiento (% inventario depositado). Controles: constitución congelada; ablación (sin módulos sociales, de metas y grounding).
- Transmisión cultural (500 agentes, 6 pueblos + zonas rurales, 9000 s): extracción de memes a partir de resúmenes de metas/conversaciones; análisis de conteos por agente y por pueblo a lo largo del tiempo. Religión: 20 sacerdotes pastafarianos en un pueblo; medición de conversiones directas ("Pastafarian"/"Spaghetti Monster") e indirectas ("Pasta"/"Spaghetti") y área de influencia espacial en el tiempo.

## Resultados Clave
- Progreso individual: con PIANO completo, los agentes obtuvieron en promedio ~17 ítems únicos tras 30 min; variabilidad por spawn; mejores agentes 30–40 ítems (nivel humano básico). La conciencia de acción mejoró la progresión. En 4 h (49 agentes) se alcanzaron ~320 ítems únicos totales (~1/3 del universo de ~1000 ítems); diamantes logrados ~30 min.
- Dependencia del modelo base: el rendimiento sostenido requirió GPT-4o; modelos anteriores no alcanzaron metas comparables.
- Percepción social (50 agentes, ~4 h): con módulos sociales, la likeability percibida correlacionó fuertemente con la verdadera (p. ej., r≈0.81, pendiente≈0.37 con ≥10 observadores); la precisión aumenta con más observadores y con el tiempo. Sin módulos sociales, relaciones más neutras y pendientes menores (p. ej., pendiente≈0.16). Extroversión predijo mayor in-degree (r≈0.48). La reciprocidad afectiva fue alta pero no garantizada.
- Especialización: con módulos sociales, surgieron roles diversos y persistentes (p. ej., farmer, miner, engineer, guard, explorer, blacksmith), con alta heterogeneidad (entropías aprox.: Ablated 2.60; Normal 3.41; Martial 3.83; Art 4.04). En aldeas marcial/artística aparecieron roles exclusivos (scout/strategist vs. curator/collector). Las acciones de bajo nivel se alinearon fuertemente con los roles (p. ej., guards/builders fabrican fences; farmers siembran/preparan tierra; artists recolectan flores).
- Reglas colectivas (impuestos): antes de cambios, los constituyentes cumplieron (~20% del inventario), pese a influencers. Influencers pro/anti sesgaron feedback y votos, induciendo enmiendas y cambiando el % pagado (p. ej., reducción a ~9% cuando la constitución pasó a 5–10%). Con constitución congelada, el pago permaneció estable; con ablación, se perdió bidireccionalidad del cambio (tasas aumentaron en ambas condiciones), mostrando la necesidad de módulos PIANO para propagar influencia de forma coherente.
- Memes (500 agentes): los pueblos generaron significativamente más memes por agente que áreas rurales; cada pueblo mostró perfiles temáticos distintos (p. ej., Woodhaven: eco; Clearwater: pranks) y dinámicas temporales con ascenso/declive de popularidad.
- Religión (Pastafarianismo): aumentaron continuamente conversos directos e indirectos durante >2 h; el área espacial de influencia creció conforme sacerdotes/conversos migraron entre pueblos.
- Escalabilidad: simulaciones de 500 agentes estables; con >1000 agentes aparecieron cuellos de botella del servidor (latencias e inactividad intermitente).

## Limitaciones
- Habilidades perceptivo-espaciales limitadas: carencia de visión/razonamiento espacial robusto dificulta navegación y construcción colaborativa.
- Motivaciones intrínsecas débiles: ausencia de drives robustos (supervivencia, curiosidad, comunidad) para un desarrollo societal más genuino.
- Dependencia de conocimiento previo: basados en modelos fundacionales, no emergen de novo instituciones complejas (democracia, economías fiat, sistemas de comunicación).
- Infraestructura: restricciones de servidor afectaron corridas >1000 agentes (intermitencias).
- Evaluación con LLM: inferencias de sentimientos/roles/memes pueden introducir sesgos del evaluador LLM.
- Incoherencias terminológicas: discrepancia menor en el acrónimo PIANO ("Information" vs. "Input").

## Trabajo Futuro
- Integrar percepción visual y mapas cognitivos para navegación y construcción multiagente.
- Incorporar motivaciones intrínsecas y objetivos homeostáticos para impulsar auto-organización sostenida.
- Fomentar emergencia de instituciones y economías de forma endógena (p. ej., mercados, moneda, normativas).
- Escalar infraestructura y optimización en tiempo real para 1000–10,000+ agentes con baja latencia.
- Ampliar modalidades de salida (gaze, gestos, expresiones) y reforzar mecanismos de coherencia multimodal.
- Diseñar benchmarks estandarizados de "progreso civilizatorio" y métricas causalmente identificables.
- Explorar entornos más allá de Minecraft y mayor interacción humano–agente en tiempo real.
- Reducir dependencia de LLM evaluadores con métricas objetivas/instrumentadas y señales de entorno.

## Citas Relevantes
- "We first introduce the PIANO (Parallel Information Aggregation via Neural Orchestration) architecture, which enables agents to interact with humans and other agents in real-time while maintaining coherence across multiple output streams."
- "We define a civilization as an advanced society that has achieved a high level of institutional development, which manifests in specialized roles, organized governance, and advancements in areas like science, art, and commerce."
- "Agents should be able to think and act concurrently."
- "An immediate challenge with concurrent modules is that they can produce independent outputs, making the agent incoherent."
- "The Cognitive Controller synthesizes information across the Agent State through a bottleneck."
- "We show that agents form their own professional identities, obey collective rules, transmit cultural information and exert religious influence, and use sophisticated infrastructures, such as legal systems."
- "On average, agents deposited roughly 20% of their inventory, as stipulated by the constitution."
- "We believe the lack of such large-scale benchmarks can be attributed to how technically difficult it is to perform simulations of hundreds or thousands of agents in a single world."

## Notas Adicionales
El paper funciona como informe técnico con resultados preliminares. La arquitectura PIANO combina concurrencia y un controlador cognitivo con cuello de botella para coordinar múltiples flujos de salida en tiempo real. Varias métricas (sentimientos, roles, memes) se infieren mediante LLMs, lo que puede introducir sesgos. Los mejores resultados requieren GPT-4o; la comparación con Voyager no es directa por diferencias metodológicas. Se observan pequeñas inconsistencias en la denominación de PIANO ("Parallel Information" vs. "Parallel Input"). El entorno de evaluación es Minecraft; se escaló a 500 agentes de forma estable y se alcanzaron ~1000 con restricciones de servidor. No hay sección formal de Conclusiones; la Discusión sintetiza avances y proyecciones.
