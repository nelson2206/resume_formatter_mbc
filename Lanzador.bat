@echo off
setlocal EnableDelayedExpansion
title Staffing AI Builder — Lanzador
color 0B

echo.
echo  ========================================================
echo    Staffing AI Builder v2 — Lanzador Automatico
echo  ========================================================
echo.

:: ── PASO 1: Python ────────────────────────────────────────────────
echo  [1/4] Comprobando Python 3.11...
py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [!] Python 3.11 no fue detectado.
    echo      Intentando instalar via Winget...
    winget install Python.Python.3.11 -e --accept-package-agreements --accept-source-agreements --silent
    echo.
    echo  ============================================================
    echo   Python instalado. CIERRA esta ventana y vuelve a ejecutar.
    echo  ============================================================
    pause
    exit
) else (
    for /f "tokens=*" %%V in ('py -3.11 --version 2^>^&1') do echo  [OK] %%V
)

:: ── PASO 2: Node.js ───────────────────────────────────────────────
echo.
echo  [2/4] Comprobando Node.js...
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [!] Node.js no detectado.
    echo      Intentando instalar via Winget...
    winget install OpenJS.NodeJS -e --accept-package-agreements --accept-source-agreements --silent
    echo.
    echo  ============================================================
    echo   Node.js instalado. CIERRA esta ventana y vuelve a ejecutar.
    echo  ============================================================
    pause
    exit
) else (
    for /f "tokens=*" %%V in ('node -v 2^>^&1') do echo  [OK] Node.js %%V
)

:: ── PASO 3: Dependencias ──────────────────────────────────────────
echo.
echo  [3/4] Instalando dependencias (solo la primera vez)...

echo      Instalando paquetes Python...
cd /d "%~dp0backend"
py -3.11 -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Falló la instalación de paquetes Python.
    echo          Revisa tu conexión a internet y vuelve a intentarlo.
    pause
    exit
)

echo      Instalando paquetes Node (frontend)...
cd /d "%~dp0frontend"
call npm install --silent
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Falló la instalación de paquetes Node.
    echo          Revisa tu conexión a internet y vuelve a intentarlo.
    pause
    exit
)
cd /d "%~dp0"

:: ── PASO 4: Levantar servicios ────────────────────────────────────
echo.
echo  [4/4] Iniciando servicios...

echo      Levantando Backend IA (Puerto 8000)...
cd /d "%~dp0backend"
start "Backend-StaffingAI" cmd /c "title ^| Motor Backend AI ^| && color 0A && py -3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
cd /d "%~dp0"

echo      Levantando Frontend (Puerto 5173)...
cd /d "%~dp0frontend"
start "Frontend-StaffingAI" cmd /c "title ^| Plataforma Web ^| && color 09 && npm run dev"
cd /d "%~dp0"

:: ── Esperar y abrir navegador ─────────────────────────────────────
echo.
echo  Esperando que los servicios arranquen...
timeout /t 5 >nul

:: Abrir browser
echo  Abriendo aplicacion en el navegador...
start http://localhost:5173/

echo.
echo  ========================================================
echo   TODO LISTO. La app esta corriendo en:
echo   http://localhost:5173/
echo.
echo   Para apagar: cierra las ventanas negras del backend
echo   y del frontend que se abrieron.
echo  ========================================================
echo.
pause
