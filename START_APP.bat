@echo off
color 0b
title OmniUSB Director - Bootloader

if "%~1"=="KEEP_OPEN" goto :main
cmd /k ""%~f0" KEEP_OPEN"
exit /b

:main
echo =======================================
echo Iniciando Sistema... Por favor, Espera.
echo =======================================

:: AUTO-CONFIGURAR GIT SI ES UNA PC NUEVA O ZIP DESCARGADO
where git >nul 2>&1
if not errorlevel 1 (
    git remote get-url origin >nul 2>&1
    if errorlevel 1 (
        echo [!] Inicializando Git para permitir actualizaciones online...
        if exist ".git" rmdir /s /q ".git"
        git init
        git remote add origin https://github.com/mrpoeta2018/omniusb-farm-manager.git
        git fetch origin
        git branch -M main
        git checkout -f main
        echo [OK] Git configurado correctamente.
        echo.
    )
)

set MEMORY_FILE=install_path.txt

:: Adaptador de Migracion Automatica
if exist %MEMORY_FILE% (
    set /p SAVED_PATH=<%MEMORY_FILE%
) else (
    set SAVED_PATH=NONE
)

:: Entorno conservado para arranque rápido
:: if exist venv (
::     echo [-] Borrando entorno corrupto...
::     rmdir /s /q venv
:: )
:: if exist node_modules (
::     rmdir /s /q node_modules
:: )
if exist %MEMORY_FILE% del /q %MEMORY_FILE%
echo %CD%>%MEMORY_FILE%

echo.
echo [1/3] Chequeando Python...

:: -- Buscar Python dinamicamente --
set PYTHON=

python --version >nul 2>&1
if not errorlevel 1 ( set "PYTHON=python" & goto :python_ok )

for %%V in (313 312 311 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :python_ok
    )
)
for %%V in (313 312 311 310 39 38) do (
    if exist "C:\Python%%V\python.exe" (
        set "PYTHON=C:\Python%%V\python.exe"
        goto :python_ok
    )
)

echo [!] Python NO encontrado. Iniciando descarga automatica (Python 3.11)...
curl -L -o python-installer.exe https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe
if not exist python-installer.exe (
    echo [X] Error descargando Python. Por favor verifica tu conexion a internet.
    pause
    exit /b
)
echo [+] Descarga completada. Instalando de forma silenciosa (puede tardar un par de minutos)...
python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del python-installer.exe
echo [+] Instalacion completada!
set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

:python_ok
"%PYTHON%" --version
echo [+] Python OK

echo.
echo [2/3] Construyendo Entorno...
if not exist venv (
    "%PYTHON%" -m venv venv
)
call venv\Scripts\activate.bat

echo.
echo [3/3] Chequeando Dependencias...

if exist "node_portable" (
    set "PATH=%CD%\node_portable;%PATH%"
)

pip install -r requirements.txt
python auto_repair.py

echo.
echo.
echo [+] Abriendo OmniUSB...

:loop
python app.py
echo.
echo [!] El programa se ha cerrado o actualizado. Reiniciando en 2 segundos...
timeout /t 2 >nul
goto loop
