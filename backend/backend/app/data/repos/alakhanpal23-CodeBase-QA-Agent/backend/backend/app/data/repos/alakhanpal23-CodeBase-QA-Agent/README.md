# Codebase QA Agent

A backend service that ingests GitHub repositories, indexes source code, and answers natural-language questions about the codebase using Retrieval-Augmented Generation (RAG) with citations to file paths and line ranges.

## Features

- **Repository Ingestion**: Clone GitHub repos or upload ZIP files
- **Smart Chunking**: Syntax-aware code chunking using tree-sitter (with fallback to line-based chunking)
- **Vector Search**: FAISS-based vector indexing with metadata filtering
- **RAG-powered Q&A**: GPT-4 class model with deterministic, cited outputs
- **REST API**: FastAPI endpoints for ingestion and querying
- **CLI Tools**: Command-line interface for local operations
- **Docker Support**: Containerized deployment

## Quick Start

### Local Development

1. **Clone and setup**:
```bash
git clone <your-repo>
cd GithubDownloaderPersonal
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

3. **Run the service**:
```bash
uvicorn backend.app.main:app --reload
```

### Docker

```bash
docker-compose up --build
```

## Usage

### API Endpoints

#### Ingest Repository
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "github",
    "url": "https://github.com/org/repo",
    "branch": "main",
    "repo_id": "org/repo",
    "include_globs": ["**/*.py", "**/*.ts", "**/*.js"],
    "exclude_globs": [".git/**", "node_modules/**"]
  }'
```

#### Query Codebase
```bash
curl -X GET "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Where is JWT refresh implemented?",
    "repo_ids": ["org/repo"],
    "k": 6
  }'
```

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Statistics
```bash
curl http://localhost:8000/stats
```

### CLI Tools

#### Ingest Repository
```bash
python scripts/ingest_repo.py --url https://github.com/org/repo --branch main --repo org/repo
```

#### Query Codebase
```bash
python scripts/query.py --repo org/repo --q "Where is auth implemented?"
```

## Configuration

Key environment variables in `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key
- `INDEX_DIR`: Directory for storing FAISS indexes
- `META_DB_URI`: SQLite database URI for metadata
- `EMBED_BATCH_SIZE`: Batch size for embedding computation
- `MAX_CHUNK_TOKENS`: Maximum tokens per chunk
- `CHUNK_OVERLAP_TOKENS`: Token overlap between chunks

## Architecture

### Components

1. **Ingestion Pipeline**: Clones repos, filters files, chunks code, computes embeddings
2. **Vector Store**: FAISS index with metadata mapping
3. **RAG Engine**: Retrieves relevant chunks and generates answers with citations
4. **API Layer**: FastAPI endpoints for ingestion and querying
5. **CLI Tools**: Command-line interface for local operations

### Data Flow

1. **Ingest**: GitHub URL/ZIP → Clone/Extract → Filter → Chunk → Embed → Index
2. **Query**: Question → Embed → Retrieve → RAG → Answer with Citations

## Testing

Run the test suite:

```bash
pytest tests/
```

Test coverage includes:
- Chunking logic (syntax-aware and fallback)
- Vector store operations
- RAG formatting and citation generation
- API endpoints

## Limitations

- Maximum file size: 500KB per file
- Supported languages: Python, TypeScript, JavaScript (extensible)
- Requires OpenAI API key for embeddings and RAG
- Local FAISS storage (no distributed indexing)

## Roadmap

- [ ] Multi-repo queries with weights
- [ ] GitHub App integration with webhooks
- [ ] Redis caching for repeated queries
- [ ] Basic React UI
- [ ] VSCode/Chrome extensions
- [ ] Support for more programming languages

## License

MIT License
