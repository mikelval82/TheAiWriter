# TheAIWriter - Arquitectura del Sistema

> Sistema de escritura académica asistida por IA especializado en **papers de perspectivas**.  
> Versión: 1.0.0 | Última actualización: Enero 2026

## 📋 Índice

1. [Visión General](#-visión-general)
2. [Arquitectura de Alto Nivel](#-arquitectura-de-alto-nivel)
3. [Pipeline de 3 Fases](#-pipeline-de-3-fases)
4. [Sistema de Agentes](#-sistema-de-agentes)
5. [Sistema RAG](#-sistema-rag)
6. [Modelos de Datos](#-modelos-de-datos)
7. [Estructura del Proyecto](#-estructura-del-proyecto)
8. [CLI y Uso](#-cli-y-uso)

---

## 🎯 Visión General

TheAIWriter genera papers académicos de perspectiva utilizando:

- **Análisis de Clusters**: Extrae temas principales del espacio de embeddings
- **Planificación Inteligente**: Genera outlines detallados párrafo por párrafo
- **RAG-Enhanced Writing**: Cada párrafo busca evidencia específica
- **Revisión Iterativa**: ReviewerAgent fortalece argumentos con evidencia adicional
- **Memoria de Sección**: Mantiene coherencia entre secciones

### Métricas del Sistema

| Recurso | Cantidad |
|---------|----------|
| Ideas indexadas | 3,733 |
| Claims indexados | 3,839 |
| Referencias indexadas | 1,200+ |
| Papers procesados | 41 |
| Dimensiones embedding | 1,536 |

---

## 🏗️ Arquitectura de Alto Nivel

```mermaid
flowchart TB
    subgraph Input["📥 Entrada"]
        Abstract["📝 ABSTRACT.md"]
        PDFs["📄 PDFs de Referencia"]
    end

    subgraph Processing["⚙️ Procesamiento Offline"]
        Docling["Docling\nPDF → Markdown"]
        Extractor["PDFExtractionAgent\nIdeas, Claims, Referencias"]
        Embedder["OpenAI Embeddings\ntext-embedding-3-small"]
        
        PDFs --> Docling --> Extractor --> Embedder
    end

    subgraph Storage["💾 Almacenamiento"]
        direction LR
        Ideas[("💡 Ideas\nideas_index.npz")]
        Claims[("📌 Claims\nclaims_index.npz")]
        Refs[("📚 Referencias\nreferences_index.npz")]
        
        Embedder --> Ideas & Claims & Refs
    end

    subgraph Generation["🚀 Generación (3 Fases)"]
        Phase1["🔬 Fase 1\nCluster Analysis"]
        Phase2["📋 Fase 2\nPlanning"]
        Phase3["✍️ Fase 3\nWriting"]
        
        Phase1 --> Phase2 --> Phase3
    end

    subgraph Output["📤 Salida"]
        Paper["📄 Paper.md"]
        Review["📋 Critical Review.md"]
    end

    Abstract --> Phase1
    Ideas --> Phase1
    Ideas & Claims & Refs --> Phase3
    Phase3 --> Paper & Review

    style Input fill:#e3f2fd
    style Processing fill:#fff3e0
    style Storage fill:#f3e5f5
    style Generation fill:#e8f5e9
    style Output fill:#fce4ec
```

---

## 🔬 Pipeline de 3 Fases

### Diagrama Detallado del Pipeline

```mermaid
flowchart TD
    subgraph Phase1["🔬 FASE 1: Análisis de Clusters"]
        A1["📝 Cargar Abstract"] --> A2["📊 Cargar Embeddings\n(ideas_index.npz)"]
        A2 --> A3["🎯 KMeans Clustering\n(n_clusters=25)"]
        A3 --> A4["📈 TF-IDF por Cluster"]
        A4 --> A5["🏷️ Generar ClusterTopics\n• label\n• keywords\n• centroid\n• size"]
    end

    subgraph Phase2["📋 FASE 2: Planificación"]
        B1["📑 Definir Secciones"] --> B2["🔗 Mapear Secciones → Topics"]
        B2 --> B3["🔍 Buscar Ideas por Centroide\n~8 ideas/sección"]
        B3 --> B4["📝 Construir Prompt\n• Abstract\n• Topics\n• Ideas reales"]
        B4 --> B5["🤖 PlannerAgent\n→ PaperOutline"]
        B5 --> B6["👀 ReviewerAgent\nreview_outline()"]
        B6 --> B7{¿Cambios?}
        B7 -->|Sí| B8["✏️ Refinar Outline"]
        B8 --> B6
        B7 -->|No| B9["✅ Outline Final"]
    end

    subgraph Phase3["✍️ FASE 3: Escritura"]
        C1["📑 Por cada Sección"] --> C2["¶ Por cada Párrafo"]
        C2 --> C3["🔍 paragraph.to_query()\n= key_idea + points"]
        C3 --> C4["📚 get_context_for_idea()\nBúsqueda semántica"]
        C4 --> C5["✍️ WriterAgent\nwrite_paragraph()"]
        C5 --> C6["📝 Añadir a Sección"]
        C6 --> C7{¿Más párrafos?}
        C7 -->|Sí| C2
        C7 -->|No| C8["💾 Generar Summary"]
        C8 --> C9["📋 Actualizar Memory"]
        C9 --> C10["👀 ReviewerAgent\nreview_section()"]
        C10 --> C11{¿Más secciones?}
        C11 -->|Sí| C1
        C11 -->|No| C12["📄 Paper Completo"]
    end

    A5 --> B1
    B9 --> C1
    C12 --> D1["📄 Guardar Paper.md"]
    C12 --> D2["📋 Generar Critical Review"]

    style Phase1 fill:#fff3e0
    style Phase2 fill:#f3e5f5
    style Phase3 fill:#e8f5e9
```

### Descripción de Fases

#### Fase 1: Cluster Analysis
1. Carga embeddings de ideas (3,733 vectores × 1,536 dims)
2. Aplica KMeans con `n_clusters=25`
3. Extrae keywords con TF-IDF por cluster
4. Genera `ClusterTopic` con label, keywords, centroid y tamaño

#### Fase 2: Planning
1. Define 8 secciones estándar de paper de perspectivas
2. Mapea cada sección a topics relevantes
3. Busca ideas cercanas a centroids (`cosine_similarity`)
4. PlannerAgent genera outline estructurado
5. ReviewerAgent valida (cambios conservadores)

#### Fase 3: Writing
1. Para cada párrafo del outline:
   - Genera query semántico desde `key_idea + supporting_points`
   - Busca contexto específico (NO usa abstract genérico)
   - WriterAgent escribe párrafo fundamentado
2. Genera summary de sección para memoria
3. ReviewerAgent revisa sección completa

---

## 🤖 Sistema de Agentes

### Diagrama de Clases

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        +client: OpenAI
        +model: str = "gpt-5.2"
        +_call_api(system_prompt, user_prompt) str
        +_call_api_json(system_prompt, user_prompt) dict
    }
    
    class PlannerAgent {
        +generate_outline(title, abstract, topics) PaperOutline
        +refine_outline(outline, feedback) PaperOutline
        -_build_prompt(title, abstract, topics, ideas) str
    }
    
    class WriterAgent {
        +abstract_context: str
        +write_section(name, previous, context) Section
        +write_paragraph(outline, context, memory) str
        -_get_section_instructions(name) str
    }
    
    class ReviewerAgent {
        +abstract_context: str
        +context_manager: EnhancedContextManager
        +review_outline(outline) tuple[str, bool]
        +review_section(section, memory) Section
        +review_full_paper(paper) Paper
        +generate_critical_review(paper) str
        -_strengthen_with_rag(content) str
    }

    BaseAgent <|-- PlannerAgent
    BaseAgent <|-- WriterAgent
    BaseAgent <|-- ReviewerAgent
```

### Flujo de Interacción

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant P as PlannerAgent
    participant W as WriterAgent
    participant R as ReviewerAgent
    participant CM as ContextManager
    participant M as SectionMemory

    Note over O: Fase 1: Cluster Analysis
    O->>O: phase1_analyze_topics()
    
    Note over O: Fase 2: Planning
    O->>P: generate_outline(title, abstract, topics)
    P-->>O: PaperOutline
    
    loop outline_review_iterations
        O->>R: review_outline(outline)
        R-->>O: (feedback, requires_changes)
        alt requires_changes
            O->>P: refine_outline(outline, feedback)
            P-->>O: refined_outline
        end
    end
    
    Note over O: Fase 3: Writing
    loop cada sección
        loop cada párrafo
            O->>CM: get_context_for_idea(paragraph.to_query())
            CM-->>O: evidence[]
            O->>W: write_paragraph(paragraph, evidence, memory)
            W-->>O: content
        end
        O->>M: generate_summary(section)
        M-->>O: summary
        
        loop review_iterations
            O->>R: review_section(section, memory)
            R->>CM: search_for_evidence(4 query types)
            CM-->>R: supporting evidence
            R-->>O: improved_section
        end
    end
    
    O->>R: generate_critical_review(paper)
    R-->>O: critical_review.md
```

---

## 🔍 Sistema RAG

### Arquitectura de Búsqueda

```mermaid
flowchart LR
    subgraph Query["🔎 Generación de Query"]
        Q1["Párrafo actual"] --> Q2["key_idea +\nsupporting_points"]
        Q2 --> Q3["Query semántico"]
    end
    
    subgraph Indices["📊 Índices"]
        I1[("💡 Ideas\n3,733")]
        I2[("📌 Claims\n3,839")]
        I3[("📚 Refs\n1,200+")]
    end
    
    subgraph Search["🎯 Búsqueda"]
        S1["Embedding Query\ntext-embedding-3-small"]
        S2["Cosine Similarity"]
        S3["Ranking por Score"]
        S4["Filtro Confianza"]
        S5["Diversificación\nmax_per_paper"]
    end
    
    subgraph Output["📝 Contexto"]
        O1["Ideas relevantes"]
        O2["Claims con evidencia"]
        O3["Referencias citables"]
    end
    
    Q3 --> S1
    I1 & I2 & I3 --> S2
    S1 --> S2 --> S3 --> S4 --> S5
    S5 --> O1 & O2 & O3

    style Query fill:#e3f2fd
    style Indices fill:#f3e5f5
    style Search fill:#fff3e0
    style Output fill:#e8f5e9
```

### RAG en ReviewerAgent

El ReviewerAgent usa 4 tipos de queries para fortalecer argumentos:

```mermaid
flowchart TD
    Section["📄 Sección a revisar"] --> Analysis["🔍 Analizar contenido"]
    
    Analysis --> Q1["🛡️ Query 1: SUPPORT\nEvidencia que respalde"]
    Analysis --> Q2["⚔️ Query 2: COUNTER\nContraargumentos"]
    Analysis --> Q3["📊 Query 3: EXAMPLES\nEjemplos concretos"]
    Analysis --> Q4["🔗 Query 4: CONNECTIONS\nConexiones interdisciplinarias"]
    
    Q1 --> RAG["RAG Search"]
    Q2 --> RAG
    Q3 --> RAG
    Q4 --> RAG
    
    RAG --> Evidence["📚 Evidencia consolidada"]
    Evidence --> Strengthen["✨ Fortalecer sección"]

    style Q1 fill:#c8e6c9
    style Q2 fill:#ffcdd2
    style Q3 fill:#fff9c4
    style Q4 fill:#b3e5fc
```

---

## 📦 Modelos de Datos

### Estructura del Outline

```mermaid
erDiagram
    PaperOutline ||--o{ SectionOutline : contiene
    SectionOutline ||--o{ ParagraphOutline : contiene
    
    PaperOutline {
        string title
        string abstract
        string thesis_statement
    }
    
    SectionOutline {
        string section_name
        string section_purpose
    }
    
    ParagraphOutline {
        string key_idea
        list supporting_points
        list suggested_sources
    }
```

### Datos Extraídos

```mermaid
erDiagram
    ProcessedPaper ||--o{ Idea : contiene
    ProcessedPaper ||--o{ Claim : contiene
    ProcessedPaper ||--o{ Reference : cita
    
    Idea {
        uuid id
        uuid paper_id
        string paper_title
        string section
        string idea
        string context
        string importance
        list keywords
    }
    
    Claim {
        uuid id
        uuid paper_id
        string claim
        string evidence
        string evidence_type
        string confidence
        list cited_references
    }
    
    Reference {
        uuid id
        string formatted
        list authors
        int year
        string title
        string venue
    }
```

---

## 📁 Estructura del Proyecto

```
TheAIWriter/
├── src/ai_writer/
│   ├── main.py                    # CLI con Typer
│   ├── __main__.py                # Entry point
│   │
│   ├── agents/                    # 🤖 Agentes de IA
│   │   ├── base_agent.py          # Clase base abstracta
│   │   ├── planner_agent.py       # Generación de outlines
│   │   ├── writer_agent.py        # Escritura de contenido
│   │   └── reviewer_agent.py      # Revisión RAG-enhanced
│   │
│   ├── orchestrators/             # 🎼 Orquestación
│   │   └── advanced_orchestrator.py  # Pipeline 3 fases
│   │
│   ├── embeddings/                # 🧮 Sistema de embeddings
│   │   ├── embedding_index.py     # Índice NPZ genérico
│   │   └── rag_system.py          # Sistema RAG
│   │
│   ├── processors/                # ⚙️ Procesamiento
│   │   ├── batch_processor.py     # Procesamiento en lote
│   │   ├── pdf_processor.py       # Procesador individual
│   │   ├── extraction_agent.py    # Extractor de ideas/claims
│   │   └── models.py              # Modelos Pydantic
│   │
│   ├── utils/                     # 🔧 Utilidades
│   │   ├── cluster_analyzer.py    # Análisis de clusters
│   │   ├── enhanced_context_manager.py  # Contexto RAG
│   │   └── pipeline_logger.py     # Logging del pipeline
│   │
│   ├── models/                    # 📋 Modelos de datos
│   │   ├── paper.py               # Paper, Section
│   │   └── outline.py             # PaperOutline
│   │
│   ├── readers/                   # 📖 Lectores
│   │   ├── markdown_reader.py
│   │   └── pdf_reader.py
│   │
│   ├── writers/                   # ✍️ Escritores
│   │   ├── markdown_writer.py
│   │   └── pdf_writer.py
│   │
│   └── scripts/                   # 📜 Scripts
│       └── run_advanced_paper.py
│
├── config/
│   └── settings.py                # Configuración Pydantic
│
├── docs/
│   └── architecture.md            # Este documento
│
├── data/                          # ⚠️ No tracked en git
│   ├── references/
│   │   ├── markdown/ABSTRACT.md   # Abstract del paper
│   │   └── pdfs/                  # PDFs de referencia
│   ├── processed/
│   │   ├── embeddings/            # Índices NPZ
│   │   └── indices/               # JSONL files
│   ├── logs/                      # Logs del pipeline
│   └── output/
│       ├── drafts/                # Outlines
│       └── final/                 # Papers generados
│
└── pyproject.toml
```

---

## 💻 CLI y Uso

### Comandos Disponibles

```bash
# Generar paper completo
python -m ai_writer generate "Título del Paper"

# Con opciones
python -m ai_writer generate "Título" \
    --clusters 25 \
    --reviews 1 \
    --output ./output/

# Solo generar outline
python -m ai_writer outline "Título"

# Revisar paper existente
python -m ai_writer review ./paper.md

# Procesar nuevos PDFs
python -m ai_writer process --input ./pdfs/

# Ver configuración
python -m ai_writer version
```

### Configuración

```python
# config/settings.py
default_model = "gpt-5.2"      # Modelo principal
reasoning_model = "gpt-5.2"    # Tareas complejas
fast_model = "gpt-5.2"         # Operaciones rápidas
embedding_model = "text-embedding-3-small"

# Parámetros del pipeline
n_clusters = 25                # Clusters para análisis
review_iterations = 1          # Iteraciones de revisión por sección
outline_review_iterations = 1  # Iteraciones de refinamiento del outline
```

---

## 📝 Notas de Implementación

### Memoria de Sección

El sistema mantiene coherencia entre secciones usando un diccionario de summaries:

```python
section_memory = {
    "Introducción": "Resumen de 3-5 oraciones...",
    "Estado del Arte": "Resumen de 3-5 oraciones...",
    # ...
}
```

Cada agente recibe este contexto para mantener continuidad argumentativa.

### Logging del Pipeline

Todos los pasos se registran en `data/logs/run_{title}/`:

- `phase1_topics.json`: Topics extraídos
- `phase2_outline.json`: Outline generado
- `outline_feedback_{n}.json`: Feedback del reviewer
- `outline_refined_{n}.json`: Outline refinado
- `run_log.json`: Metadata de ejecución

### Refinamiento Conservador

El ReviewerAgent aplica cambios conservadores al outline:
- Solo fusiona párrafos si hay **redundancia evidente**
- Valora la profundidad y exhaustividad
- Preserva la estructura original cuando es posible
