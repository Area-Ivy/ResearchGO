@echo off
echo ========================================
echo Starting ResearchGO Backend Server
echo ========================================
echo.

cd backend

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate
echo.

if not exist .env (
    echo WARNING: .env file not found!
    echo Please create backend\.env with your OPENAI_API_KEY
    echo.
    echo Example:
    echo OPENAI_API_KEY=your_key_here
    echo OPENAI_MODEL=gpt-4o
    echo HOST=0.0.0.0
    echo PORT=8000
    echo ALLOWED_ORIGINS=http://localhost:5173
    echo.
    pause
    exit /b 1
)

echo Installing/Updating dependencies...
pip install -r requirements.txt
echo.

echo Starting backend server...
echo Backend will be available at: http://localhost:8000
echo API documentation: http://localhost:8000/docs
echo.
python run.py

