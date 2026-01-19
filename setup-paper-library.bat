@echo off
echo ========================================
echo   文献库功能安装脚本
echo ========================================
echo.

echo [1/5] 检查 MinIO 状态...
docker-compose ps | findstr "researchgo-minio" >nul 2>&1
if errorlevel 1 (
    echo [警告] MinIO 未运行，正在启动...
    docker-compose up -d
    timeout /t 5 /nobreak >nul
) else (
    echo [完成] MinIO 正在运行
)

echo.
echo [2/5] 检查后端环境变量文件...
if not exist backend\.env (
    echo [提示] backend\.env 文件不存在，正在创建...
    (
        echo # OpenAI 配置
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo OPENAI_MODEL=gpt-4o
        echo.
        echo # OpenAlex 配置
        echo CONTACT_EMAIL=your_email@example.com
        echo.
        echo # 服务器配置
        echo HOST=0.0.0.0
        echo PORT=8000
        echo ALLOWED_ORIGINS=http://localhost:5173
        echo.
        echo # MinIO 配置
        echo MINIO_ENDPOINT=localhost:9000
        echo MINIO_ACCESS_KEY=minioadmin
        echo MINIO_SECRET_KEY=minioadmin123
        echo MINIO_BUCKET_NAME=research-papers
        echo MINIO_SECURE=False
    ) > backend\.env
    echo [完成] backend\.env 文件已创建
    echo [重要] 请编辑 backend\.env 文件，设置您的 OPENAI_API_KEY
) else (
    echo [完成] backend\.env 文件已存在
    echo [提示] 请确保已添加 MinIO 配置（参考 backend\.env.example）
)

echo.
echo [3/5] 激活 Python 虚拟环境...
if exist backend\.venv\Scripts\activate.bat (
    call backend\.venv\Scripts\activate.bat
    echo [完成] 虚拟环境已激活
) else (
    echo [警告] 虚拟环境不存在，请先创建：
    echo   cd backend
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
)

echo.
echo [4/5] 安装 Python 依赖...
cd backend
pip install -q minio==7.2.3 python-multipart==0.0.6
if errorlevel 1 (
    echo [错误] 依赖安装失败
    cd ..
    pause
    exit /b 1
)
echo [完成] MinIO SDK 和文件上传支持已安装
cd ..

echo.
echo [5/5] 验证安装...
echo 正在检查 MinIO 连接...
curl -s http://localhost:9000/minio/health/live >nul 2>&1
if errorlevel 1 (
    echo [警告] 无法连接到 MinIO，请检查服务状态
) else (
    echo [完成] MinIO 连接正常
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 下一步:
echo   1. 编辑 backend\.env 文件，设置 OPENAI_API_KEY
echo   2. 访问 http://localhost:9001 登录 MinIO 控制台
echo   3. 创建名为 'research-papers' 的存储桶
echo   4. 运行 start-backend.bat 启动后端服务
echo   5. 访问 http://localhost:8000/docs 测试 API
echo.
echo 详细文档:
echo   - MinIO 部署: MINIO_SETUP.md
echo   - 后端设置: backend\PAPER_LIBRARY_SETUP.md
echo.
pause

