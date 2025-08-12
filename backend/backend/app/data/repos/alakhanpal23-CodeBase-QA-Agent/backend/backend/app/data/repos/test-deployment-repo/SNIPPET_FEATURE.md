# 🔍 Snippet + Surrounding Context Feature

## Overview
Enhanced the CodeBase QA Agent with **snippet extraction** - now returns actual code snippets with surrounding context instead of just file paths and line numbers.

## What's New

### ✨ Key Benefits
- **Instant usefulness**: Users see actual code without opening files
- **Better context**: 6 lines of context before/after each match
- **Reduced black box feel**: Users can verify AI reasoning directly
- **Works everywhere**: Both mock mode and GPT-4 mode
- **Safe extraction**: Path traversal protection and text file detection

### 🔧 Implementation Details

#### 1. Configuration (`backend/app/core/config.py`)
```python
# New settings
snippet_context_lines: int = 6          # lines of context before/after
snippet_max_chars: int = 1200           # hard cap to avoid huge payloads
repos_dir: str = "backend/app/data/repos"  # base dir where repos are stored
```

#### 2. Enhanced Schemas (`backend/app/core/schemas.py`)
```python
class Snippet(BaseModel):
    path: str                    # File path
    start: int                   # Original match start line
    end: int                     # Original match end line  
    window_start: int            # Context window start line
    window_end: int              # Context window end line
    code: str                    # Code with surrounding context

class Citation(BaseModel):
    # ... existing fields ...
    url: Optional[str] = None           # Optional deep link
    preview: Optional[str] = None       # Short preview for list views

class QueryResponse(BaseModel):
    # ... existing fields ...
    snippets: List[Snippet] = []        # NEW: Code snippets with context
    mode: Optional[str] = None          # Query mode (mock/gpt4)
    confidence: Optional[float] = None  # Answer confidence score
```

#### 3. Snippet Extraction Service (`backend/app/services/snippets.py`)
- Safe file path handling (prevents path traversal)
- Text file detection (avoids binary files)
- Context window calculation
- Character limit enforcement
- UTF-8 encoding with error handling

#### 4. Enhanced Query Service (`backend/app/services/query.py`)
- Automatic snippet extraction for all citations
- Preview generation for citations
- Mode detection (mock vs GPT-4)
- Graceful fallback when snippet extraction fails

## 🚀 Usage Examples

### API Request
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does JWT refresh work?",
    "repo_ids": ["my-repo"],
    "k": 5
  }'
```

### API Response
```json
{
  "answer": "JWT refresh is handled in app/auth/jwt.py...",
  "citations": [
    {
      "path": "app/auth/jwt.py",
      "start": 42,
      "end": 67,
      "score": 0.83,
      "preview": "def refresh_token(user_id):\n    # Generate new JWT\n    ..."
    }
  ],
  "snippets": [
    {
      "path": "app/auth/jwt.py", 
      "start": 42,
      "end": 67,
      "window_start": 39,
      "window_end": 70,
      "code": "# JWT utilities\n\ndef refresh_token(user_id):\n    # Generate new JWT token\n    token = create_jwt(user_id)\n    return token\n\n# Helper functions"
    }
  ],
  "latency_ms": 245,
  "mode": "mock"
}
```

## 🧪 Testing

### Run Tests
```bash
# Simple standalone test
python simple_snippet_test.py

# Demo with running server
python demo_snippets.py
```

### Start Server
```bash
uvicorn backend.app.main:app --reload
```

## 🔒 Security Features
- **Path traversal protection**: Prevents access outside repo directories
- **Text file detection**: Avoids processing binary files
- **Character limits**: Prevents huge payloads
- **Error handling**: Graceful fallback when files can't be read

## 📈 Performance Impact
- **Minimal overhead**: Only processes text files for existing citations
- **Configurable limits**: Adjustable context lines and character limits
- **Lazy loading**: Snippets only extracted when citations exist
- **Caching ready**: File reads can be cached if needed

## 🎯 Future Enhancements
- **GitHub deep links**: Add URLs like `https://github.com/org/repo/blob/main/file.py#L42-L67`
- **Syntax highlighting**: Add language detection for better formatting
- **Smart context**: Expand context to include full functions/classes
- **Caching**: Cache file contents for better performance

## ✅ Compatibility
- ✅ Works with existing mock mode
- ✅ Works with GPT-4 mode  
- ✅ Backward compatible API
- ✅ No breaking changes
- ✅ Configurable feature (can be disabled)

---

**Ready to ship!** 🚢 This feature provides immediate value with minimal complexity and works in both testing (mock) and production (GPT-4) modes.