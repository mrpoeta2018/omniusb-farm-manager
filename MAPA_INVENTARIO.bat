@echo off
cd /d "%~dp0"
echo Abriendo Mapa del Inventario...
call venv\Scripts\activate.bat
python inventory_tool.py
