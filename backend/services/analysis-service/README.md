# Analysis Service (论文分析服务)

基于 AI 的论文分析微服务，可从 PDF 论文自动生成结构化分析报告。

## 服务信息

- **端口**: 8008
- **API 前缀**: `/api/analysis`

## 快速启动

```bash
# 1. 进入服务目录
cd backend/services/analysis-service

# 2. 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量（创建 .env 文件）

# 5. 启动服务
python run.py
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
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
GET /api/analysis/health
```

### 生成论文分析
```
POST /api/analysis/generate
Content-Type: application/json

{
  "object_name": "20260122_paper.pdf",
  "language": "zh"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Analysis generated successfully",
  "analysis": {
    "title": "论文标题",
    "abstract": "论文摘要",
    "research_background": "研究背景",
    "research_problem": "研究问题",
    "methodology": "研究方法",
    "key_findings": "主要发现",
    "innovations": "创新点",
    "limitations": "局限性",
    "future_work": "未来工作",
    "conclusion": "结论"
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
python test_analysis_service.py
```

## 目录结构

```
analysis-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── analysis.py      # API 路由
│   ├── models/
│   │   ├── __init__.py
│   │   ├── analysis.py      # 分析数据模型
│   │   └── chat.py          # ChatMessage 模型
│   └── services/
│       ├── __init__.py
│       ├── minio_service.py    # MinIO 文件服务
│       ├── openai_service.py   # OpenAI API 服务
│       └── analysis_service.py # 论文分析服务
├── requirements.txt
├── run.py
├── test_analysis_service.py
└── README.md
```

## 分析报告内容

服务会生成包含以下内容的结构化分析报告：

1. **论文标题** - 从论文中提取
2. **摘要** - 论文核心内容概括
3. **研究背景** - 研究领域、现状、问题
4. **研究问题** - 核心问题和研究目标
5. **研究方法** - 技术手段、实验设计
6. **主要发现** - 关键结果和贡献
7. **创新点** - 与现有研究的突破
8. **局限性** - 不足和未解决的挑战
9. **未来工作** - 后续研究方向
10. **结论** - 整体贡献和意义

## 依赖服务

- **MinIO**: 存储 PDF 文件
- **OpenAI API**: 生成分析报告

## 注意事项

1. PDF 文件必须已上传到 MinIO
2. 需要有效的 OpenAI API Key
3. 生成分析报告可能需要 60-120 秒
4. 支持中文和英文两种语言输出

