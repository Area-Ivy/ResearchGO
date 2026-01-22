# Mindmap Service (思维导图服务)

基于 AI 的思维导图生成微服务，可从 PDF 论文自动生成结构化思维导图。

## 服务信息

- **端口**: 8007
- **API 前缀**: `/api/mindmap`

## 快速启动

```bash
# 1. 进入服务目录
cd backend/services/mindmap-service

# 2. 创建虚拟环境（可选）
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量（创建 .env 文件）

# 5. 启动服务
python run.py
uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload
```

## 环境变量配置

在服务目录下创建 `.env` 文件：

```env
# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=research-papers
MINIO_SECURE=False

# OpenAI 配置（必需）
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

## API 端点

### 健康检查
```
GET /api/mindmap/health
```

### 生成思维导图
```
POST /api/mindmap/generate
Content-Type: application/json

{
  "object_name": "20260122_paper.pdf",
  "max_depth": 3,
  "language": "zh"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Mindmap generated successfully",
  "mindmap_data": {
    "meta": {"name": "论文思维导图", "version": "1.0"},
    "format": "node_tree",
    "data": {
      "id": "root",
      "topic": "论文标题",
      "children": [...]
    }
  },
  "pdf_info": {
    "object_name": "20260122_paper.pdf",
    "original_name": "paper.pdf",
    "size": 1234567
  }
}
```

## 测试服务

```bash
python test_mindmap_service.py
```

## 目录结构

```
mindmap-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── mindmap.py       # API 路由
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mindmap.py       # 思维导图数据模型
│   │   └── chat.py          # ChatMessage 模型
│   └── services/
│       ├── __init__.py
│       ├── minio_service.py    # MinIO 文件服务
│       ├── openai_service.py   # OpenAI API 服务
│       └── mindmap_service.py  # 思维导图生成服务
├── requirements.txt
├── run.py
├── test_mindmap_service.py
└── README.md
```

## 依赖服务

- **MinIO**: 存储 PDF 文件
- **OpenAI API**: 生成思维导图

## 工作流程

1. 接收请求（PDF 对象名称）
2. 从 MinIO 下载 PDF 文件
3. 使用 pdfplumber 提取文本（前20页）
4. 调用 OpenAI 分析论文并生成 jsMind 格式的思维导图
5. 返回思维导图 JSON 数据

## 注意事项

1. PDF 文件必须已上传到 MinIO
2. 需要有效的 OpenAI API Key
3. 生成思维导图可能需要 30-60 秒
4. 输出格式兼容 jsMind 前端组件

