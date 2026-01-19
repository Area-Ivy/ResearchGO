# ResearchGO API Backend

AI-powered research assistant API built with FastAPI, OpenAI, and OpenAlex.

## Features

### Chat System
- ✅ Real-time streaming responses using Server-Sent Events (SSE)
- ✅ OpenAI GPT-4o integration
- ✅ Conversation context management
- ✅ Markdown and code highlighting support

### Literature Search
- ✅ Search 250M+ academic papers via OpenAlex API
- ✅ Advanced filtering (year, citations, open access)
- ✅ AI-powered paper summarization
- ✅ Multiple citation formats (BibTeX, RIS, APA, MLA)
- ✅ Related papers discovery
- ✅ Author information lookup

### General
- ✅ CORS support for frontend integration
- ✅ Health check endpoints
- ✅ Comprehensive error handling and logging

## Prerequisites

- Python 3.9+
- OpenAI API key

## Installation

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment:**
   
   Windows:
   ```bash
   .venv\Scripts\activate
   ```
   
   Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create `.env` file:**
   ```bash
   # Create .env file in backend directory
   OPENAI_API_KEY=your_openai_api_key_here
   CONTACT_EMAIL=your_email@example.com  # Optional, for OpenAlex polite pool
   OPENAI_MODEL=gpt-4o
   HOST=0.0.0.0
   PORT=8000
   ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

## Configuration

Edit the `.env` file to configure:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4o)
- `CONTACT_EMAIL`: Your email for OpenAlex polite pool (optional, gets better rate limits)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

## Running the Server

**Development mode (with auto-reload):**
```bash
python run.py
```

**Production mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
GET /api/chat/health
```

Returns health status of the service.

### Chat Message
```
POST /api/chat/message
```

Send a chat message and receive streaming response.

**Request Body:**
```json
{
  "message": "Explain transformer architecture",
  "conversation_history": [
    {
      "role": "user",
      "content": "Previous message"
    },
    {
      "role": "assistant",
      "content": "Previous response"
    }
  ],
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response:**
Server-Sent Events (SSE) stream with the following events:
- `message`: Content chunks
- `done`: Completion signal
- `error`: Error information

### Literature Search

#### Search Papers
```
POST /api/literature/search
```

Search academic papers from OpenAlex.

**Request Body:**
```json
{
  "query": "machine learning",
  "filters": {
    "publication_year_start": 2020,
    "publication_year_end": 2024,
    "min_cited_by_count": 100,
    "open_access_only": true
  },
  "page": 1,
  "per_page": 20,
  "sort": "cited_by_count"
}
```

#### Get Paper Details
```
GET /api/literature/work/{work_id}
```

#### Get Related Papers
```
GET /api/literature/related/{work_id}?limit=10
```

#### Generate AI Summary
```
POST /api/literature/summarize
```

Generate structured AI summary of a paper in Chinese or English.

#### Export Citations
```
POST /api/literature/export
```

Export citations in various formats: `bibtex`, `ris`, `apa`, `mla`

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py              # Chat endpoints
│   │   └── literature.py        # Literature search endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py    # OpenAI API integration
│   │   └── openalex_service.py  # OpenAlex API integration
│   └── models/
│       ├── __init__.py
│       ├── chat.py              # Chat models
│       └── literature.py        # Literature models
├── .env                         # Environment variables (create this)
├── requirements.txt             # Python dependencies
├── run.py                       # Development server script
└── README.md                    # This file
```

## Development

### Adding New Endpoints

1. Create new route file in `app/api/`
2. Import and include router in `app/main.py`
3. Add models in `app/models/` if needed

### Testing

Test the API using curl:

```bash
# Health check
curl http://localhost:8000/health

# Chat message
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "conversation_history": [],
    "stream": false
  }'

# Search literature
curl -X POST http://localhost:8000/api/literature/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "page": 1,
    "per_page": 10
  }'

# Get paper details
curl http://localhost:8000/api/literature/work/W2741809807
```

## Troubleshooting

### "OPENAI_API_KEY is not set" error
Make sure you've created a `.env` file with your OpenAI API key.

### CORS errors
Check that your frontend URL is included in the `ALLOWED_ORIGINS` environment variable.

### Connection refused
Ensure the backend server is running and the port (8000) is not in use by another application.

## License

MIT

