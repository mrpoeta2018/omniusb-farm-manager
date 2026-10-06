@echo off
setlocal
echo Instalando arranque automatico del Agente Supervisor...
set "VBS_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ArrancaSupervisor.vbs"
set "SUPERVISOR_DIR=%~dp0"
set "SUPERVISOR_DIR=%SUPERVISOR_DIR:~0,-1%"

echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_PATH%"
echo WshShell.CurrentDirectory = "%SUPERVISOR_DIR%" >> "%VBS_PATH%"
echo WshShell.Run "pythonw.exe supervisor_bot.py", 0, False >> "%VBS_PATH%"

echo.
echo =========================================================
echo INSTALACION COMPLETADA CON EXITO
echo El Agente Supervisor se iniciara oculto en esta PC
echo cada vez que Windows encienda.
echo =========================================================
echo.
pause
