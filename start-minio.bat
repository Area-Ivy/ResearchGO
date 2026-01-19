@echo off
echo ========================================
echo   ResearchGO MinIO 启动脚本
echo ========================================
echo.

REM 检查 Docker 是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

echo [1/4] 检查环境变量文件...
if not exist .env.minio (
    echo [提示] .env.minio 文件不存在，正在创建...
    (
        echo # MinIO 访问凭证
        echo MINIO_ROOT_USER=minioadmin
        echo MINIO_ROOT_PASSWORD=minioadmin123
        echo.
        echo # MinIO 连接配置（用于后端应用）
        echo MINIO_ENDPOINT=localhost:9000
        echo MINIO_ACCESS_KEY=minioadmin
        echo MINIO_SECRET_KEY=minioadmin123
        echo MINIO_BUCKET_NAME=research-papers
        echo MINIO_SECURE=false
    ) > .env.minio
    echo [完成] .env.minio 文件已创建
) else (
    echo [完成] .env.minio 文件已存在
)

echo.
echo [2/4] 启动 MinIO 服务...
docker-compose up -d

if errorlevel 1 (
    echo [错误] MinIO 启动失败
    pause
    exit /b 1
)

echo.
echo [3/4] 等待服务就绪...
timeout /t 3 /nobreak >nul

echo.
echo [4/4] 检查服务状态...
docker-compose ps

echo.
echo ========================================
echo   MinIO 启动完成！
echo ========================================
echo.
echo 访问地址:
echo   - MinIO 控制台: http://localhost:9001
echo   - MinIO API:    http://localhost:9000
echo.
echo 登录信息:
echo   - 用户名: minioadmin
echo   - 密码:   minioadmin123
echo.
echo 下一步:
echo   1. 在浏览器打开 http://localhost:9001
echo   2. 使用上述账号登录
echo   3. 创建名为 'research-papers' 的存储桶
echo.
echo 查看详细文档: MINIO_SETUP.md
echo ========================================
echo.
pause

