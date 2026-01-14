# AgentMaster: A Multi-Agent Conversational Framework Using A2A and MCP Protocols for Multimodal Information Retrieval and Analysis

## Metadata
- **Autores**: Callie C. Liao, Duoduo Liao, Sai Surya Gadiraju
- **Año**: 2025
- **Keywords**: Multi-Agent Systems, Agent-to-Agent (A2A), Model Context Protocol (MCP), Multimodal, Information Retrieval, Question Answering, Retrieval-Augmented Generation, Orquestación, SQL, Análisis de imágenes, Conversational AI

## Abstract
El trabajo presenta AgentMaster, un marco conversacional modular de sistemas multiagente (MAS) que integra los protocolos A2A (comunicación agente-a-agente) y MCP (Model Context Protocol) para abordar desafíos de coordinación, comunicación e interacción con herramientas heterogéneas en entornos multimodales. A través de una interfaz conversacional unificada, el sistema permite interacción en lenguaje natural y resuelve tareas de recuperación de información, respuesta a preguntas y análisis de imágenes. En un estudio piloto con una implementación propia de A2A y MCP, evaluado con BERTScore F1 (96.3%) y G-Eval (87.1%), se observa coordinación robusta entre agentes, descomposición de consultas, enrutamiento dinámico y respuestas pertinentes a dominios específicos.

## Contribuciones Principales
- Presenta AgentMaster, un marco MAS modular que integra MCP de Anthropic y A2A de Google para comunicación flexible entre agentes, coordinación inteligente y RAG.
- Diseña una arquitectura unificada para descomposición de consultas, enrutamiento dinámico y orquestación entre agentes especializados y fuentes de datos multimodales.
- Implementa versiones propias de A2A y MCP adaptadas a AgentMaster, sin depender de SDKs existentes.
- Desarrolla un prototipo funcional basado en microservicios Flask, aplicable a IR, análisis de imágenes, consultas SQL, QA y resumen.
- Realiza una evaluación con G-Eval, BERTScore y métricas relacionadas para validar corrección, completitud y fidelidad semántica en consultas diversas.

## Metodología
Arquitectura general MAS con cuatro componentes: (1) Interfaz conversacional unificada tipo chatbot que acepta entradas multimodales (texto, imágenes, audio, tablas/gráficas) y produce salidas en múltiples modalidades; (2) Centro Multi-Agente con tres niveles: un agente orquestador (orchestrator) para descomponer tareas y coordinar su ejecución; agentes de dominio (p. ej., SQL, IR, visión) que integran funciones y datos específicos; y agentes generales con LLM dedicados para razonamiento de propósito general; (3) Protocolos multiagente: A2A para comunicación estructurada entre agentes (mensajes JSON estandarizados) y MCP para acceso unificado a herramientas, memoria de largo plazo y gestión de contexto, mejorando modularidad e interoperabilidad; (4) Capa de gestión de estado que emplea bases vectoriales y cachés de contexto para mantener el estado MCP, habilitando memoria semántica persistente y datos de sesión temporales para flujos activos.
Caso de estudio (arquitectura de implementación): interfaz web, un servidor Flask como punto de entrada, un Coordinator Agent (equivalente al orquestador) con un módulo de evaluación de complejidad que decide entre procesamiento por un solo agente o colaboración multiagente, y clientes de agentes (Agent Clients) que invocan flujos distribuidos vía JSON-RPC. Los MCP Clients gestionan la comunicación con MCP Servers específicos de cada agente de recuperación. Agentes especializados: IR Agent (contenido no estructurado), SQL Agent (generación/ejecución de consultas sobre BD relacionales), Image Agent (procesamiento de imágenes mediante APIs de visión externas) y un General Agent (consultas abiertas y casos de respaldo). Un módulo LLM (local o externo) agrega salidas parciales y sintetiza la respuesta final. Se incluyen mecanismos de manejo de errores a nivel de servidor Flask y del coordinador.
Implementación y despliegue: microservicios en Flask, ejecución local y en AWS; protocolos A2A y MCP autoimplementados; cada agente utiliza GPT-4o mini; datos de dominio proceden de conjuntos públicos del FHWA. El flujo E2E: el usuario envía la consulta; el coordinador evalúa la complejidad y enruta; los agentes especializados devuelven resultados vía MCP; el LLM sintetiza y la UI presenta la respuesta.
Evaluación: (i) evaluación individual de agentes (basada en trabajos previos); (ii) evaluación de tareas complejas mediante verificación de subpreguntas (las subconsultas simples se contrastan con segmentos de la respuesta compuesta); (iii) métricas G-Eval, BERTScore, relevancia de respuesta y detección de alucinaciones; además de evaluación humana centrada en finalización y corrección de tareas. Se probaron seis consultas complejas con descomposición automática y asignación de rutas a agentes según sus capacidades.

## Resultados Clave
- Desempeño promedio: G-Eval 87.1% y BERTScore F1 96.3%, indicando alta fidelidad semántica y respuestas robustas.
- Por tipo de consulta (G-Eval / BERT-F1): SQL 92.0% / 98.7%; IR 90.2% / 97.8%; QA general 84.0% / 96.8%; Imagen/QA compleja 82.0% / 91.9%.
- La verificación por subpreguntas simples coincidió con segmentos de respuestas a consultas complejas, confirmando descomposición y enrutamiento adecuados (p. ej., conteo total de puentes en Virginia y los construidos en 2019 vía SQL correcto).
- Evaluación humana: todas las consultas complejas fueron correctamente descompuestas; la mayoría de las rutas de agentes fueron adecuadas a sus capacidades.
- Agentes SQL e IR mostraron resultados consistentemente precisos; agentes General e Image presentaron variabilidad menor por la naturaleza abierta de la generación.
- Se observó ocasional clasificación errónea de consultas simples como complejas, lo que puede degradar respuestas o añadir pasos innecesarios.

## Limitaciones
- La exactitud depende del LLM subyacente y del corpus de recuperación; bases de datos de tamaño limitado reducen la profundidad informativa.
- Errores ocasionales en la clasificación de complejidad provocan descomposición innecesaria o respuestas incompletas.
- Colaboración interagente aún limitada; los flujos pueden no explotar plenamente la sinergia entre agentes.
- Dificultades en la síntesis de información compleja por parte del LLM.
- La evaluación LLM-as-a-judge, aunque escalable, puede estar sesgada y no siempre alinearse con juicios humanos o expertos.
- Ausencia de salvaguardas de seguridad establecidas para almacenamiento y uso de información.

## Trabajo Futuro
- Mejorar el clasificador de complejidad y las políticas de enrutamiento dinámico para reducir descomposiciones innecesarias.
- Fortalecer la colaboración interagente (memorias compartidas, planificación conjunta) y ampliar/curar los repositorios de datos para mayor cobertura y profundidad.
- Incorporar salvaguardas de seguridad y control de acceso para datos, herramientas y estados MCP.
- Diseñar evaluaciones más robustas que mitiguen sesgos de LLM-as-a-judge e incrementen la alineación con expertos humanos.
- Extender el soporte multimodal (audio, video) y dominios adicionales manteniendo modularidad y reproducibilidad.
- Optimizar costos y recursos (p. ej., cacheo, compresión de contexto, control de tasas) y explorar compatibilidad con SDKs oficiales.

## Citas Relevantes
- "We present a pilot study of AgentMaster, a novel modular multi-protocol MAS framework with self-implemented A2A and MCP, enabling dynamic coordination and flexible communication."
- "Evaluation through the BERTScore F1 and LLM-as-a-Judge metric G-Eval averaged 96.3% and 87.1%, revealing robust inter-agent coordination, query decomposition, dynamic routing, and domain-specific, relevant responses."
- "To the best of our knowledge, very few applications exist where both protocols are employed within a single MAS framework."
- "The A2A-MCP design emphasizes modularity, extensibility, and reproducibility."

## Notas Adicionales
Estudio piloto con implementación propia de A2A y MCP, sin depender del SDK de Google; arquitectura de microservicios Flask desplegada localmente y en AWS; cada agente usa GPT-4o mini. Los datos provienen de FHWA para construir bases de conocimiento de dominio (puentes, tráfico). La orquestación se basa en un Coordinator Agent con evaluación de complejidad, Agent/MCP Clients y MCP Servers por agente. La memoria y contexto se gestionan con base vectorial y caché. No se reporta un conjunto de pruebas a gran escala ni ablation de componentes (p. ej., sin MCP/A2A), por lo que la generalización más allá del dominio del caso de estudio queda por validar. El manuscrito indica contribución igualitaria de los tres autores. No se listan palabras clave oficiales.
