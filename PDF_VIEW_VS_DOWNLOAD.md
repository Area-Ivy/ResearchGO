# PDF 查看 vs 下载功能说明

## 问题描述

之前选择论文后，PDF会被下载到本地而不是在浏览器中显示。

## 问题原因

后端API使用了 `Content-Disposition: attachment`，这会告诉浏览器下载文件而不是显示文件。

## 解决方案

创建两个不同的端点：
1. **`/api/papers/view/{object_name}`** - 用于在线查看
2. **`/api/papers/download/{object_name}`** - 用于下载到本地

## Content-Disposition 详解

### inline（在线查看）
```python
headers={
    "Content-Disposition": f'inline; filename="{original_name}"'
}
```
- ✅ 浏览器会尝试在页面中显示文件
- ✅ 适合PDF、图片、视频等可预览的文件
- ✅ iframe可以正常加载和显示

### attachment（下载）
```python
headers={
    "Content-Disposition": f'attachment; filename="{original_name}"'
}
```
- ✅ 浏览器会下载文件到本地
- ✅ 用户可以保存到指定位置
- ✅ 适合需要下载的场景

## API端点对比

### 查看端点 `/api/papers/view/{object_name}`

**用途**: 在浏览器中在线查看PDF

**响应头**:
```
Content-Type: application/pdf
Content-Disposition: inline; filename="paper.pdf"
```

**使用场景**:
- 思维导图页面的PDF预览
- 快速浏览论文
- iframe嵌入显示

**前端使用**:
```javascript
pdfUrl.value = `${API_BASE_URL}/api/papers/view/${paper.object_name}`
```

### 下载端点 `/api/papers/download/{object_name}`

**用途**: 下载PDF到本地

**响应头**:
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="paper.pdf"
```

**使用场景**:
- 文献库的下载按钮
- 需要保存文件到本地
- 离线阅读

**前端使用**:
```javascript
// 在papers.js中已经使用
await downloadPaper(paper.object_name, paper.original_name)
```

## 修改的文件

### 后端
✅ `backend/app/api/papers.py`
- 新增 `view_paper()` 端点
- 保留 `download_paper()` 端点

### 前端
✅ `frontend/src/views/PaperMindmap.vue`
- 使用 `/api/papers/view/` 而不是 `/api/papers/download/`

## 使用方式

### 思维导图页面（在线查看）
```vue
<iframe :src="pdfUrl"></iframe>
```
```javascript
// 使用view端点
pdfUrl.value = `${API_BASE_URL}/api/papers/view/${paper.object_name}`
```

### 文献库页面（下载）
```javascript
// 使用download端点
await downloadPaper(paper.object_name, paper.original_name)
```

## 浏览器行为

### 使用 inline
1. 浏览器接收到PDF
2. 检测到 `Content-Disposition: inline`
3. 尝试在当前窗口/iframe中显示
4. 使用内置PDF阅读器渲染

### 使用 attachment
1. 浏览器接收到PDF
2. 检测到 `Content-Disposition: attachment`
3. 触发下载对话框
4. 文件保存到本地

## 测试步骤

### 测试在线查看
1. 进入思维导图页面 `/mindmap`
2. 点击"选择论文"
3. 选择一个PDF
4. **预期**: PDF在左侧iframe中显示
5. **不应该**: 触发下载

### 测试下载功能
1. 进入文献库页面 `/library`
2. 点击论文的下载按钮
3. **预期**: 触发下载，文件保存到本地
4. **不应该**: 在浏览器中显示

## 技术细节

### HTTP响应头对比

**在线查看响应**:
```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: inline; filename="paper.pdf"
Content-Length: 1234567
```

**下载响应**:
```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="paper.pdf"
Content-Length: 1234567
```

### iframe加载行为

当iframe的src指向返回 `inline` disposition的URL时：
1. ✅ 浏览器会在iframe中渲染PDF
2. ✅ 显示PDF阅读器控件
3. ✅ 允许滚动、缩放等操作

当iframe的src指向返回 `attachment` disposition的URL时：
1. ❌ 浏览器会触发下载
2. ❌ iframe中显示为空白或错误
3. ❌ 无法在线查看

## 兼容性

### inline支持
- ✅ Chrome: 完美支持
- ✅ Firefox: 完美支持
- ✅ Safari: 完美支持
- ✅ Edge: 完美支持

### attachment支持
- ✅ 所有现代浏览器都支持

## 最佳实践

### API设计
```python
# 查看 - 使用inline
@router.get("/view/{id}")
async def view_file(id: str):
    return StreamingResponse(
        file_data,
        headers={"Content-Disposition": "inline; filename=..."}
    )

# 下载 - 使用attachment
@router.get("/download/{id}")
async def download_file(id: str):
    return StreamingResponse(
        file_data,
        headers={"Content-Disposition": "attachment; filename=..."}
    )
```

### 前端使用
```javascript
// 在线查看
<iframe :src="`/api/papers/view/${id}`"></iframe>

// 下载
<a :href="`/api/papers/download/${id}`" download>下载</a>
```

## 优势

### 分离关注点
- ✅ 查看和下载是不同的用户需求
- ✅ 不同端点提供不同的Content-Disposition
- ✅ 更清晰的API语义

### 用户体验
- ✅ 思维导图页面：即时预览，无需下载
- ✅ 文献库页面：一键下载，保存本地
- ✅ 行为符合用户预期

### 性能
- ✅ 在线查看：无需下载完整文件即可开始浏览
- ✅ 下载：完整保存到本地供离线使用

## 总结

通过创建两个不同的端点（`/view/` 和 `/download/`），我们现在可以：
- ✅ 在思维导图页面在线查看PDF
- ✅ 在文献库页面下载PDF到本地
- ✅ 提供更好的用户体验
- ✅ 符合Web标准和最佳实践

现在选择论文后，PDF会直接在浏览器的iframe中显示，而不是下载到本地！

