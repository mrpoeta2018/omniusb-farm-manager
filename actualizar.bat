@echo off
color 0A
echo ========================================================
echo     ACTUALIZADOR AUTOMATICO - OMNIUSB FARM MANAGER
echo ========================================================
echo.
echo Descargando la ultima version desde GitHub...
echo.
git fetch origin main
git reset --hard origin/main
git pull origin main
echo.
echo ========================================================
echo     ACTUALIZACION COMPLETADA CON EXITO
echo ========================================================
pause
