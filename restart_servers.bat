@echo off
title Penerjemah Kitab — Restart Servers
echo ============================================
echo   Penerjemah Kitab — Restart Servers
echo ============================================
echo.

echo [1/4] Killing all old server processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
timeout /t 3 /nobreak >nul
echo   Done.
echo.

echo [2/4] Starting Backend (CAMeL Tools + post-processing)...
start "PenerjemahKitab-Backend" cmd /k "cd /d %~dp0backend && python -X utf8 -m uvicorn main:app --host 0.0.0.0 --port 8001"
echo   Backend window opened (title: PenerjemahKitab-Backend)
timeout /t 12 /nobreak >nul
echo.

echo [3/4] Starting Frontend...
start "PenerjemahKitab-Frontend" cmd /k "cd /d %~dp0frontend && set NUXT_PUBLIC_API_BASE=http://localhost:8001 && npx nuxt dev --port 3000 --host 0.0.0.0"
echo   Frontend window opened (title: PenerjemahKitab-Frontend)
timeout /t 15 /nobreak >nul
echo.

echo [4/4] Verifying servers...

REM Test backend
curl -s --fail http://localhost:8001/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Backend: http://localhost:8001
) else (
    echo   [FAIL] Backend not responding - check the backend window for errors
)

REM Test frontend
curl -s --fail http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Frontend: http://localhost:3000
) else (
    echo   [INFO] Frontend may still be compiling - wait a moment
)

echo.
echo ============================================
echo  Open http://localhost:3000 in your browser
echo  API docs: http://localhost:8001/docs
echo ============================================
echo.
echo If the greeting "السلام عليكم" still shows wrong output
echo (missing shadda), check the BACKEND window for errors.
echo.
pause
