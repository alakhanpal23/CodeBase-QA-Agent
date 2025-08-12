# 🤖 CodeBase QA Agent

An AI-powered codebase question answering system that provides intelligent responses with code snippets, citations, and context.

## ✨ Features

- **🔍 Intelligent Code Search**: Vector-based semantic search through your codebase
- **💬 Natural Language Queries**: Ask questions in plain English about your code
- **📝 Code Snippets**: Get relevant code snippets with surrounding context
- **🔗 Citations**: Precise file paths and line numbers for all references
- **🎨 Modern UI**: Clean, responsive interface built with Next.js 14 and Tailwind CSS
- **⚡ Fast Performance**: Optimized vector search with FAISS
- **🔒 Secure**: Path traversal protection and input validation
- **📊 Analytics**: Query performance metrics and usage statistics

## 🏗️ Architecture

### Backend (FastAPI)
- **FastAPI**: High-performance Python web framework
- **Vector Search**: FAISS for efficient similarity search
- **Embeddings**: Sentence Transformers for code vectorization
- **RAG Pipeline**: Retrieval-Augmented Generation for intelligent answers
- **Repository Management**: Git integration for automatic code ingestion

### Frontend (Next.js 14)
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **TanStack Query**: Data fetching and caching
- **Zustand**: State management
- **Monaco Editor**: Code syntax highlighting

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Git

### Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-key-or-dummy-for-mock"

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Start development server
npm run dev
```

### Access the Application
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage

### 1. Add Repositories
1. Go to the **Repositories** page
2. Enter a GitHub repository URL
3. Click **Add Repository**
4. Wait for ingestion to complete

### 2. Ask Questions
1. Go to the **Chat** page
2. Select repositories from the sidebar
3. Ask questions like:
   - "How does authentication work?"
   - "Show me the main API endpoints"
   - "What database models are defined?"
   - "How is error handling implemented?"

### 3. View Results
- **Answer**: AI-generated response with explanations
- **Citations**: File paths and line numbers
- **Code Snippets**: Relevant code with syntax highlighting
- **Context**: Surrounding code for better understanding

## 🔧 Configuration

### Backend Configuration (`backend/app/core/config.py`)

```python
# OpenAI Configuration
openai_api_key: str = "your-key-here"
openai_model: str = "gpt-4"

# Embedding Configuration
embed_mode: str = "mock"  # Options: openai | mock
embed_model: str = "all-MiniLM-L6-v2"

# Storage Configuration
index_dir: str = "backend/app/data/indexes"
repos_dir: str = "backend/app/data/repos"

# Snippet Configuration
snippet_context_lines: int = 6
snippet_max_chars: int = 1200
```

### Frontend Configuration (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run Frontend Tests
```bash
cd frontend
npm test
```

### Run Deployment Tests
```bash
# Make sure both backend and frontend are running
python test_deployment.py
```

## 📊 API Endpoints

### Repository Management
- `GET /repos` - List all repositories
- `POST /ingest` - Add a new repository
- `DELETE /repos/{repo_id}` - Delete a repository

### Query System
- `POST /query` - Ask questions about the codebase
- `GET /health` - Health check
- `GET /stats` - System statistics

### Example API Usage

```bash
# Add repository
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "github",
    "url": "https://github.com/user/repo",
    "repo_id": "my-repo",
    "include_globs": ["**/*.py", "**/*.js"],
    "exclude_globs": [".git/**", "node_modules/**"]
  }'

# Query codebase
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does authentication work?",
    "repo_ids": ["my-repo"],
    "k": 5
  }'
```

## 🔒 Security Features

- **Path Traversal Protection**: Prevents access to files outside repository directories
- **Input Validation**: Comprehensive request validation with Pydantic
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Rate Limiting**: Built-in request rate limiting
- **File Size Limits**: Configurable maximum file and repository sizes

## 🚀 Deployment

### Quick Deployment

**One-Command Deployment:**
```bash
# Development
./deploy.sh development

# Production
./deploy.sh production
```

### Manual Production Deployment

#### Option 1: Docker Compose (Recommended)
```bash
# Clone the repository
git clone https://github.com/alakhanpal23/CodeBase-QA-Agent.git
cd CodeBase-QA-Agent

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export ENVIRONMENT="production"

# Deploy with Docker
docker-compose up -d

# Check status
docker-compose ps
```

#### Option 2: Manual Setup

**Backend:**
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export ENVIRONMENT="production"
export EMBED_MODE="auto"

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Start production server
npm start
```

### Environment Configuration

#### Backend (.env)
```bash
# Required
OPENAI_API_KEY=your-openai-api-key-here

# Optional (with defaults)
ENVIRONMENT=production
EMBED_MODE=auto  # auto | openai | local | mock
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

#### Frontend (.env.production.local)
```bash
NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com
NEXT_PUBLIC_ENVIRONMENT=production
```

### Deployment Modes

#### 🤖 Auto Mode (Recommended)
- **With OpenAI API Key**: Uses OpenAI embeddings and GPT-4
- **Without API Key**: Falls back to local embeddings and mock responses
- **Perfect for**: Seamless transition from development to production

#### 🔧 Manual Modes
- **`openai`**: Force OpenAI (requires API key)
- **`local`**: Use local sentence transformers
- **`mock`**: Development/testing mode

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Run comprehensive tests
python test_deployment.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and embeddings
- **Hugging Face** for Sentence Transformers
- **Facebook Research** for FAISS vector search
- **Vercel** for Next.js framework
- **FastAPI** team for the excellent Python framework

## 🔧 Production Checklist

### Before Deployment
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Configure production API URL in frontend
- [ ] Set up SSL certificates (if using HTTPS)
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging

### After Deployment
- [ ] Run health checks (`curl http://your-domain/health`)
- [ ] Test repository ingestion
- [ ] Test query functionality
- [ ] Monitor resource usage
- [ ] Set up backup procedures

## 🔒 Security Considerations

- **API Keys**: Store securely, never commit to version control
- **HTTPS**: Use SSL/TLS in production
- **Rate Limiting**: Configure appropriate limits
- **Input Validation**: All inputs are validated by Pydantic
- **Path Traversal**: Protected against directory traversal attacks
- **CORS**: Configure for your domain

## 📊 Monitoring

### Key Metrics
- Response times (`/health` endpoint)
- Memory usage (embedding models can be large)
- Disk usage (vector indexes and repositories)
- API rate limits and usage

### Logs
- Backend: Structured JSON logs with `structlog`
- Frontend: Next.js built-in logging
- Docker: `docker-compose logs [service]`

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

### Common Issues

**"No relevant code found"**
- Check if repository was properly ingested
- Verify repository has supported file types
- Try rephrasing your question

**Slow responses**
- Check if using local embeddings (slower than OpenAI)
- Monitor memory usage
- Consider upgrading hardware

**OpenAI API errors**
- Verify API key is valid
- Check API quota and billing
- System will fall back to local/mock mode

---

**Built with ❤️ for developers who want to understand their code better**