#!/bin/bash

# Setup script for StockInformationWebsiteAIBackend

set -e

echo "🚀 Setting up StockInformationWebsiteAIBackend..."
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version || { echo "❌ Python 3 is required but not installed."; exit 1; }
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your OpenAI API key!"
    echo "   OPENAI_API_KEY=your_actual_api_key_here"
    echo ""
else
    echo "ℹ️  .env file already exists, skipping..."
    echo ""
fi

echo "✅ Setup complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Edit .env and add your OpenAI API key"
echo "   2. Activate the virtual environment: source venv/bin/activate"
echo "   3. Run the application: python main.py"
echo "   4. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "🎉 Happy coding!"
