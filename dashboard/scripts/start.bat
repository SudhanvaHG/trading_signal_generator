@echo off
REM PropAlgo Dashboard — Windows Startup Script
cd /d "%~dp0.."

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║         PropAlgo Trading Dashboard — Startup        ║
echo ╚══════════════════════════════════════════════════════╝
echo.

if not exist ".env" (
    echo Warning: .env not found. Copying from .env.example...
    copy .env.example .env
    echo Done. Edit .env with your credentials, then re-run.
    pause
    exit /b 1
)

echo Building and starting containers...
docker compose up -d --build

echo.
echo Waiting for services...
timeout /t 15 /nobreak >nul

echo Checking health...
curl -sf http://localhost:80/health >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ✅  Dashboard:  http://localhost:80
    echo ✅  API Docs:   http://localhost:80/api/docs
    echo ✅  WebSocket:  ws://localhost:80/ws
    echo.
) else (
    echo ⚠️  Service may still be starting. Check: docker compose logs
)
pause
