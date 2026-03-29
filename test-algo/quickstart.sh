#!/bin/bash

# LunarAtlas Quick Start Script
# Sets up and runs the complete system

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       LunarAtlas Spectral Visualization System            ║"
echo "║       Quick Start Deployment Script                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/backend"

echo "Step 1: Starting Docker containers..."
echo "----------------------------------------"
docker-compose up -d

echo ""
echo "Step 2: Waiting for PostgreSQL to be ready..."
echo "----------------------------------------"
sleep 5

# Wait for PostgreSQL
until docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; do
    echo "  Waiting for database..."
    sleep 2
done

echo "✓ PostgreSQL is ready"
echo ""

echo "Step 3: Setting up database and loading data..."
echo "----------------------------------------"
docker-compose exec -T api python setup_database.py

echo ""
echo "Step 4: Running API tests..."
echo "----------------------------------------"
sleep 2
docker-compose exec -T api python test_api.py

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              DEPLOYMENT SUCCESSFUL ✓                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Services Running:"
echo "   • API:      http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Database: localhost:5432"
echo ""
echo "📝 Next Steps:"
echo ""
echo "   1. Test the API:"
echo "      curl http://localhost:8000/api/v1/observations"
echo ""
echo "   2. Start the frontend (in a new terminal):"
echo "      cd frontend"
echo "      npm install"
echo "      npm start"
echo ""
echo "   3. Open your browser:"
echo "      http://localhost:3000"
echo ""
echo "   4. View API documentation:"
echo "      http://localhost:8000/docs"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo ""
echo "📖 For more information, see README.md"
echo ""
