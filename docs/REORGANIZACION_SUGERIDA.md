# Plan de Reorganización del Proyecto

## Estado Actual - Problemas

1. **Carpetas de datos duplicadas/confusas:**
   - `datos_limpios/` - CSV procesados
   - `datos_procesados/` - Solo 1 archivo parquet?
   - `datos_rapidos/` - Parquet optimizados
   - `C:proyectos/` - Error de creación

2. **Carpeta produccion con .git propio:**
   - No debería tener su propio repositorio
   - Duplica archivos innecesariamente

3. **Archivos mezclados en raíz:**
   - Scripts Python junto con documentación
   - Sin separación clara de responsabilidades

## Estructura Propuesta

```
Visualizador_boletines/
│
├── 📄 README.md                    # Inicio rápido
├── 📄 requirements.txt             # Dependencias
├── 📄 .gitignore                   # Ignorar archivos
│
├── 📂 src/                         # CÓDIGO FUENTE
│   ├── preprocesamiento.py        # Excel → CSV
│   ├── preprocesar_csv_a_parquet.py # CSV → Parquet  
│   └── dashboard.py                # Dashboard principal
│
├── 📂 data/                        # TODOS LOS DATOS
│   ├── 📂 raw/                    # Excel original
│   │   └── nacional_serie_empleo_trimestral_actualizado241312.xlsx
│   ├── 📂 processed/              # CSV procesados
│   │   ├── C1.1.csv
│   │   ├── C1.2.csv
│   │   └── ... (todos los CSV)
│   └── 📂 optimized/              # Parquet optimizados
│       ├── c11.parquet
│       ├── c12.parquet
│       └── ... (todos los Parquet)
│
├── 📂 docs/                        # DOCUMENTACIÓN
│   ├── GEMINI.md                  # Documentación técnica completa
│   ├── FORMATO_EXCEL.md           # Especificación del Excel
│   └── ESTRUCTURA_PROYECTO.md     # Estructura del proyecto
│
└── 📂 deploy/                      # DESPLIEGUE
    ├── Procfile                    # Para Heroku/Render
    ├── render.yaml                 # Config de Render
    ├── runtime.txt                 # Versión Python
    └── app.py                      # Wrapper Gunicorn
```

## Comandos para Reorganizar

```bash
# 1. Crear nueva estructura
mkdir -p src data/raw data/processed data/optimized docs deploy tests

# 2. Mover archivos Python a src/
mv preprocesamiento.py src/
mv preprocesar_csv_a_parquet.py src/
mv dashboard.py src/

# 3. Mover datos
mv nacional_serie_empleo_trimestral_actualizado241312.xlsx data/raw/
mv datos_limpios/* data/processed/
mv datos_rapidos/* data/optimized/

# 4. Mover documentación
mv GEMINI.md FORMATO_EXCEL.md ESTRUCTURA_PROYECTO.md docs/

# 5. Mover archivos de deploy
mv produccion/Procfile produccion/render.yaml produccion/runtime.txt produccion/app.py deploy/

# 6. Limpiar carpetas vacías
rmdir datos_limpios datos_rapidos datos_procesados
rm -rf "C:proyectos"
rm -rf produccion  # Después de copiar lo necesario

# 7. Actualizar rutas en los scripts
# Necesario actualizar las rutas en los archivos Python
```

## Ventajas de esta Estructura

### ✅ Separación clara de responsabilidades:
- `src/` - Todo el código
- `data/` - Todos los datos
- `docs/` - Toda la documentación
- `deploy/` - Todo lo de despliegue

### ✅ Flujo de datos obvio:
- raw → processed → optimized

### ✅ Fácil de mantener:
- Cada cosa en su lugar
- Sin duplicaciones
- Sin confusión

### ✅ Preparado para crecer:
- Espacio para tests/
- Espacio para notebooks/
- Espacio para config/

## Actualización de Rutas en Código

### En src/preprocesamiento.py:
```python
# Cambiar:
output_dir = 'datos_limpios'
# Por:
output_dir = '../data/processed'

# Cambiar:
input_file = 'nacional_serie_empleo_trimestral_actualizado241312.xlsx'
# Por:
input_file = '../data/raw/nacional_serie_empleo_trimestral_actualizado241312.xlsx'
```

### En src/preprocesar_csv_a_parquet.py:
```python
# Cambiar:
input_dir = 'datos_limpios'
output_dir = 'datos_rapidos'
# Por:
input_dir = '../data/processed'
output_dir = '../data/optimized'
```

### En src/dashboard.py:
```python
# Cambiar:
DATA_DIR = 'datos_limpios'
parquet_dir = 'datos_rapidos'
# Por:
DATA_DIR = '../data/processed'
parquet_dir = '../data/optimized'
```

## Para GitHub

### .gitignore sugerido:
```
# Python
__pycache__/
*.py[cod]
*$py.class
.Python
env/
venv/

# Datos grandes (opcional)
data/raw/*.xlsx
data/optimized/*.parquet

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Temporales
*.log
*.tmp
```

## Siguiente Paso

¿Quieres que ejecute esta reorganización? Incluirá:
1. Mover todos los archivos a su nueva ubicación
2. Actualizar todas las rutas en el código
3. Limpiar carpetas redundantes
4. Crear un .gitignore apropiado
5. Actualizar README con la nueva estructura

Esto hará el proyecto mucho más profesional y mantenible.