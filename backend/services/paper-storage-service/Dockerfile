FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（pdfplumber 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpoppler-cpp-dev \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8003

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
