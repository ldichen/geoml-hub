#!/bin/bash
# setup.sh - Environment setup script

echo "🚀 Setting up GeoML-Hub development environment..."

# Check for required tools
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 not installed"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not installed"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not installed"; exit 1; }

# Set up backend environment
echo "📦 Setting up backend environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Set up frontend environment
echo "🎨 Setting up frontend environment..."
cd ../frontend
npm install
echo "✅ Frontend dependencies installed"

# Start databases
echo "🗄️ Starting databases..."
cd ..
docker-compose up -d postgres redis
echo "✅ Databases started"

# Database migration
echo "📊 Running database migrations..."
cd backend
source venv/bin/activate
alembic upgrade head
python scripts/init_data.py
echo "✅ Database initialized"

echo "🎉 Setup complete!"
echo "📝 Use these commands to start development servers:"
echo "   Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "   Frontend: cd frontend && npm run dev"