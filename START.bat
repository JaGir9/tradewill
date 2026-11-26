@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  call INSTALL.bat
  if errorlevel 1 exit /b 1
)
echo Open http://127.0.0.1:8000 after server starts.
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
