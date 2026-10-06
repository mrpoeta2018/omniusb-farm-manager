@echo off
color 0B
title Instalador OmniUSB Piloto Automatico

echo ===================================================
echo     INSTALADOR OMNIUSB - PILOTO AUTOMATICO V2
echo ===================================================
echo.

echo [*] Verificando si Python esta instalado en la PC...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [!] ERROR CRITICO: Python NO esta instalado o no esta en el PATH.
    echo.
    echo Para que esta granja funcione, DEBES instalar Python.
    echo 1. Se abrira la pagina web oficial de Python ahora mismo.
    echo 2. Descarga la ultima version para Windows.
    echo 3. DURANTE LA INSTALACION, marca la casilla que dice:
    echo    "Add python.exe to PATH" (Esto es OBLIGATORIO).
    echo.
    echo Presiona cualquier tecla para abrir la web de Python y salir...
    pause >nul
    start https://www.python.org/downloads/
    exit /b
) else (
    echo [+] Python detectado correctamente.
)
echo.

echo [*] Paso 1: Instalando dependencias de la aplicacion...
pip install -r requirements.txt
echo.

echo [*] Paso 2: Creando acceso de Auto-Arranque en Windows...
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set VBS_PATH=%STARTUP_DIR%\ArrancaSupervisor.vbs
set CURRENT_DIR=%~dp0
set CURRENT_DIR=%CURRENT_DIR:~0,-1%

:: Generar el archivo VBS dinamicamente con la ruta actual
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.CurrentDirectory = "%CURRENT_DIR%"
echo WshShell.Run "python.exe app.py --auto", 1, False
) > "%VBS_PATH%"

echo [+] Archivo de Auto-Arranque creado en el sistema de esta PC.
echo.
echo ===================================================
echo   INSTALACION 100%% COMPLETADA. 
echo   La app arrancara sola la proxima vez que reinicies.
echo ===================================================
pause
