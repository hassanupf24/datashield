#!/bin/bash
# ============================================================
# DATASHIELD Deployment Script
# Builds and launches all services via Docker Compose
# ============================================================
set -e

echo "╔══════════════════════════════════════════════╗"
echo "║    DATASHIELD - Enterprise Data Governance    ║"
echo "║           Deployment Script v1.0              ║"
echo "╚══════════════════════════════════════════════╝"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required"; exit 1; }

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with production secrets before deploying!"
fi

# Build and start
echo ""
echo "🔨 Building all services..."
docker compose build --no-cache

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

echo ""
echo "🌱 Seeding database..."
docker compose exec backend python seed.py

echo ""
echo "✅ DATASHIELD is running!"
echo ""
echo "📡 Services:"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Frontend:     http://localhost:3000"
echo "   PostgreSQL:   localhost:5432"
echo "   Redis:        localhost:6379"
echo ""
echo "🔐 Default Login:"
echo "   Username: admin"
echo "   Password: DataShield@2026"
echo ""
echo "📖 Run 'docker compose logs -f' to view logs"
