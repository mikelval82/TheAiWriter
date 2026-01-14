# TheAIWriter - Arquitectura del Sistema

## 📋 Resumen

TheAIWriter es un sistema de escritura académica asistida por IA especializado en **papers de perspectivas**. Utiliza agentes especializados para generar, revisar iterativamente y exportar papers científicos manteniendo coherencia con un abstract base.

---

## 🎯 Flujo Principal: Paper de Perspectivas

```mermaid
flowchart TD
    A[📄 ABSTRACT.md] --> B[Cargar Contexto Base]
    B --> C[PerspectivePaperOrchestrator]
    
    C --> D[ReferenceIndex]
    D --> E[Parsear 42 referencias]
    E --> F[Generar embeddings]
    F --> G[Cachear en JSON]
    
    C --> H[WriterAgent<br/>con contexto abstract]
    C --> I[ReviewerAgent<br/>con contexto abstract]
    C --> J[ReferenceContextManager]
    
    subgraph loop["🔄 Por cada sección"]
        J --> K[Buscar top 8 refs<br/>por similitud coseno]
        K --> L[Extraer solo secciones<br/>relevantes sin truncar]
        L --> M[WriterAgent escribe]
        M --> N{Iteración < 2?}
        N -->|Sí| O[ReviewerAgent revisa]
        O --> M
        N -->|No| P[Sección completada]
    end
    
    P --> Q[Paper completo]
    Q --> R[Revisión Final]
    R --> S[📝 Paper.md]
    R --> T[📋 Critical_Review.md]
```

---

## 🔍 Sistema de Selección Inteligente de Referencias

```mermaid
flowchart LR
    A[Sección actual:<br/>e.g. 'Introducción'] --> B[Section Mapper]
    B --> C[Secciones a extraer:<br/>abstract, contributions]
    
    D[42 Referencias<br/>con embeddings] --> E[ReferenceIndex]
    
    F[Query = Abstract +<br/>Sección + Contexto] --> E
    E --> G[Similitud Coseno]
    G --> H[Top 8 referencias]
    
    C --> I[ReferenceContextManager]
    H --> I
    I --> J[Contexto optimizado<br/>SIN truncamiento]
    J --> K[WriterAgent]
```

### Mapeo Sección → Referencias

| Sección del Paper | Secciones de Referencia |
|-------------------|------------------------|
| Introducción | abstract, contributions |
| Estado del Arte | abstract, contributions, methodology, results |
| Identificación del Problema | limitations, future_work, contributions |
| La Nueva Perspectiva | contributions, methodology, results, notes |
| Discusión | results, notes, limitations, quotes |
| Implicaciones Futuras | future_work, results, contributions |
| Desafíos y Limitaciones | limitations, future_work |
| Conclusiones | abstract, results, quotes, contributions |

---

## 📚 Estructura de un Paper de Perspectivas

| Orden | Sección | Descripción |
|-------|---------|-------------|
| 0 | **Abstract** | Proporcionado por el usuario (no generado) |
| 1 | Introducción | Contexto y objetivos |
| 2 | Estado Actual del Arte | Revisión de literatura |
| 3 | Identificación del Problema | La brecha a abordar |
| 4 | La Nueva Perspectiva | Propuesta central |
| 5 | Discusión | Argumentación detallada |
| 6 | Implicaciones Futuras | Hoja de ruta |
| 7 | Desafíos y Limitaciones | Reconocimiento honesto |
| 8 | Conclusiones | Síntesis final |
| 9 | Conflicto de Intereses | Declaración formal |
| 10 | Agradecimientos | Reconocimientos |
| 11 | Referencias | Bibliografía |

---

## 🏗️ Arquitectura de Agentes

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        +client: OpenAI
        +model: str
        +_call_api(system_prompt, user_prompt)
        +system_prompt: str*
    }
    
    class WriterAgent {
        +abstract_context: str
        +write(topic, sections, references) Paper
        +write_section(section_name, previous_sections, references) Section
        +expand_section(paper, section_title) Paper
    }
    
    class ReviewerAgent {
        +abstract_context: str
        +review(paper) Paper
        +review_section(section, previous_sections) Section
        +review_full_paper(paper) Paper
        +generate_critical_review(paper) str
        +get_feedback(paper) str
    }
    
    class PaperSummaryAgent {
        +summarize(paper_text) str
        +summarize_with_context(paper_text, context) str
    }
    
    BaseAgent <|-- WriterAgent
    BaseAgent <|-- ReviewerAgent
    BaseAgent <|-- PaperSummaryAgent
```

---

## 🔄 Proceso Iterativo de Escritura-Revisión

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant W as WriterAgent
    participant R as ReviewerAgent
    participant API as OpenAI API
    
    Note over O: Carga ABSTRACT.md como contexto
    O->>W: Inicializa con abstract_context
    O->>R: Inicializa con abstract_context
    
    loop Para cada sección
        O->>W: write_section(nombre, secciones_previas)
        W->>API: Genera con contexto
        API-->>W: Contenido inicial
        
        loop 2 iteraciones
            O->>R: review_section(sección, contexto)
            R->>API: Revisa y mejora
            API-->>R: Contenido mejorado
        end
    end
    
    O->>R: review_full_paper(paper)
    R-->>O: Paper coherente
    
    O->>R: generate_critical_review(paper)
    R-->>O: Documento crítico
```

---

## 📦 Modelo de Datos

```mermaid
erDiagram
    Paper ||--o{ Section : contiene
    Paper {
        string title
        list authors
        list keywords
        datetime created_at
        datetime updated_at
    }
    Section {
        string title
        string content
    }
```

---

## 🎯 Componentes Principales

| Componente | Responsabilidad |
|------------|-----------------|
| `PerspectivePaperOrchestrator` | Orquesta el flujo completo de paper de perspectivas |
| `ReferenceIndex` | Índice de referencias con embeddings cacheados |
| `ReferenceContextManager` | Selección inteligente de referencias por sección |
| `ReferenceParser` | Parsea markdown estructurado en secciones |
| `WriterAgent` | Genera contenido académico con contexto del abstract |
| `ReviewerAgent` | Revisa secciones y genera documento crítico |
| `MarkdownReader` | Lee referencias y abstract |
| `MarkdownWriter` / `PDFWriter` | Exporta el paper final |

---

## 📁 Estructura de Directorios

```
TheAIWriter/
├── src/ai_writer/
│   ├── agents/              # Agentes de IA
│   │   ├── base_agent.py
│   │   ├── writer_agent.py  # Escritura con contexto
│   │   └── reviewer_agent.py # Revisión iterativa
│   ├── orchestrators/       # Orquestadores de flujo
│   │   └── perspective_paper_orchestrator.py
│   ├── models/              # Modelos de datos
│   │   ├── paper.py
│   │   └── reference.py     # ParsedReference
│   ├── utils/               # Utilidades
│   │   ├── reference_parser.py      # Parser de markdown
│   │   ├── reference_index.py       # Índice con embeddings
│   │   └── reference_context_manager.py  # Selector inteligente
│   ├── readers/             # Lectores
│   ├── writers/             # Exportadores
│   └── scripts/             # Scripts ejecutables
│       └── generate_perspective_paper.py
├── config/                  # Configuración
├── data/
│   ├── references/
│   │   └── markdown/
│   │       ├── ABSTRACT.md          # ⭐ Abstract base (requerido)
│   │       ├── reference_index.json # 📦 Cache de embeddings
│   │       └── *.md                 # Referencias parseadas
│   └── output/
│       └── drafts/          # Papers generados
└── docs/                    # Documentación
```

---

## 🚀 Uso

```bash
# Generar un paper de perspectivas
python -m ai_writer.scripts.generate_perspective_paper
```

**Requisitos:**
1. Archivo `data/references/markdown/ABSTRACT.md` con el abstract del paper
2. Referencias estructuradas en `data/references/markdown/*.md`

**Primera ejecución:**
- Parsea todas las referencias
- Genera embeddings (1 llamada API por lote de 100)
- Cachea en `reference_index.json`

**Ejecuciones siguientes:**
- Carga directamente del cache (instantáneo)
