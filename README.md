# TheAIWriter

AI-powered academic paper writing assistant that uses AI agents to help you write, review, and improve academic papers.

## Features

- 📄 **PDF & Markdown Reference Reading**: Import and process reference documents
- 🤖 **AI Writing Agents**: Intelligent agents for writing and reviewing papers
- 📝 **Multiple Output Formats**: Export to Markdown and PDF
- 🔄 **Iterative Refinement**: Review and improve your papers with AI feedback

## Project Structure

```
TheAIWriter/
├── src/ai_writer/      # Main source code
│   ├── agents/         # AI agents (writer, reviewer)
│   ├── readers/        # Document readers (PDF, Markdown)
│   ├── writers/        # Document writers (PDF, Markdown)
│   ├── models/         # Data models (Paper, Reference)
│   └── utils/          # Utility functions
├── data/
│   ├── references/     # Reference documents (PDFs, Markdown)
│   └── output/         # Generated papers
├── config/             # Configuration files
└── tests/              # Test suite
```

## Installation

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Copy `.env.example` to `.env` and configure your API keys:
```bash
cp .env.example .env
```

## Usage

```python
from ai_writer.main import AIWriter

writer = AIWriter()
paper = writer.create_paper(
    topic="Your research topic",
    references=["path/to/reference.pdf"]
)
```

## Configuration

Set your API keys in the `.env` file:

```env
OPENAI_API_KEY=your-api-key-here
```

## License

MIT License
