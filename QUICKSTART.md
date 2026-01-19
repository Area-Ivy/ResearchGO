# 快速启动指南

## 第一步: 后端设置

1. **进入后端目录并创建虚拟环境:**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **安装依赖:**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置OpenAI API密钥:**
   
   在 `backend` 目录下创建 `.env` 文件:
   ```env
   OPENAI_API_KEY=你的OpenAI_API密钥
   OPENAI_MODEL=gpt-4o
   CONTACT_EMAIL=your_email@example.com  # 可选,用于OpenAlex API
   HOST=0.0.0.0
   PORT=8000
   ALLOWED_ORIGINS=http://localhost:5173
   ```

4. **启动后端服务器:**
   ```bash
   python run.py
   ```
   
   ✅ 后端运行在: http://localhost:8000

## 第二步: 前端设置

1. **打开新终端,进入前端目录:**
   ```bash
   cd frontend
   ```

2. **安装依赖 (如果还没安装):**
   ```bash
   npm install
   ```

3. **配置API地址 (可选):**
   
   在 `frontend` 目录下创建 `.env` 文件:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```
   
   如果不创建,默认会使用 http://localhost:8000

4. **启动前端开发服务器:**
   ```bash
   npm run dev
   ```
   
   ✅ 前端运行在: http://localhost:5173

## 第三步: 使用应用

1. **访问Dashboard:** http://localhost:5173/
   - 查看研究统计
   - 浏览推荐论文
   - 查看知识熵可视化

2. **访问Chat:** http://localhost:5173/chat
   - 与AI助手对话
   - 询问研究问题
   - 获得实时流式响应

3. **访问文献检索:** http://localhost:5173/literature
   - 搜索2.5亿+学术论文
   - 按年份、引用数、开放获取筛选
   - 查看论文详情和摘要
   - 生成AI摘要(中文/英文)
   - 导出引用(BibTeX/RIS/APA/MLA)
   - 与AI讨论论文内容

## 验证安装

### 测试后端健康检查:
```bash
curl http://localhost:8000/health
```

应该返回:
```json
{"status":"healthy","service":"chat-api"}
```

### 测试Chat API:
```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Hello\",\"stream\":false}"
```

### 测试文献搜索API:
```bash
curl -X POST http://localhost:8000/api/literature/search \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"machine learning\",\"page\":1,\"per_page\":10}"
```

## 常见问题

### Q: 后端启动失败,提示"OPENAI_API_KEY is not set"
**A:** 确保在 `backend/.env` 文件中设置了有效的OpenAI API密钥

### Q: 前端无法连接后端
**A:** 
1. 确认后端正在运行: http://localhost:8000/health
2. 检查 `frontend/.env` 中的 `VITE_API_BASE_URL` 设置
3. 确认没有防火墙阻止连接

### Q: Chat页面显示错误
**A:**
1. 打开浏览器开发者工具查看具体错误
2. 确认OpenAI API密钥有效且有足够额度
3. 检查后端日志输出

### Q: 依赖安装失败
**A:**
- Python依赖: 确保使用Python 3.9+
- Node依赖: 确保使用Node.js 16+
- 尝试清除缓存后重新安装

## 下一步

- 阅读完整文档: [README.md](README.md)
- 查看后端API文档: http://localhost:8000/docs
- 自定义配置和样式
- 添加更多功能

## 技术支持

如有问题,请检查:
1. 后端日志输出
2. 浏览器控制台错误
3. 网络请求详情

祝使用愉快! 🚀

