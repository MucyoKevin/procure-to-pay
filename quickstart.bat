@echo off
REM Quick Start Script for Procure-to-Pay System (Windows)

echo 🚀 Starting Procure-to-Pay System Setup...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    exit /b 1
)

echo ✓ Python found
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo ⚙️  Creating .env file from template...
    if exist "env.example.txt" (
        copy env.example.txt .env
        echo ⚠️  Please edit .env file with your configuration (especially OPENAI_API_KEY)
    ) else (
        echo ⚠️  No env.example.txt found. Please create .env file manually.
    )
)

REM Run migrations
echo 🗄️  Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create test users
echo 👥 Creating test users...
python manage.py create_test_users

REM Create test data
echo 📊 Creating test data...
python manage.py create_test_data

REM Collect static files
echo 📁 Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ✅ Setup complete!
echo.
echo 🎯 Next steps:
echo 1. Edit .env file with your OpenAI API key
echo 2. Start the development server: python manage.py runserver
echo 3. Access the API at: http://localhost:8000/api/v1/
echo 4. Access API docs at: http://localhost:8000/api/docs/
echo 5. Login with test credentials (see README.md)
echo.
echo Test Users:
echo - Staff: staff1 / staff123
echo - L1 Approver: approver_l1 / approver123
echo - L2 Approver: approver_l2 / approver123
echo - Finance: finance / finance123
echo - Admin: admin / admin123
echo.

pause




