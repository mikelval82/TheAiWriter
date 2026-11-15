# TheAIWriter

🤖 AI-powered academic writing system specialized in **perspective papers**. Uses a 3-phase architecture with semantic search over curated reference embeddings.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

TheAIWriter generates high-quality perspective papers by:
1. **Analyzing** your reference corpus through semantic clustering
2. **Planning** a detailed outline with paragraph-level ideas
3. **Writing** each paragraph with targeted semantic search for evidence

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Input["📥 Input Layer"]
        PDFs[("📄 PDFs")]
        Abstract["📝 Abstract"]
    end

    subgraph Processing["⚙️ Processing Pipeline"]
        Reader["PyMuPDF\nPDF→Texto"]
        Extractor["PDFExtractionAgent\nIdeas, Claims, Refs"]
        Embedder["Local\nEmbeddings"]
        PDFs --> Reader --> Extractor --> Embedder
    end

    subgraph Storage["💾 Vector Storage"]
        Ideas[("💡 Ideas\n3,733")]
        Claims[("📌 Claims\n3,839")]
        Refs[("📚 References\n1,200+")]
        Embedder --> Ideas & Claims & Refs
    end

    subgraph Generation["🚀 3-Phase Generation"]
        direction TB
        P1["🔬 Phase 1\nCluster Analysis"]
        P2["📋 Phase 2\nPlanning"]
        P3["✍️ Phase 3\nWriting"]
        P1 --> P2 --> P3
    end

    subgraph Agents["🤖 Agent System"]
        Planner["PlannerAgent\nOutline Generation"]
        Writer["WriterAgent\nParagraph Writing"]
        Reviewer["ReviewerAgent\nRAG-Enhanced Review"]
        Summary["PaperSummaryAgent\nSection Summaries"]
        Memory["📝 Section Memory\nShort-term Context"]
    end

    subgraph PostProcess["📋 Post-Processing"]
        RefProc["ReferenceProcessor\nCitations → Bibliography"]
        Translator["TranslatorAgent\n(Optional)"]
    end

    subgraph Output["📤 Output"]
        Paper["📄 Perspective Paper"]
        PaperEN["📄 Paper (EN)"]
        Review["📋 Critical Review"]
    end

    Abstract --> P1
    Ideas --> P1
    P1 -->|Topics| Planner
    Planner -->|Outline| P2
    P2 -->|Refined Outline| Writer
    Ideas & Claims & Refs --> Writer
    Writer --> Memory
    Writer --> Summary
    Memory --> Reviewer
    Reviewer --> P3
    P3 --> RefProc
    Refs --> RefProc
    RefProc --> Paper & Review
    RefProc --> Translator --> PaperEN
```

## ✨ Features

- **🔬 Semantic Clustering**: Extracts main topics from embedding space using KMeans
- **📋 Intelligent Planning**: Generates detailed outlines with paragraph-level key ideas
- **✍️ Targeted Writing**: Each paragraph gets context from semantic search on its specific idea
- **🔄 RAG-Enhanced Review**: Reviewer searches for supporting/counter evidence
- **📝 Section Memory**: Maintains coherence across sections with summaries
- **� Reference Processing**: Automatic citation resolution and bibliography generation
- **🌐 Translation**: Optional translation to English via TranslatorAgent
- **�📊 Pipeline Logging**: Full traceability of generation process

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/your-username/TheAIWriter.git
cd TheAIWriter

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .

# Text generation uses the Claude Code CLI: install it and log in once
claude   # then /login

# Optional: override models or backends
cp .env.example .env

# After changing the embedding model, rebuild the indices
python -m ai_writer reindex
```

## 🚀 Usage

### Command Line Interface

```bash
# Generate a perspective paper
python -m ai_writer generate "Hacia Agentes Empáticos Fundamentales"

# Generate with custom options
python -m ai_writer generate "Paper Title" -c 30 -r 2 -o ./output/

# Generate only the outline
python -m ai_writer outline "Paper Title"

# Review an existing paper
python -m ai_writer review ./paper.md

# Show configuration
python -m ai_writer version

# Process new PDFs into the index
python -m ai_writer process --input ./new_papers/
```

### CLI Options

| Command | Description |
|---------|-------------|
| `generate` | Generate a complete perspective paper |
| `outline` | Generate only the structured outline |
| `review` | Generate critical review of existing paper |
| `process` | Process PDFs and build embedding indices |
| `stats` | Show embedding index statistics |
| `version` | Show configuration and version info |

### Generate Options

| Option | Default | Description |
|--------|---------|-------------|
| `-c, --clusters` | 25 | Number of clusters for topic extraction |
| `-r, --reviews` | 1 | Review iterations per section |
| `-o, --output` | `data/output/final/` | Output directory |
| `-a, --abstract` | `ABSTRACT.md` | Path to abstract file |
| `--no-log` | False | Disable pipeline logging |

## 📁 Project Structure

```
TheAIWriter/
├── src/ai_writer/
│   ├── agents/           # AI agents
│   │   ├── planner_agent.py       # Outline generation
│   │   ├── writer_agent.py        # Paragraph writing
│   │   ├── reviewer_agent.py      # RAG-enhanced review
│   │   ├── translator_agent.py    # Paper translation
│   │   └── paper_summary_agent.py # Section summaries
│   ├── orchestrators/    # Pipeline orchestration
│   │   └── advanced_orchestrator.py          # 3-phase pipeline
│   ├── processors/       # PDF processing
│   │   ├── extraction_agent.py    # Ideas/claims extraction
│   │   └── batch_processor.py     # Batch PDF processing
│   ├── utils/            # Utilities
│   │   ├── cluster_analyzer.py          # KMeans clustering
│   │   ├── enhanced_context_manager.py  # RAG context
│   │   ├── reference_processor.py       # Citation processing
│   │   └── pipeline_logger.py           # Execution logging
│   ├── embeddings/       # Embedding management
│   ├── readers/          # Document readers
│   ├── writers/          # Document writers
│   └── models/           # Data models (Paper, Outline)
├── data/
│   ├── references/       # Source PDFs and markdown
│   ├── processed/        # Embeddings and indices
│   ├── logs/             # Pipeline execution logs
│   └── output/           # Generated papers
├── config/               # Settings and configuration
├── docs/                 # Architecture documentation
└── tests/                # Test suite
```

## ⚙️ Configuration

No API key is needed by default. Text is generated through the Claude Code CLI
(`claude -p`, using its own login) and embeddings are computed locally with
`sentence-transformers`. Everything is set through environment variables or a
`.env` file; the values below are the defaults:

```env
LLM_BACKEND=claude-code        # or "openai" (needs OPENAI_API_KEY)
DEFAULT_MODEL=sonnet           # Writing and reviewing
REASONING_MODEL=opus           # Outline planning
FAST_MODEL=haiku               # Section summaries

EMBEDDING_BACKEND=local        # or "openai" (needs OPENAI_API_KEY)
EMBEDDING_MODEL=intfloat/multilingual-e5-small
```

An index remembers the embedding model it was built with and refuses to load
under a different one. Run `python -m ai_writer reindex` after changing it; the
previous vectors are kept in `data/processed/embeddings/previous_<model>/`.

## 📊 Embedding Indices

The system uses pre-built indices from processed papers:

| Index | Items | Description |
|-------|-------|-------------|
| Ideas | 3,733 | Key ideas extracted from papers |
| Claims | 3,839 | Specific claims with evidence |
| References | 1,200+ | Bibliographic references |

## 🔄 Pipeline Phases

### Phase 1: Cluster Analysis
- Loads embedding indices
- Applies KMeans clustering (default: 25 clusters)
- Extracts representative topics from each cluster

### Phase 2: Planning
- PlannerAgent generates structured outline
- Each section has paragraphs with key ideas
- ReviewerAgent refines outline (conservative changes)

### Phase 3: Writing
- Writes paragraph-by-paragraph
- Each paragraph gets targeted semantic search context
- Section summaries maintain coherence
- RAG-enhanced review strengthens arguments

## 📝 Output

Generated files in `data/output/final/`:
- `Paper_Title.md` - The perspective paper (Spanish)
- `Paper_Title_EN.md` - Translated version (English, optional)
- `Paper_Title_critical_review.md` - Critical analysis

Logs in `data/logs/run_*/`:
- `phase1_topics.json` - Extracted cluster topics
- `phase2_outline.json` - Generated outline
- `outline_feedback_*.json` - Reviewer feedback
- `run_log.json` - Execution metadata

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with ❤️ using Claude and semantic embeddings.
