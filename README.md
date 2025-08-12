# Visualizador de Empleo Argentina - Versión Producción

Dashboard interactivo para análisis de datos de empleo trimestral de Argentina (SIPA).

## 🚀 Instrucciones de Deployment

### Opción 1: Render.com (RECOMENDADO - GRATIS)

1. **Crear cuenta en Render**:
   - Ve a [render.com](https://render.com) y crea una cuenta gratuita

2. **Subir el código a GitHub**:
   ```bash
   # En la carpeta 'produccion'
   git init
   git add .
   git commit -m "Initial deployment"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/visualizador-empleo.git
   git push -u origin main
   ```

3. **Conectar con Render**:
   - En Render, click en "New +" → "Web Service"
   - Conecta tu cuenta de GitHub
   - Selecciona el repositorio
   - Render detectará automáticamente el archivo `render.yaml`
   - Click en "Create Web Service"

4. **Esperar el deployment** (5-10 minutos)

5. **Tu app estará en**: `https://visualizador-empleo-argentina.onrender.com`

### Opción 2: Railway.app (También gratuito)

1. Ve a [railway.app](https://railway.app)
2. Click en "Start a New Project"
3. Selecciona "Deploy from GitHub repo"
4. Conecta tu repositorio
5. Railway detectará Python automáticamente
6. Click en "Deploy"

### Opción 3: Heroku (Gratis con límites)

1. Crear archivo `Procfile`:
   ```
   web: gunicorn dashboard:server
   ```

2. Crear archivo `runtime.txt`:
   ```
   python-3.11.0
   ```

3. Deploy con Heroku CLI:
   ```bash
   heroku create visualizador-empleo
   git push heroku main
   ```

### Opción 4: PythonAnywhere (Gratis con límites)

1. Crear cuenta en [pythonanywhere.com](https://www.pythonanywhere.com)
2. Subir archivos via dashboard
3. Configurar WSGI
4. Reload app

## 📁 Estructura de Archivos

```
produccion/
├── dashboard.py          # Aplicación principal
├── requirements.txt      # Dependencias Python
├── render.yaml          # Config para Render
├── .gitignore          # Archivos a ignorar
├── README.md           # Este archivo
└── datos_limpios/      # Datos procesados
    ├── C1.1.csv
    ├── C1.2.csv
    ├── C2.1.csv
    ├── C2.2.csv
    ├── C3.csv
    ├── C4.csv
    ├── C5.csv
    ├── C6.csv
    ├── C7.csv
    └── descriptores_CIIU.csv
```

## 🔧 Configuración Local para Pruebas

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar localmente
python dashboard.py --debug

# O con gunicorn (como en producción)
gunicorn dashboard:server
```

## 📊 Características del Dashboard

- 7 vistas interactivas de análisis
- Datos de empleo 1996-2024
- Análisis por sectores CIIU
- Sistema de alertas automáticas
- Metodología completa incluida
- Exportación de datos

## ⚙️ Variables de Entorno (Opcional)

Si necesitas configurar algo específico:

```bash
PORT=8050  # Puerto (Render lo asigna automáticamente)
```

## 🆘 Troubleshooting

### Error: "Module not found"
- Verificar que todas las dependencias estén en `requirements.txt`

### Error: "Port already in use"
- Render asigna el puerto automáticamente, no hardcodear

### Dashboard no carga
- Verificar que todos los archivos CSV estén en `datos_limpios/`
- Revisar logs en el panel de Render

## 📝 Notas Importantes

1. **Render.com**: 
   - Plan gratuito: 750 horas/mes
   - Se suspende después de 15 min de inactividad
   - Primera carga puede tardar 30 segundos

2. **Datos**: 
   - Los CSVs están incluidos (no requiere BD)
   - Total: ~10MB de datos

3. **Performance**:
   - Dashboard optimizado con caché
   - Carga inicial: 5-10 segundos
   - Navegación: instantánea

## 🔗 Links Útiles

- [Render Docs](https://render.com/docs)
- [Dash Deployment](https://dash.plotly.com/deployment)
- [Gunicorn Config](https://docs.gunicorn.org/en/stable/configure.html)

---

**Desarrollado para el Ministerio de Trabajo, Empleo y Seguridad Social**
*Datos: Sistema Integrado Previsional Argentino (SIPA)*