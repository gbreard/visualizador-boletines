@echo off
echo ========================================
echo   SINCRONIZACION A PRODUCCION
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    pause
    exit /b 1
)

REM Ejecutar script de sincronización
python sincronizar_a_produccion.py %*

echo.
echo Presiona cualquier tecla para salir...
pause >nul