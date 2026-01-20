# ResearchGO

AI-powered research assistant with intelligent chat, literature search, and analytics dashboard.

## Features

- 🤖 **AI Chat Assistant**: Real-time streaming responses powered by OpenAI GPT-4o
- 🧮 **Math Formula Rendering**: LaTeX/KaTeX support for mathematical expressions
- 📚 **Literature Search**: Search 250M+ academic papers from OpenAlex
- 🔍 **Smart Filtering**: Filter by year, citations, open access, and more
- 🧠 **Vector Search**: Semantic search powered by Milvus vector database
- 🎯 **Similarity Detection**: Find similar papers based on content meaning
- 📝 **AI Summarization**: Generate structured summaries of research papers
- 📄 **Citation Export**: Export in BibTeX, RIS, APA, and MLA formats
- 🔗 **Chat Integration**: Discuss papers directly with AI assistant
- 📊 **Research Dashboard**: Track your research activity and progress
- 🎨 **Modern UI**: Deep tech aesthetic with glassmorphism and neon effects
- 🔄 **Real-time Updates**: Server-Sent Events (SSE) for streaming responses
- 💾 **Smart Caching**: Keep-alive component caching to prevent unnecessary re-renders

## Tech Stack

### Frontend
- Vue 3 (Composition API)
- Vite
- Chart.js for visualizations
- Marked for Markdown rendering
- KaTeX for LaTeX math formula rendering
- Highlight.js for code syntax highlighting

### Backend
- FastAPI
- OpenAI API (GPT-4o)
- OpenAlex API (academic search)
- SSE (Server-Sent Events)
- Python 3.9+

### Infrastructure
- **Milvus 2.3.3** - 向量数据库，用于语义搜索
- **Attu** - Milvus 可视化管理界面
- **MinIO** - 对象存储服务
- **etcd** - 分布式配置存储

## Quick Start

### Prerequisites
- Node.js 16+
- Python 3.9+
- OpenAI API key

### Backend Setup

1. **Navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```bash
   # backend/.env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o
   CONTACT_EMAIL=your_email@example.com  # Optional, for OpenAlex
   HOST=0.0.0.0
   PORT=8000
   ALLOWED_ORIGINS=http://localhost:5173
   ```

5. **Run backend:**
   ```bash
   python run.py
   ```

   Backend will be available at: `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create `.env` file:**
   ```bash
   # frontend/.env
   VITE_API_BASE_URL=http://localhost:8000
   ```

4. **Run frontend:**
   ```bash
   npm run dev
   ```

   Frontend will be available at: `http://localhost:5173`

### Milvus 向量数据库设置

1. **启动 Milvus 和相关服务：**
   ```bash
   docker-compose up -d
   ```

2. **验证服务状态：**
   ```bash
   docker-compose ps
   ```
   
   确保以下服务都在运行：
   - ✅ Milvus (端口 19530, 9091)
   - ✅ Attu (端口 9002) - 可视化管理界面
   - ✅ etcd (健康状态)
   - ✅ MinIO (端口 9000, 9001)

3. **访问 Attu 管理界面：**
   - 打开浏览器访问：`http://localhost:9002`
   - 连接地址输入：`localhost:19530`
   - 点击 "Connect" 连接

4. **使用 Python 连接：**
   ```python
   from app.services.milvus_service import milvus_service
   
   # 连接到 Milvus
   milvus_service.connect()
   
   # 创建集合
   milvus_service.create_collection(dim=768)
   
   # 创建索引
   milvus_service.create_index()
   ```

5. **详细使用指南：**
   - 📖 [Milvus 使用指南](docs/MILVUS_USAGE.md) - 完整的使用教程
   - 📖 [Milvus 部署文档](docs/MILVUS_SETUP.md) - 部署和配置说明
   - 📖 [快速开始](docs/QUICK_START.md) - 快速入门指南

## Usage

### Dashboard
Visit `http://localhost:5173/` to see:
- Photon usage statistics
- Knowledge entropy visualization
- Daily research recommendations
- Field progress updates
- Cognitive architecture radar chart
- Neural imprint trends
- Background synthesis queue

### Milvus Manager
Visit `http://localhost:5173/milvus` to:
- View all vector collections
- Create and delete collections  
- Load/Release collections from memory
- Monitor collection statistics
- View collection details and schemas

### Chat Assistant
Visit `http://localhost:5173/chat` to:
- Ask questions about research topics
- Get explanations of complex concepts
- Discuss papers and methodologies
- Receive formatted responses with code highlighting

### Literature Search
Visit `http://localhost:5173/literature` to:
- Search 250M+ academic papers from OpenAlex
- Filter by year, citations, open access status
- View detailed paper information and abstracts
- Generate AI-powered summaries in Chinese or English
- Export citations in BibTeX, RIS, APA, or MLA format
- Discover related papers
- Discuss papers directly with AI assistant

## Project Structure

```
ResearchGO/
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Home.vue              # Dashboard
│   │   │   ├── Chat.vue              # Chat interface
│   │   │   └── LiteratureSearch.vue  # Literature search
│   │   ├── api/
│   │   │   └── literature.js         # Literature API client
│   │   ├── router/
│   │   │   └── index.js              # Routes
│   │   ├── config.js                 # API configuration
│   │   ├── style.css                 # Global styles
│   │   └── App.vue                   # Main layout
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py               # Chat endpoints
│   │   │   └── literature.py         # Literature endpoints
│   │   ├── services/
│   │   │   ├── openai_service.py     # OpenAI integration
│   │   │   └── openalex_service.py   # OpenAlex integration
│   │   ├── models/
│   │   │   ├── chat.py               # Chat models
│   │   │   └── literature.py         # Literature models
│   │   └── main.py               # FastAPI app
│   ├── requirements.txt
│   ├── run.py
│   └── README.md
│
└── README.md                      # This file
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

### Backend (.env)
```env
OPENAI_API_KEY=sk-...           # Required: Your OpenAI API key
OPENAI_MODEL=gpt-4o             # Optional: Model to use
HOST=0.0.0.0                     # Optional: Server host
PORT=8000                        # Optional: Server port
ALLOWED_ORIGINS=http://localhost:5173 # Optional: CORS origins
```

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000 # Backend API URL
```

## Development

### Frontend Development
```bash
cd frontend
npm run dev      # Start dev server
npm run build    # Build for production
npm run preview  # Preview production build
```

### Backend Development
```bash
cd backend
python run.py    # Start with auto-reload
```

## Troubleshooting

### Chat not working
1. Ensure backend is running: `http://localhost:8000/health`
2. Check OpenAI API key is set in `backend/.env`
3. Verify CORS origins include your frontend URL
4. Check browser console for errors

### Connection errors
1. Verify backend is running on port 8000
2. Check `VITE_API_BASE_URL` in frontend `.env`
3. Ensure no firewall blocking connections

### OpenAI API errors
1. Verify API key is valid
2. Check you have sufficient credits
3. Ensure model name is correct

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

