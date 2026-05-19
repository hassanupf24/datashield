@echo off
REM ============================================================
REM DATASHIELD Deployment Script (Windows)
REM ============================================================

echo ========================================
echo   DATASHIELD - Enterprise Data Governance
echo   Deployment Script v1.0
echo ========================================

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is required
    exit /b 1
)

REM Create .env if not exists
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo WARNING: Update .env with production secrets!
)

echo.
echo Building all services...
docker compose build --no-cache

echo.
echo Starting services...
docker compose up -d

echo.
echo Waiting for PostgreSQL...
timeout /t 10 /nobreak

echo.
echo Seeding database...
docker compose exec backend python seed.py

echo.
echo ========================================
echo   DATASHIELD is running!
echo ========================================
echo.
echo   Backend API:  http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo   Frontend:     http://localhost:3000
echo.
echo   Default Login:
echo     Username: admin
echo     Password: DataShield@2026
echo.
echo   Run: docker compose logs -f
echo ========================================
