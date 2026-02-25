# Flujo de Desarrollo

Workflow de desarrollo local a produccion en Render.

## Entorno Local

### Setup inicial

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar sin BD (modo desarrollo)

```bash
python src/app.py
```

Dashboard corre en http://localhost:8050 con acceso admin publico. Ideal para desarrollo de visualizaciones.

### Ejecutar con BD local

```bash
# Opcion 1: PostgreSQL local
export DATABASE_URL=postgresql://user:pass@localhost/dbname

# Opcion 2: Conectar a BD remota (Render)
export DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require

# Inicializar BD (primera vez)
python scripts/init_db.py

# Arrancar
python src/app.py
```

## Actualizar Datos

Cuando hay nuevas publicaciones de datos del OEDE:

```bash
# 1. Descargar archivos fuente
python scripts/download_oede.py --all

# 2. Preprocesar (genera CSV + Parquet)
python scripts/preprocess/empleo_trimestral.py
python scripts/preprocess/remuneraciones_mes.py
python scripts/preprocess/empresas.py
python scripts/preprocess/flujos.py
python scripts/preprocess/genero.py
python scripts/preprocess/ipc.py

# 3. Verificar que el dashboard muestra los nuevos datos
python src/app.py
```

Los archivos procesados en `data/processed/` y `data/optimized/` estan en git, asi que al commitear se actualizan en produccion.

## Hacer Cambios de Codigo

### Donde va cada cosa

| Quiero... | Archivo/modulo |
|-----------|---------------|
| Agregar una tab nueva | `src/tabs/nueva.py` + registrar en `src/callbacks/register.py` + agregar en `src/layout/main.py` |
| Modificar una visualizacion | `src/tabs/<tab>.py` (layout y callbacks en el mismo archivo) |
| Cambiar estilos | `assets/custom.css` |
| Agregar un dataset | `src/data/loader.py` + procesador en `scripts/preprocess/` |
| Modificar autenticacion | `src/auth/` |
| Cambiar componentes UI | `src/layout/components.py` o `feedback_components.py` |
| Agregar feedback a componente | Usar `graph_with_feedback()` de `src/layout/feedback_components.py` |

### Estructura de una tab

Cada archivo en `src/tabs/` sigue el patron:

```python
# src/tabs/mi_tab.py

def create_mi_tab_layout():
    """Retorna el layout Dash de la tab."""
    return html.Div([...])

def register_mi_tab_callbacks(app):
    """Registra los callbacks interactivos."""
    @app.callback(Output(...), Input(...))
    def update_grafico(...):
        data = cache.get_ref('dataset_key')
        fig = px.line(data, ...)
        return fig
```

## Testing

```bash
# Ejecutar todos los tests
pytest tests/

# Ejecutar un test especifico
pytest tests/test_processing.py -v
```

Tests disponibles:
- `test_processing.py` — Parseo de periodos y calculos de variaciones
- `test_cache.py` — Singleton DataCache
- `test_loader.py` — Carga de datos
- `test_ingestion.py` — Ingesta a BD
- `test_tabs.py` — Smoke tests de todas las tabs

## Deploy a Produccion

### Flujo normal

```bash
# 1. Commitear cambios
git add <archivos>
git commit -m "Descripcion del cambio"

# 2. Push a main (dispara auto-deploy en Render)
git push origin master:main
```

Render detecta el push a `main`, instala dependencias y ejecuta:
```
gunicorn src.app:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

### Variables de entorno en produccion

Configuradas en el dashboard de Render:

| Variable | Descripcion |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL managed de Render (auto-configurada) |
| `SECRET_KEY` | Clave segura para sesiones Flask |
| `GITHUB_FEEDBACK_TOKEN` | Token GitHub para issues (opcional) |
| `PYTHON_VERSION` | `3.11.5` |

## Troubleshooting del Deploy

| Problema | Solucion |
|----------|----------|
| Build falla | Verificar `requirements.txt` (todas las dependencias listadas) |
| Timeout al iniciar | Verificar que `data/optimized/` tiene Parquets (mucho mas rapido que CSV) |
| 500 en produccion | Revisar logs en Render dashboard, verificar env vars |
| BD no conecta | Verificar `DATABASE_URL` en env vars de Render |
| Datos desactualizados | Actualizar archivos en `data/processed/` y `data/optimized/`, commitear y push |
