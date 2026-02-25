# Estructura del Proyecto

## Arbol de Archivos

```
Visualizador_boletines/
├── src/                          # Codigo fuente principal
│   ├── app.py                    # Entry point (Dash + Flask)
│   ├── config.py                 # Constantes, colores, mapeos de datasets
│   ├── feedback.py               # Cliente GitHub Issues API
│   │
│   ├── auth/                     # Sistema de autenticacion
│   │   ├── __init__.py
│   │   ├── manager.py            # Flask-Login setup, auth_enabled(), get_db_session()
│   │   ├── models.py             # Modelos SQLAlchemy: User, Feedback, AppConfig
│   │   └── routes.py             # Blueprint login/logout (HTML inline)
│   │
│   ├── callbacks/                # Logica interactiva (Dash callbacks)
│   │   ├── __init__.py
│   │   ├── feedback.py           # Submit feedback → BD + GitHub
│   │   ├── global_controls.py    # Switching de tabs
│   │   └── register.py           # Registro centralizado de 14 grupos de callbacks
│   │
│   ├── data/                     # Capa de datos
│   │   ├── __init__.py
│   │   ├── cache.py              # DataCache singleton thread-safe
│   │   ├── db.py                 # get_engine() desde DATABASE_URL
│   │   ├── loader.py             # Carga desde Parquet/CSV/PostgreSQL
│   │   └── processing.py         # Parseo de periodos, variaciones, filtros
│   │
│   ├── layout/                   # Componentes de UI
│   │   ├── __init__.py
│   │   ├── components.py         # KPI cards, section cards, format_number
│   │   ├── feedback_components.py # graph_with_feedback(), modal de feedback
│   │   └── main.py               # Layout principal: header + tabs + footer
│   │
│   └── tabs/                     # 11 pestanas del dashboard
│       ├── __init__.py
│       ├── resumen.py            # KPIs ejecutivos + sparklines
│       ├── analisis.py           # Analisis temporal + sectorial + por tamano
│       ├── remuneraciones.py     # Salarios nominales y reales (deflactados por IPC)
│       ├── empresas.py           # Cantidad de empresas por sector/tamano
│       ├── flujos.py             # Altas/bajas de empleo, creacion neta, rotacion
│       ├── genero.py             # Empleo por genero + brecha salarial
│       ├── comparaciones.py      # Comparacion periodo A vs B con presets
│       ├── alertas.py            # Deteccion de anomalias multi-fuente
│       ├── datos.py              # Explorador de datos + metadatos + descarga CSV
│       ├── metodologia.py        # Referencia metodologica (HTML estatico)
│       └── admin.py              # Panel admin: feedback, usuarios, configuracion
│
├── scripts/                      # Scripts utilitarios
│   ├── download_oede.py          # Descarga Excel de argentina.gob.ar
│   ├── init_db.py                # Bootstrap BD + primer usuario admin
│   ├── cargar_datos.py           # Ingesta Excel/CSV → PostgreSQL
│   ├── schema.sql                # Schema PostgreSQL (9 tablas + 11 indices)
│   ├── setup_feedback_labels.py  # Labels de GitHub para feedback (one-time)
│   └── preprocess/               # Procesadores de datos
│       ├── __init__.py
│       ├── base.py               # Clase abstracta ExcelProcessor
│       ├── empleo_trimestral.py  # Excel → C1.1-C7 + descriptores
│       ├── remuneraciones_mes.py # Excel → R1-R4 + descriptores
│       ├── empresas.py           # Excel → E1-E3
│       ├── flujos.py             # Excel → F1-F3
│       ├── genero.py             # Excel → G1-G3
│       └── ipc.py                # CSV → IPC
│
├── tests/                        # Tests automatizados (pytest)
│   ├── __init__.py
│   ├── test_cache.py             # Tests del singleton DataCache
│   ├── test_ingestion.py         # Tests de ingesta de datos
│   ├── test_loader.py            # Tests de carga de datos
│   ├── test_processing.py        # Tests de parseo de periodos y variaciones
│   └── test_tabs.py              # Smoke tests: todas las tabs renderizan
│
├── assets/
│   └── custom.css                # Estilos institucionales OEDE (--sipa-*)
│
├── data/
│   ├── raw/                      # Archivos fuente (Excel/CSV, no en git)
│   │   ├── empleo_trimestral.xlsx
│   │   ├── remuneraciones_mensual.xlsx
│   │   ├── empresas_anual.xlsx
│   │   ├── flujos_empleo.xlsx
│   │   ├── genero.xlsx
│   │   └── ipc_mensual.csv
│   ├── processed/                # CSVs procesados (en git)
│   │   ├── C1.1.csv ... C7.csv
│   │   ├── R1.csv ... R4.csv
│   │   ├── E1.csv, E2.csv
│   │   ├── F1.csv ... F3.csv
│   │   ├── G1.csv, G2.csv
│   │   ├── IPC.csv
│   │   └── descriptores_*.csv
│   └── optimized/                # Parquet comprimidos (en git)
│       ├── c11.parquet ... c7.parquet
│       ├── r1.parquet ... r4.parquet
│       ├── e1.parquet, e2.parquet
│       ├── f1.parquet ... f3.parquet
│       ├── g1.parquet, g2.parquet
│       ├── ipc.parquet
│       └── descriptores*.parquet
│
├── docs/                         # Documentacion
│   ├── ESTRUCTURA_PROYECTO.md    # Este archivo
│   ├── FORMATO_EXCEL.md          # Formato esperado del Excel de empleo
│   └── GEMINI.md                 # Registro historico del desarrollo inicial
│
├── .env.example                  # Template de variables de entorno
├── .python-version               # Python 3.11.5
├── Procfile                      # gunicorn src.app:server
├── requirements.txt              # 14 dependencias
├── README.md                     # Presentacion del proyecto
├── DOCUMENTACION_COMPLETA.md     # Referencia tecnica completa
├── INICIO_RAPIDO.md              # Guia rapida de arranque
├── FLUJO_DESARROLLO.md           # Workflow desarrollo → produccion
└── INDICE_DOCUMENTACION.md       # Indice de toda la documentacion
```

## Descripcion de Modulos

### `src/auth/` — Autenticacion

Sistema condicional de autenticacion. Solo se activa si `DATABASE_URL` esta configurada; sin ella, el dashboard corre en modo desarrollo con acceso admin publico.

- **`manager.py`**: Inicializa Flask-Login, expone `auth_enabled()` y `get_db_session()`
- **`models.py`**: Tres modelos SQLAlchemy — `User` (email, role, password_hash), `Feedback` (graph_id, category, status, JSONB context), `AppConfig` (key-value)
- **`routes.py`**: Blueprint Flask con `/login` (GET=formulario HTML, POST=validacion) y `/logout`

Roles: `admin` (ve todo + feedback + panel admin) | `viewer` (solo visualizacion)

### `src/callbacks/` — Logica Interactiva

Callbacks de Dash organizados por funcionalidad. Se registran centralmente desde `register.py`.

- **`register.py`**: Llama a 14 funciones `register_*_callbacks(app)` (una por tab + globales + feedback + admin)
- **`global_controls.py`**: Switching entre tabs
- **`feedback.py`**: Abre modal → guarda en BD → opcionalmente crea issue en GitHub

### `src/data/` — Capa de Datos

Carga, cacheo y procesamiento de los 26+ datasets.

- **`cache.py`**: Singleton `DataCache` thread-safe. Se carga una vez al inicio. Ofrece `get_ref(key)` (lectura sin copia) y `get(key)` (copia)
- **`loader.py`**: `load_all_data()` intenta BD primero, fallback a archivos locales (Parquet preferido, luego CSV). Calcula datasets derivados (R1_real, R2_real, R3_real = salario/IPC*100)
- **`processing.py`**: `process_periods()` parsea strings de periodo a fechas; `calculate_variations()` calcula cambios trimestrales/interanuales + indice base 100
- **`db.py`**: `get_engine()` crea engine SQLAlchemy desde `DATABASE_URL`

### `src/layout/` — Componentes de UI

Componentes reutilizables para construir la interfaz.

- **`main.py`**: `create_main_layout()` arma header + tabs + footer + modal de feedback. La funcion `serve_layout()` en `app.py` la invoca en cada request para inyectar el rol del usuario
- **`components.py`**: `create_kpi_card()`, `create_section_card()`, `format_number()`
- **`feedback_components.py`**: `graph_with_feedback()` envuelve cualquier componente con un boton de feedback (visible solo para admins via CSS)

### `src/tabs/` — Pestanas del Dashboard

Cada archivo exporta `create_<nombre>_layout()` y `register_<nombre>_callbacks(app)`.

| Tab | Archivo | Datos que usa |
|-----|---------|--------------|
| Resumen | `resumen.py` | Todos (KPIs cross-source) |
| Analisis | `analisis.py` | C1-C7 (empleo trimestral) |
| Remuneraciones | `remuneraciones.py` | R1-R4, IPC (salarios + deflactados) |
| Empresas | `empresas.py` | E1-E3 (cantidad de empresas) |
| Flujos | `flujos.py` | F1-F3 (altas/bajas/rotacion) |
| Genero | `genero.py` | G1-G3 (empleo + brecha salarial) |
| Comparaciones | `comparaciones.py` | Todos (comparacion entre periodos) |
| Alertas | `alertas.py` | Todos (deteccion de anomalias) |
| Datos | `datos.py` | Todos (explorador + descarga) |
| Metodologia | `metodologia.py` | Ninguno (referencia estatica) |
| Admin | `admin.py` | BD: feedback, users, config |

### `scripts/` — Utilidades

- **`download_oede.py`**: Descarga archivos Excel/CSV desde URLs oficiales a `data/raw/`
- **`preprocess/`**: Cada procesador extiende `ExcelProcessor` (base abstracta). Lee Excel crudo, transforma, y genera CSV + Parquet
- **`init_db.py`**: Crea tablas SQLAlchemy + primer usuario admin interactivo
- **`cargar_datos.py`**: Ingesta masiva de datos a PostgreSQL
- **`schema.sql`**: Schema SQL completo (9 tablas de datos + indices)

### `tests/` — Tests

Tests con pytest. Incluyen tests unitarios de procesamiento, cache, carga, y smoke tests de todas las tabs.

## Flujo de Datos

```
Fuentes oficiales (OEDE, IPC)
        │
        ▼
scripts/download_oede.py ──→ data/raw/*.xlsx, *.csv
        │
        ▼
scripts/preprocess/*.py ───→ data/processed/*.csv + data/optimized/*.parquet
        │
        ▼
src/data/loader.py ────────→ DataCache (singleton en memoria)
        │
        ▼
src/tabs/*.py + callbacks/ → Dashboard interactivo (Dash/Plotly)
```

## Entry Points

| Contexto | Comando | Que ejecuta |
|----------|---------|------------|
| Desarrollo local | `python src/app.py` | Dash dev server en puerto 8050 |
| Produccion (Render) | `gunicorn src.app:server` | Via Procfile |
| Descargar datos | `python scripts/download_oede.py --all` | Descarga Excel/CSV a data/raw/ |
| Preprocesar datos | `python scripts/preprocess/empleo_trimestral.py` | (y cada procesador individual) |
| Inicializar BD | `python scripts/init_db.py` | Crea tablas + primer admin |
| Tests | `pytest tests/` | Ejecuta todos los tests |

## Archivos Legacy

Estos archivos existen en el repositorio pero **no son parte del sistema activo**:

| Archivo | Razon por la que sigue |
|---------|----------------------|
| `src/dashboard.py` (92 KB) | Dashboard monolitico original, referencia historica |
| `src/preprocesamiento.py` (21 KB) | Preprocesamiento original, importado por `scripts/cargar_datos.py` |
| `src/preprocesar_csv_a_parquet.py` | Conversor CSV→Parquet original |
| `deploy/` | Carpeta de deploy legacy (gitignored, tiene su propio .git) |
| `sincronizar_a_produccion.py` | Script de sync dev→deploy (ya no se usa) |
