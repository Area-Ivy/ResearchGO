@echo off
echo ========================================
echo Starting ResearchGO Frontend
echo ========================================
echo.

cd frontend

if not exist node_modules (
    echo Installing dependencies...
    call npm install
    echo.
)

echo Starting frontend development server...
echo Frontend will be available at: http://localhost:5173
echo.
call npm run dev

