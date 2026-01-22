# 对话服务 (Conversation Service)

独立的对话管理微服务，负责对话历史和消息管理。

## 功能

- 创建对话
- 获取对话列表
- 获取对话详情（包含消息）
- 更新对话标题
- 删除对话（软删除）
- 添加消息到对话
- 获取对话的所有消息

## 快速启动

### 1. 安装依赖

```bash
cd backend/services/conversation-service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend/services/conversation-service` 目录创建 `.env` 文件：

```env
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_DATABASE=researchgo
MYSQL_USER=researchgo_user
MYSQL_PASSWORD=researchgo123
```

### 3. 启动服务

```bash
python run.py
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

```

服务将在 http://localhost:8002 运行

## API端点

- `POST /api/conversations` - 创建对话
- `GET /api/conversations` - 获取对话列表
- `GET /api/conversations/{id}` - 获取对话详情
- `PUT /api/conversations/{id}` - 更新对话
- `DELETE /api/conversations/{id}` - 删除对话
- `POST /api/conversations/{id}/messages` - 添加消息
- `GET /api/conversations/{id}/messages` - 获取消息列表

## API文档

启动后访问：http://localhost:8002/docs

