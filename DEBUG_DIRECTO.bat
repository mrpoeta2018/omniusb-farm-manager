@echo off
echo ========================================
echo   DIAGNOSTICO DE EMERGENCIA OMNIUSB
echo ========================================
echo [*] Borrando registros previos...
if exist DEBUG_TOTAL.txt del /q DEBUG_TOTAL.txt

echo [*] Ejecutando test con log...
:: Intentar correr python directamente y guardar todo el error en el archivo
python app.py > DEBUG_TOTAL.txt 2>&1

echo [*] Test finalizado. 
if exist DEBUG_TOTAL.txt (
    echo [!] Se ha generado el archivo DEBUG_TOTAL.txt
    echo [!] Por favor, abre ese archivo y dime que dice.
) else (
    echo [X] No se pudo generar ni siquiera el log. El sistema esta bloqueando a Python.
)
pause
