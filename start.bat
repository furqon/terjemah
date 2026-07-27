@echo off
REM ============================================
REM Penerjemah Kitab — Start Servers (Windows)
REM ============================================

echo === Penerjemah Kitab — Starting Servers ===
echo.

REM Kill any existing processes on our ports
echo Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing backend PID: %%a
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo Killing frontend PID: %%a
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 3 /nobreak >nul

REM Step 1: Start Backend (FastAPI)
echo.
echo [1/2] Starting Backend (FastAPI) on :8000...
cd /d "%~dp0backend"
start "PenerjemahKitab-Backend" cmd /c "python -X utf8 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
cd /d "%~dp0"
timeout /t 8 /nobreak >nul

REM Verify backend
curl -s --fail http://localhost:8000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend running on http://localhost:8000
    echo     API Docs: http://localhost:8000/docs
) else (
    echo [FAIL] Backend failed to start
)

REM Step 2: Start Frontend (Nuxt)
echo.
echo [2/2] Starting Frontend (Nuxt) on :3000...
cd /d "%~dp0frontend"
start "PenerjemahKitab-Frontend" cmd /c "npx nuxt dev --port 3000 --host 0.0.0.0"
cd /d "%~dp0"
timeout /t 15 /nobreak >nul

REM Verify frontend
curl -s --fail -o nul -w "%%{http_code}" http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend running on http://localhost:3000
) else (
    echo [INFO] Frontend may still be compiling... check the window
)

echo.
echo ============================================
echo  Open in browser: http://localhost:3000
echo  Backend API:     http://localhost:8000/docs
echo ============================================
echo.
echo Close the server windows to stop.
pause
