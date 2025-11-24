#!/bin/bash
# Quick Start Script for Procure-to-Pay System

echo "🚀 Starting Procure-to-Pay System Setup..."
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.11+ first."
    exit 1
fi

echo "✓ Python found: $(python --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    if [ -f "env.example.txt" ]; then
        cp env.example.txt .env
        echo "⚠️  Please edit .env file with your configuration (especially OPENAI_API_KEY)"
    else
        echo "⚠️  No env.example.txt found. Please create .env file manually."
    fi
fi

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create test users
echo "👥 Creating test users..."
python manage.py create_test_users

# Create test data
echo "📊 Creating test data..."
python manage.py create_test_data

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit .env file with your OpenAI API key"
echo "2. Start the development server: python manage.py runserver"
echo "3. Access the API at: http://localhost:8000/api/v1/"
echo "4. Access API docs at: http://localhost:8000/api/docs/"
echo "5. Login with test credentials (see README.md)"
echo ""
echo "Test Users:"
echo "- Staff: staff1 / staff123"
echo "- L1 Approver: approver_l1 / approver123"
echo "- L2 Approver: approver_l2 / approver123"
echo "- Finance: finance / finance123"
echo "- Admin: admin / admin123"
echo ""




