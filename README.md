# Visualizador de Boletines de Empleo Registrado

Dashboard interactivo para analisis y visualizacion de datos de empleo registrado en Argentina (SIPA/OEDE).

## Inicio Rapido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar (sin BD = modo desarrollo, acceso publico completo)
python src/app.py

# 3. Abrir en navegador
# http://localhost:8050
```

## Caracteristicas

### 11 Pestanas de Visualizacion

| Tab | Descripcion |
|-----|-------------|
| **Resumen** | KPIs ejecutivos con sparklines de todas las fuentes |
| **Analisis** | Empleo temporal + sectorial + por tamano de empresa |
| **Remuneraciones** | Salarios nominales y reales (deflactados por IPC) |
| **Empresas** | Cantidad de empresas por sector y tamano |
| **Flujos** | Altas, bajas, creacion neta y rotacion de empleo |
| **Genero** | Empleo por genero y brecha salarial |
| **Comparaciones** | Comparacion entre dos periodos con presets |
| **Alertas** | Deteccion de anomalias multi-fuente |
| **Datos** | Explorador con metadatos y descarga CSV |
| **Metodologia** | Referencia metodologica OEDE/SIPA |
| **Admin** | Gestion de feedback, usuarios y configuracion |

### Funcionalidades Adicionales

- **Autenticacion**: Flask-Login + PostgreSQL, roles admin/viewer, degradacion graceful sin BD
- **Feedback**: 31 componentes con botones de feedback (20 graficos + 6 KPIs + 5 tablas)
- **Panel Admin**: Gestion de feedback, usuarios y configuracion del sistema

## Arquitectura

```
src/
├── app.py              # Entry point (Dash + Flask)
├── config.py           # Constantes y mapeos
├── auth/               # Autenticacion (Flask-Login + SQLAlchemy)
├── callbacks/          # 14 grupos de callbacks Dash
├── data/               # Cache singleton, loader, processing
├── layout/             # Componentes UI (KPIs, feedback, main layout)
└── tabs/               # 11 pestanas del dashboard

scripts/                # Descarga, preprocesamiento, init BD
tests/                  # pytest (5 archivos)
data/                   # raw/ → processed/ → optimized/
assets/                 # custom.css (estilos institucionales OEDE)
```

## Estructura del Proyecto

Ver arbol completo en [docs/ESTRUCTURA_PROYECTO.md](docs/ESTRUCTURA_PROYECTO.md).

## Variables de Entorno

| Variable | Requerida | Descripcion |
|----------|-----------|-------------|
| `DATABASE_URL` | No | PostgreSQL. Sin ella, corre en modo dev (publico) |
| `SECRET_KEY` | No | Clave Flask. Default: `dev-secret-key-cambiar` |
| `GITHUB_FEEDBACK_TOKEN` | No | Token GitHub para issues de feedback |
| `PORT` | No | Puerto del servidor. Default: `8050` |

## Stack Tecnologico

| Tecnologia | Version | Uso |
|------------|---------|-----|
| Dash | 2.14 | Framework del dashboard |
| Plotly | 5.18 | Graficos interactivos |
| Pandas | 2.1 | Procesamiento de datos |
| Flask-Login | 0.6 | Autenticacion |
| SQLAlchemy | 2.0 | ORM para PostgreSQL |
| PostgreSQL | — | Base de datos (auth + feedback) |
| Gunicorn | 21.2 | Servidor WSGI (produccion) |
| Bootstrap 5 | — | Estilos base (via dash-bootstrap-components) |
| PyArrow | 14.0 | Lectura de Parquet |

## Datos

26+ datasets de 8 fuentes:

| Fuente | Datasets | Frecuencia |
|--------|----------|-----------|
| Empleo trimestral (OEDE) | C1.1 a C7 (9 datasets) | Trimestral |
| Remuneraciones (OEDE) | R1 a R4 + R1-R3 reales | Mensual |
| Empresas (OEDE) | E1 a E3 | Anual |
| Flujos de empleo (OEDE) | F1 a F3 | Trimestral |
| Genero (OEDE) | G1 a G3 | Trimestral |
| IPC | IPC | Mensual |
| Descriptores | CIIU, remuneraciones | Estatico |

Pipeline: `scripts/download_oede.py` → `scripts/preprocess/*.py` → `data/optimized/*.parquet`

## Deploy

Desplegado en [Render](https://render.com) con PostgreSQL managed.

```bash
# Deploy: push a main dispara auto-deploy
git push origin master:main
```

Ver detalles en [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md#14-deploy-en-produccion).

## Documentacion

| Documento | Descripcion |
|-----------|-------------|
| [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md) | Referencia tecnica completa |
| [INICIO_RAPIDO.md](INICIO_RAPIDO.md) | Guia de 2 minutos para arrancar |
| [FLUJO_DESARROLLO.md](FLUJO_DESARROLLO.md) | Workflow desarrollo → produccion |
| [docs/ESTRUCTURA_PROYECTO.md](docs/ESTRUCTURA_PROYECTO.md) | Arbol de archivos con descripciones |
| [docs/FORMATO_EXCEL.md](docs/FORMATO_EXCEL.md) | Formato del Excel de empleo |
| [INDICE_DOCUMENTACION.md](INDICE_DOCUMENTACION.md) | Indice completo de documentacion |

---

*Fuente: SIPA | Ministerio de Capital Humano*
