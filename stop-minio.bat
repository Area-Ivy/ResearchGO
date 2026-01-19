@echo off
echo ========================================
echo   ResearchGO MinIO 停止脚本
echo ========================================
echo.

echo [1/2] 停止 MinIO 服务...
docker-compose down

if errorlevel 1 (
    echo [错误] 停止失败
    pause
    exit /b 1
)

echo.
echo [2/2] 检查状态...
docker-compose ps

echo.
echo ========================================
echo   MinIO 已停止
echo ========================================
echo.
echo 数据已保存在 minio_data 目录中
echo 下次启动时数据仍会保留
echo.
echo 如需完全删除（包括数据）:
echo   docker-compose down -v
echo   rmdir /s /q minio_data
echo.
pause

