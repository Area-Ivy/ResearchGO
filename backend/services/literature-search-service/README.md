# Literature Search Service (文献检索服务)

基于 OpenAlex 的学术文献检索微服务，提供文献搜索、论文详情、相关论文推荐、作者信息、AI摘要生成和引用导出功能。

## 服务信息

- **端口**: 8005
- **API 前缀**: `/api/literature`
- **数据源**: [OpenAlex](https://openalex.org/) - 免费开放的学术数据库

## 快速启动

```bash
# 1. 进入服务目录
cd backend/services/literature-search-service

# 2. 创建虚拟环境（可选）
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量（创建 .env 文件）
# 参考下方环境变量配置

# 5. 启动服务
python run.py
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

```

## 环境变量配置

在服务目录下创建 `.env` 文件：

```env
# OpenAlex 配置（可选，设置邮箱可提高API速率限制）
CONTACT_EMAIL=your-email@example.com

# OpenAI 配置（用于AI摘要功能，可选）
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

## API 端点

### 健康检查
```
GET /api/literature/health
```

### 搜索文献
```
POST /api/literature/search
Content-Type: application/json

{
  "query": "machine learning",
  "page": 1,
  "per_page": 20,
  "sort": "relevance",  // relevance | cited_by_count | publication_date
  "filters": {
    "publication_year_start": 2020,
    "publication_year_end": 2024,
    "min_cited_by_count": 100,
    "open_access_only": true
  }
}
```

### 获取论文详情
```
GET /api/literature/work/{work_id}
```
- `work_id`: OpenAlex Work ID，如 `W2741809807`

### 获取相关论文
```
GET /api/literature/related/{work_id}?limit=10
```

### 获取作者信息
```
GET /api/literature/author/{author_id}
```

### AI 摘要生成
```
POST /api/literature/summarize
Content-Type: application/json

{
  "work_id": "W2741809807",
  "language": "zh"  // zh | en
}
```

返回结构化摘要：
- `background`: 研究背景
- `method`: 研究方法
- `findings`: 核心发现
- `significance`: 研究意义

### 导出引用
```
POST /api/literature/export
Content-Type: application/json

{
  "work_ids": ["W2741809807", "W1234567890"],
  "format": "bibtex"  // bibtex | ris | apa | mla
}
```

## 测试服务

```bash
python test_literature_service.py
```

## 目录结构

```
literature-search-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── literature.py    # API 路由
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── literature.py    # Pydantic 数据模型
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openalex_service.py  # OpenAlex API 服务
│   │   └── openai_service.py    # OpenAI API 服务
│   └── utils/
│       └── __init__.py
├── requirements.txt
├── run.py
├── test_literature_service.py
└── README.md
```

## 依赖服务

- **OpenAlex API**: 无需认证，但建议设置 `CONTACT_EMAIL` 以获得更高的速率限制
- **OpenAI API** (可选): 仅用于 AI 摘要功能

## 注意事项

1. OpenAlex API 是免费的，但有速率限制。设置 `CONTACT_EMAIL` 可获得更高限制（约 100,000 请求/天）
2. AI 摘要功能需要有效的 OpenAI API Key
3. 此服务不需要数据库，所有数据来自 OpenAlex API

