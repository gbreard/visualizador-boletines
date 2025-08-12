# 📋 Instrucciones para actualizar tu repositorio GitHub

## Opción A: Limpiar y actualizar el repositorio existente (RECOMENDADO)

Abre una terminal/cmd y ejecuta estos comandos **DESDE LA CARPETA PRODUCCION**:

```bash
# 1. Ir a la carpeta de producción
cd "C:\Users\gbrea\OneDrive\Documentos\Aplicacion PY\Visualizador_boletines\produccion"

# 2. Inicializar git si no está inicializado
git init

# 3. Agregar tu repositorio remoto existente
git remote add origin https://github.com/gbreard/visualizador-boletines.git

# 4. Descargar el estado actual del repositorio
git fetch origin

# 5. Resetear a main (esto permitirá sobrescribir todo)
git checkout -b main

# 6. Agregar todos los archivos nuevos
git add .

# 7. Hacer commit con los nuevos archivos
git commit -m "Nueva versión: Dashboard interactivo de empleo con 7 vistas y sistema de alertas"

# 8. Forzar el push (esto REEMPLAZARÁ todo lo que hay en GitHub)
git push --force origin main
```

## Opción B: Si prefieres mantener el historial

```bash
# 1. Clonar el repositorio existente en una carpeta temporal
cd C:\Users\gbrea\OneDrive\Documentos\Aplicacion PY\
git clone https://github.com/gbreard/visualizador-boletines.git temp_repo

# 2. Entrar a la carpeta clonada
cd temp_repo

# 3. Eliminar todos los archivos antiguos (excepto .git)
# En Windows PowerShell:
Get-ChildItem -Path . -Exclude .git | Remove-Item -Recurse -Force

# 4. Copiar todos los archivos nuevos de producción
# En Windows:
xcopy "..\Visualizador_boletines\produccion\*" . /E /Y

# 5. Agregar todos los cambios
git add .

# 6. Commit
git commit -m "Actualización completa: Dashboard v2.0 con análisis avanzado"

# 7. Push normal
git push origin main
```

## Opción C: Usando GitHub Desktop (Más visual)

1. Abre GitHub Desktop
2. Clona tu repositorio: `https://github.com/gbreard/visualizador-boletines`
3. Elimina todos los archivos de la carpeta (excepto la carpeta .git)
4. Copia todos los archivos de la carpeta `produccion` 
5. En GitHub Desktop verás todos los cambios
6. Escribe el mensaje de commit: "Dashboard v2.0 - Visualizador completo de empleo"
7. Click en "Commit to main"
8. Click en "Push origin"

## 🚀 Después de subir a GitHub

### Publicar en Render.com (GRATIS):

1. Ve a [render.com](https://render.com)
2. Inicia sesión (o crea cuenta)
3. Click en **"New +"** → **"Web Service"**
4. Conecta tu GitHub si no lo has hecho
5. Busca y selecciona: `visualizador-boletines`
6. Configuración:
   - **Name**: `visualizador-empleo-argentina` (o el que prefieras)
   - **Region**: `Oregon (US West)` (o la más cercana)
   - **Branch**: `main`
   - **Runtime**: `Python 3` (se detecta automáticamente)
   - **Build Command**: `pip install -r requirements.txt` (se detecta)
   - **Start Command**: `gunicorn dashboard:server` (se detecta)
7. Click en **"Create Web Service"**
8. Espera 5-10 minutos mientras se construye
9. ¡Tu app estará en `https://visualizador-empleo-argentina.onrender.com`!

## ⚠️ IMPORTANTE

- El comando `git push --force` REEMPLAZARÁ TODO lo que hay en GitHub
- Asegúrate de estar en la carpeta `produccion` antes de ejecutar los comandos
- Si hay algo importante en el repo actual, haz un backup primero

## 🔍 Verificar antes de subir

Asegúrate de que en la carpeta `produccion` tengas:
- ✅ dashboard.py
- ✅ requirements.txt
- ✅ render.yaml
- ✅ Procfile
- ✅ runtime.txt
- ✅ carpeta datos_limpios/ con todos los CSV
- ✅ README.md
- ✅ .gitignore

## 💡 Tips

- Si tienes problemas con git, puedes simplemente:
  1. Eliminar todo desde la web de GitHub (Settings → Delete files)
  2. Subir los archivos nuevos arrastrándolos a la web

- Render detecta automáticamente el archivo `render.yaml` y configura todo

- El dashboard tardará ~30 segundos en cargar la primera vez después de inactividad (plan gratuito)

## 🆘 Si algo sale mal

1. Verifica que estés en la carpeta correcta
2. Asegúrate de tener git instalado: `git --version`
3. Si no tienes git, descárgalo de: https://git-scm.com/download/win

---

**¡Tu dashboard estará online en menos de 15 minutos!** 🎉