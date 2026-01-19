# 文献思维导图功能

## 功能概述

文献思维导图功能允许用户上传论文PDF，并使用AI自动生成结构化的思维导图，帮助快速理解论文的核心内容、研究方法和主要发现。

## 功能特点

### 1. 左右分屏布局
- **左侧**：PDF阅读器，支持翻页浏览论文
- **右侧**：交互式思维导图，展示论文结构

### 2. AI智能分析
- 使用OpenAI GPT模型自动分析论文内容
- 提取论文的核心要点：
  - 研究主题和目标
  - 研究方法
  - 主要发现和结论
  - 创新点
  - 局限性和未来工作

### 3. 交互式思维导图
- 基于Markmap的可视化思维导图
- 支持节点展开/折叠
- 多层级结构展示
- 根据层级自动配色

## 技术架构

### 后端
- **API端点**: `/api/mindmap/generate`
- **PDF解析**: pdfplumber
- **AI分析**: OpenAI API
- **文件存储**: MinIO

### 前端
- **PDF渲染**: PDF.js
- **思维导图**: Markmap (markmap-lib + markmap-view)
- **框架**: Vue 3 + Composition API

## 使用方法

### 1. 准备工作
确保已经：
- 上传论文到文献库（Paper Library）
- 配置了OpenAI API Key

### 2. 生成思维导图
1. 点击侧边栏的 "Paper Mindmap" 菜单
2. 点击 "选择论文" 按钮
3. 从论文列表中选择一篇论文
4. 点击 "生成思维导图" 按钮
5. 等待AI分析完成（通常需要10-30秒）
6. 查看生成的思维导图

### 3. 使用思维导图
- **查看论文**: 左侧PDF阅读器可以翻页浏览
- **探索导图**: 右侧思维导图可以点击节点展开/折叠
- **重新生成**: 如果对结果不满意，可以点击 "重新生成"
- **切换论文**: 点击 "重新选择" 按钮选择其他论文

## 安装部署

### 1. 安装后端依赖
```bash
cd backend
pip install pdfplumber==0.11.0 pypdf2==3.0.1
```

### 2. 安装前端依赖
```bash
cd frontend
npm install markmap-lib markmap-view d3
```

### 3. 配置环境变量
确保 `.env` 文件中配置了：
```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o  # 或其他模型
```

### 4. 启动服务
```bash
# 后端
cd backend
python run.py

# 前端
cd frontend
npm run dev
```

## API文档

### 生成思维导图
**POST** `/api/mindmap/generate`

**请求体**:
```json
{
  "object_name": "20260116_193220_paper.pdf",
  "max_depth": 3,
  "language": "zh"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Mindmap generated successfully",
  "markdown": "# 论文标题\n## 研究方法\n...",
  "structure": {
    "type": "markdown",
    "content": "..."
  },
  "pdf_info": {
    "object_name": "20260116_193220_paper.pdf",
    "original_name": "paper.pdf",
    "size": 1234567,
    "content_type": "application/pdf"
  }
}
```

## 注意事项

1. **PDF大小限制**: 
   - 为了提高处理速度，只分析前20页内容
   - 建议使用10MB以下的PDF文件

2. **API调用成本**:
   - 每次生成思维导图会调用OpenAI API
   - 建议使用缓存机制避免重复生成

3. **处理时间**:
   - 小型PDF（<5页）: 约10-15秒
   - 中型PDF（5-20页）: 约20-30秒
   - 大型PDF（>20页）: 约30-60秒

4. **语言支持**:
   - 目前支持中文（zh）和英文（en）
   - 可以根据需要扩展其他语言

## 未来改进

- [ ] 支持思维导图的编辑和保存
- [ ] 添加思维导图导出功能（PNG、SVG、PDF）
- [ ] 支持多个论文的对比分析
- [ ] 添加思维导图的分享功能
- [ ] 优化AI提示词，提高分析质量
- [ ] 添加缓存机制，避免重复分析
- [ ] 支持自定义思维导图样式

## 故障排查

### 问题1: 思维导图生成失败
- 检查OpenAI API Key是否正确配置
- 检查网络连接是否正常
- 查看后端日志获取详细错误信息

### 问题2: PDF无法加载
- 确认PDF文件已成功上传到MinIO
- 检查MinIO服务是否正常运行
- 确认object_name是否正确

### 问题3: 思维导图显示异常
- 清除浏览器缓存
- 确认前端依赖已正确安装
- 检查浏览器控制台是否有错误信息

## 联系支持

如有问题或建议，请提交Issue或联系开发团队。

