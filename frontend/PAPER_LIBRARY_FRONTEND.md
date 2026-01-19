# 文献库前端使用指南

## 一、功能概述

文献库（Paper Library）是一个完整的文献管理界面，支持：

✅ **上传论文** - 拖放或点击上传 PDF 文件  
✅ **查看列表** - 展示所有已上传的论文  
✅ **搜索过滤** - 快速查找特定论文  
✅ **下载文件** - 一键下载论文到本地  
✅ **删除文件** - 删除不需要的论文（带确认）  
✅ **响应式设计** - 支持桌面和移动设备  

## 二、访问页面

### 启动前端服务

```bash
cd frontend
npm run dev
```

### 访问文献库

打开浏览器访问：`http://localhost:5173/library`

或通过侧边栏导航：**Dashboard → Paper Library**

## 三、使用说明

### 3.1 上传论文

**方法 1：拖放上传**

1. 将 PDF 文件拖动到上传区域
2. 文件会自动开始上传
3. 上传完成后，列表会自动刷新

**方法 2：点击选择**

1. 点击上传区域
2. 在文件选择器中选择 PDF 文件
3. 确认选择，自动上传

**注意事项：**
- 仅支持 PDF 格式（`.pdf`）
- 上传时显示加载动画
- 上传成功/失败都有提示

### 3.2 查看论文列表

论文以卡片形式展示，每张卡片包含：

- 📄 **PDF 图标** - 文件类型标识
- 📝 **文件名** - 原始文件名
- 📊 **文件大小** - 自动格式化显示（KB/MB/GB）
- 🕐 **上传时间** - 相对时间（如 "2h ago"）
- 🔽 **下载按钮** - 绿色下载图标
- 🗑️ **删除按钮** - 红色删除图标

### 3.3 搜索论文

在页面右上角的搜索框中输入关键词：

- 实时搜索，无需点击按钮
- 按文件名匹配
- 不区分大小写
- 清空搜索框显示全部论文

### 3.4 下载论文

1. 找到要下载的论文
2. 点击绿色下载按钮（↓ 图标）
3. 文件会自动下载到浏览器默认下载位置
4. 文件名保持原始名称

### 3.5 删除论文

1. 找到要删除的论文
2. 点击红色删除按钮（🗑️ 图标）
3. 在确认对话框中核对文件名
4. 点击 "Delete" 确认删除
5. 删除成功后列表自动刷新

**安全提示：** 删除操作不可恢复，请谨慎操作！

### 3.6 刷新列表

点击右上角的刷新按钮（🔄 图标）手动刷新列表。

## 四、界面说明

### 页面布局

```
┌────────────────────────────────────────┐
│ Paper Library           [搜索框] [刷新] │  Header
├────────────────────────────────────────┤
│          📤 Upload PDF File            │  Upload Area
│      Drag and drop or click to select  │
├────────────────────────────────────────┤
│ Your Papers (12)                       │  Papers List
│ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│ │ 📄 PDF 1 │ │ 📄 PDF 2 │ │ 📄 PDF 3 ││
│ │ 2.5 MB   │ │ 5.1 MB   │ │ 1.8 MB   ││
│ │ 2h ago   │ │ 1d ago   │ │ 3d ago   ││
│ │ [📥] [🗑️] │ │ [📥] [🗑️] │ │ [📥] [🗑️] ││
│ └──────────┘ └──────────┘ └──────────┘│
└────────────────────────────────────────┘
```

### 视觉特点

- 🌌 **深色科技风** - 与整体风格一致
- ✨ **霓虹效果** - 按钮悬停时的发光效果
- 🎨 **渐变色** - 标题和按钮使用渐变色
- 💫 **动画效果** - 平滑的过渡和悬停动画
- 📱 **响应式** - 自适应各种屏幕尺寸

### 状态提示

**加载中：**
```
   ⚙️ Loading papers...
```

**空状态：**
```
   📚 No Papers Yet
   Upload your first PDF to get started
```

**无搜索结果：**
```
   🔍 No Results Found
   Try a different search term
```

**上传成功：**
```
✅ File uploaded successfully!
```

**上传失败：**
```
❌ Only PDF files are allowed
或
❌ Failed to upload file
```

## 五、快捷键

| 快捷键 | 功能 |
|--------|------|
| 点击上传区域 | 打开文件选择器 |
| 拖放文件到上传区域 | 上传文件 |
| ESC | 关闭删除确认对话框 |

## 六、技术特性

### 前端技术栈

- **Vue 3** - Composition API
- **Axios** - HTTP 请求
- **Vue Router** - 路由管理
- **Keep-Alive** - 组件缓存

### API 端点

所有 API 请求都通过 `frontend/src/api/papers.js` 统一管理：

```javascript
import { uploadPaper, listPapers, downloadPaper, deletePaper } from '../api/papers'
```

### 组件特性

- ✅ **响应式数据** - 实时更新
- ✅ **错误处理** - 友好的错误提示
- ✅ **加载状态** - 优雅的加载动画
- ✅ **确认对话框** - 防止误删除
- ✅ **文件验证** - 仅接受 PDF 文件

## 七、故障排查

### 问题 1：上传失败

**现象：** 显示 "Failed to upload file"

**可能原因：**
1. 后端服务未启动
2. MinIO 未运行
3. 文件不是 PDF 格式
4. 文件过大

**解决方案：**
```bash
# 1. 检查后端状态
curl http://localhost:8000/api/papers/health

# 2. 检查 MinIO 状态
docker-compose ps

# 3. 查看后端日志
cd backend
python run.py  # 查看控制台输出

# 4. 确认文件格式
# 文件必须以 .pdf 结尾
```

### 问题 2：无法显示列表

**现象：** 一直显示 "Loading papers..."

**可能原因：**
1. 后端 API 无响应
2. 网络连接问题
3. CORS 配置问题

**解决方案：**
```bash
# 1. 检查后端 API
curl http://localhost:8000/api/papers/list

# 2. 检查浏览器控制台
# F12 → Console → 查看错误信息

# 3. 检查网络请求
# F12 → Network → 查看 papers/list 请求
```

### 问题 3：下载失败

**现象：** 点击下载按钮无反应

**可能原因：**
1. 对象名称不正确
2. 文件已被删除
3. 浏览器阻止下载

**解决方案：**
1. 刷新页面重新加载列表
2. 检查浏览器下载设置
3. 查看浏览器控制台错误

### 问题 4：删除失败

**现象：** 删除后文件仍然存在

**可能原因：**
1. 后端删除失败
2. 列表未刷新

**解决方案：**
1. 手动点击刷新按钮
2. 检查后端日志
3. 刷新浏览器页面

## 八、开发说明

### 文件结构

```
frontend/src/
├── api/
│   └── papers.js              # API 客户端
├── views/
│   └── PaperLibrary.vue       # 主页面组件
├── router/
│   └── index.js               # 路由配置（已更新）
└── App.vue                    # 导航菜单（已更新）
```

### 自定义样式

所有样式都在 `PaperLibrary.vue` 的 `<style scoped>` 中定义。

主要 CSS 变量：
```css
--bg-primary: #0a0e27;
--bg-secondary: #131829;
--bg-card: rgba(26, 31, 58, 0.6);
--accent-primary: #667eea;
--accent-success: #00ff88;
--accent-danger: #ff6b9d;
--text-primary: #e8eaf6;
--text-secondary: #a5adc8;
```

### 添加新功能

要添加新功能（如批量操作、标签管理等）：

1. 在 `backend/app/api/papers.py` 添加新的 API 端点
2. 在 `frontend/src/api/papers.js` 添加对应的 API 调用
3. 在 `PaperLibrary.vue` 中添加 UI 和逻辑

## 九、性能优化

### 组件缓存

Paper Library 组件已加入 `keep-alive` 缓存：

```vue
<keep-alive :include="['Dashboard', 'Chat', 'Literature', 'PaperLibrary']">
  <component :is="Component" />
</keep-alive>
```

**效果：**
- 切换页面时保持状态
- 避免重复加载列表
- 保留搜索关键词

### 加载优化

- 使用异步组件懒加载
- 图标使用 SVG（无需加载图片）
- API 请求防抖（可选实现）

## 十、下一步增强

可以考虑添加的功能：

1. **批量操作**
   - 批量选择
   - 批量下载
   - 批量删除

2. **高级筛选**
   - 按日期筛选
   - 按大小筛选
   - 按标签分类

3. **PDF 预览**
   - 在线预览 PDF
   - 支持翻页

4. **文件管理**
   - 重命名文件
   - 添加标签/备注
   - 文件夹分类

5. **统计信息**
   - 总文件数
   - 总大小
   - 上传趋势图

## 十一、相关文档

- [后端 API 文档](../backend/PAPER_LIBRARY_SETUP.md)
- [MinIO 部署指南](../MINIO_SETUP.md)
- [Vue 3 文档](https://vuejs.org/)
- [Axios 文档](https://axios-http.com/)

---

## 快速测试

1. **启动服务：**
   ```bash
   # Terminal 1: 启动 MinIO
   docker-compose up -d

   # Terminal 2: 启动后端
   cd backend
   python run.py

   # Terminal 3: 启动前端
   cd frontend
   npm run dev
   ```

2. **访问页面：**
   http://localhost:5173/library

3. **测试上传：**
   拖放一个 PDF 文件到上传区域

4. **测试下载：**
   点击任意论文的下载按钮

5. **测试删除：**
   点击删除按钮并确认

**全功能已实现！尽情使用吧！** 🎉

