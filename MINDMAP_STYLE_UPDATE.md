# 思维导图页面风格更新

## 更新概述

已将文献思维导图页面的设计风格与其他页面（Paper Library、Literature Search）保持一致，采用统一的暗色主题和设计系统。

## 主要更改

### 1. 头部区域 (Header)
**之前**: 
- 简单的标题和按钮
- 白色背景，浅色边框

**之后**:
- 使用统一的 `page-title` 和 `page-subtitle` 样式
- 按钮添加图标，增强视觉识别
- 采用半透明背景和CSS变量系统

### 2. 按钮样式
**之前**:
- 扁平设计，纯色背景
- 简单的hover效果

**之后**:
- 渐变色背景 (Primary: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`)
- 发光效果 (`box-shadow: 0 0 30px rgba(102, 126, 234, 0.5)`)
- 图标 + 文字组合
- 统一的圆角 (`border-radius: 10px`)
- 更流畅的过渡动画

### 3. 模态框 (Modal)
**之前**:
- 白色背景
- 简单的阴影

**之后**:
- 毛玻璃效果 (`backdrop-filter: blur(20px)`)
- 暗色半透明背景 (`var(--bg-card)`)
- 发光边框 (`border: 1px solid var(--border-glow)`)
- 增强的阴影效果 (`var(--shadow-lg)`)

### 4. 论文列表卡片
**之前**:
- 浅色背景 (#f8f9fa)
- 文本图标 (📄)

**之后**:
- 半透明暗色背景 (`rgba(255, 255, 255, 0.03)`)
- SVG图标在彩色圆角容器中
- 发光hover效果
- 更好的文字层级和间距

### 5. 内容面板
**之前**:
- 纯白色背景
- 浅灰色分隔线

**之后**:
- 半透明暗色背景
- PDF阅读器区域：深色背景 (`rgba(0, 0, 0, 0.2)`)
- 思维导图区域：浅色暗背景 (`rgba(0, 0, 0, 0.1)`)
- 统一的边框和圆角

### 6. 加载和空状态
**之前**:
- 简单的文字提示
- Emoji图标

**之后**:
- 动画加载指示器（旋转圆圈）
- SVG图标系统
- 结构化的标题和描述
- 更好的视觉层次

### 7. PDF控制栏
**之前**:
- 白色背景
- 简单边框

**之后**:
- 毛玻璃效果
- 暗色半透明背景
- 发光边框
- 更现代的外观

### 8. 思维导图样式
**新增**:
- 自定义节点样式 (`:deep(.markmap-foreign)`)
- 毛玻璃效果的节点
- hover发光效果
- 与整体主题一致的配色

## CSS变量系统

现在使用统一的CSS变量：

```css
var(--bg-primary)       // 主背景色
var(--bg-secondary)     // 次要背景色
var(--bg-card)          // 卡片背景色
var(--text-primary)     // 主文字颜色
var(--text-secondary)   // 次要文字颜色
var(--text-tertiary)    // 三级文字颜色
var(--accent-primary)   // 主强调色 (#667eea)
var(--accent-success)   // 成功色 (绿色)
var(--accent-danger)    // 危险色 (红色)
var(--border-primary)   // 主边框颜色
var(--border-glow)      // 发光边框颜色
var(--glow-primary)     // 发光效果
var(--shadow-lg)        // 大阴影
```

## 视觉特效

### 1. 渐变色
- 按钮: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- 危险按钮: `linear-gradient(135deg, #ff6b9d 0%, #c44569 100%)`

### 2. 发光效果
```css
box-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
```

### 3. 毛玻璃效果
```css
backdrop-filter: blur(20px);
background: var(--bg-card);
```

### 4. 动画
- 按钮hover: `transform: translateY(-2px)`
- 加载指示器: 旋转动画
- 卡片hover: 轻微上移和发光

## 响应式设计

### 桌面 (> 1200px)
- 左右分屏布局
- 完整的侧边栏

### 平板 (768px - 1200px)
- 上下布局
- 每个面板固定高度

### 移动 (< 768px)
- 垂直堆叠
- 按钮全宽
- 优化的间距和字体大小

## 兼容性

所有样式与现有页面完全兼容：
- ✅ Paper Library
- ✅ Literature Search  
- ✅ Chat
- ✅ Dashboard

## 用户体验改进

1. **视觉一致性**: 所有页面使用相同的设计语言
2. **更好的反馈**: hover、active状态的视觉反馈更明显
3. **清晰的层次**: 通过颜色、大小、间距建立清晰的信息层次
4. **现代感**: 毛玻璃、发光、渐变等现代设计元素
5. **可访问性**: 保持良好的对比度和可读性

## 文件修改

- ✅ `frontend/src/views/PaperMindmap.vue` - 完全重写CSS样式
- ✅ `frontend/src/api/mindmap.js` - 修复导入错误
- ✅ 所有文本改为英文，与其他页面保持一致

## 测试建议

1. 在不同屏幕尺寸下测试响应式布局
2. 测试所有按钮的hover和点击效果
3. 验证模态框的打开/关闭动画
4. 检查思维导图的渲染和交互
5. 测试加载状态和空状态的显示

## 后续优化建议

1. 添加页面过渡动画
2. 优化移动端的触摸交互
3. 添加键盘快捷键支持
4. 实现暗色/亮色主题切换
5. 添加更多的微交互动画

