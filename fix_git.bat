@echo off
echo Solucionando problema de Git...

REM Verificar estado actual
git status

REM Verificar que rama existe
git branch

REM Crear y cambiar a rama main si no existe
git checkout -b main

REM Verificar remoto
git remote -v

REM Si no hay remoto, agregarlo
git remote remove origin
git remote add origin https://github.com/gbreard/visualizador-boletines.git

REM Agregar todos los archivos si no están agregados
git add .

REM Hacer commit si es necesario
git commit -m "Dashboard v2.0 - Visualizador interactivo de empleo Argentina" --allow-empty

REM Ahora sí hacer push forzado
git push -u --force origin main

echo.
echo Listo! Tu codigo debe estar en GitHub ahora.
echo Revisa: https://github.com/gbreard/visualizador-boletines
pause