# Documentacion Completa — Visualizador de Boletines de Empleo

> **Version**: 3.0
> **Fecha**: Febrero 2026
> **Estado**: Produccion (Render)

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Instalacion y Configuracion](#3-instalacion-y-configuracion)
4. [Sistema de Autenticacion](#4-sistema-de-autenticacion)
5. [Estructura del Proyecto](#5-estructura-del-proyecto)
6. [Flujo de Datos](#6-flujo-de-datos)
7. [Dashboard — Tabs](#7-dashboard--tabs)
8. [Sistema de Feedback](#8-sistema-de-feedback)
9. [Panel de Administracion](#9-panel-de-administracion)
10. [Callbacks](#10-callbacks)
11. [Pipeline de Datos](#11-pipeline-de-datos)
12. [Base de Datos](#12-base-de-datos)
13. [CSS y Estilos](#13-css-y-estilos)
14. [Deploy en Produccion](#14-deploy-en-produccion)
15. [Desarrollo Local](#15-desarrollo-local)
16. [Testing](#16-testing)
17. [Troubleshooting](#17-troubleshooting)
18. [Historial de Cambios](#18-historial-de-cambios)

---

## 1. Resumen Ejecutivo

El **Visualizador de Boletines de Empleo Registrado** es un dashboard interactivo que presenta datos del empleo registrado en Argentina, publicados por el OEDE (Observatorio de Empleo y Dinamica Empresarial) del Ministerio de Capital Humano.

El sistema:
- Descarga y procesa datos de 8 fuentes oficiales (empleo, remuneraciones, empresas, flujos, genero, IPC)
- Presenta 26+ datasets en 11 pestanas interactivas con graficos Plotly
- Implementa autenticacion con roles (admin/viewer) via Flask-Login + PostgreSQL
- Incluye sistema de feedback por componente (31 componentes) con almacenamiento en BD y GitHub Issues
- Se despliega en Render con PostgreSQL managed

**Stack**: Python 3.11 | Dash 2.14 | Plotly 5.18 | Pandas 2.1 | Flask-Login 0.6 | SQLAlchemy 2.0 | PostgreSQL | Gunicorn | Bootstrap 5

---

## 2. Arquitectura del Sistema

### Diagrama de Modulos

```
                    ┌──────────────────────────────────┐
                    │         src/app.py                │
                    │  (Entry point: Dash + Flask)      │
                    └──────┬───────────┬────────────────┘
                           │           │
              ┌────────────▼──┐   ┌────▼──────────────┐
              │  src/auth/    │   │  src/layout/       │
              │  (Login,      │   │  (Header, tabs,    │
              │   roles,      │   │   footer, modal,   │
              │   modelos BD) │   │   KPI cards)       │
              └───────────────┘   └────────────────────┘
                                          │
                    ┌─────────────────────▼──────────────┐
                    │          src/tabs/                  │
                    │  (11 pestanas: resumen, analisis,   │
                    │   remuneraciones, empresas, flujos, │
                    │   genero, comparaciones, alertas,   │
                    │   datos, metodologia, admin)        │
                    └──────────────┬─────────────────────┘
                                   │
              ┌────────────────────▼─────────────────────┐
              │           src/callbacks/                  │
              │  (14 grupos: 1 por tab + globales +       │
              │   feedback + admin)                       │
              └────────────────────┬─────────────────────┘
                                   │
              ┌────────────────────▼─────────────────────┐
              │           src/data/                       │
              │  (DataCache singleton, loader, processing)│
              └────────────────────┬─────────────────────┘
                                   │
              ┌────────────────────▼─────────────────────┐
              │     data/optimized/*.parquet              │
              │     data/processed/*.csv                  │
              │     PostgreSQL (si DATABASE_URL)          │
              └──────────────────────────────────────────┘
```

### Diagrama de Flujo de Datos

```
OEDE (argentina.gob.ar)          GitHub (IPC)
        │                              │
        ▼                              ▼
  scripts/download_oede.py ──→ data/raw/*.xlsx, *.csv
        │
        ▼
  scripts/preprocess/*.py ───→ data/processed/*.csv
        │                      data/optimized/*.parquet
        ▼
  src/data/loader.py ────────→ DataCache (memoria, singleton)
        │
        ▼
  src/tabs/*.py ─────────────→ Graficos Plotly + tablas
        │
        ▼
  src/callbacks/*.py ────────→ Interactividad (filtros, exports, feedback)
```

---

## 3. Instalacion y Configuracion

### Requisitos

- Python 3.11+
- PostgreSQL (opcional, solo para autenticacion)

### Instalacion

```bash
# 1. Clonar repositorio
git clone https://github.com/gbreard/visualizador-boletines.git
cd visualizador-boletines

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar (modo desarrollo, sin BD)
python src/app.py
```

El dashboard estara disponible en `http://localhost:8050`.

### Variables de Entorno

Crear un archivo `.env` en la raiz (ver `.env.example`):

| Variable | Requerida | Descripcion |
|----------|-----------|-------------|
| `DATABASE_URL` | No | Conexion PostgreSQL. Sin ella, el dashboard corre publico (modo dev) |
| `SECRET_KEY` | No | Clave para sesiones Flask. Default: `dev-secret-key-cambiar` |
| `GITHUB_FEEDBACK_TOKEN` | No | Token GitHub para crear issues de feedback |
| `PORT` | No | Puerto del servidor. Default: `8050` |

### Primer Arranque con BD

```bash
# 1. Configurar DATABASE_URL en .env
# 2. Inicializar base de datos + crear primer admin
python scripts/init_db.py

# 3. Ejecutar
python src/app.py
```

---

## 4. Sistema de Autenticacion

### Arquitectura

La autenticacion es **condicional**: solo se activa si `DATABASE_URL` esta configurada. Sin ella, el dashboard corre en "modo desarrollo" con acceso admin publico completo.

Secuencia de inicio en `src/app.py`:
1. Intenta obtener engine con `get_engine()`
2. Si hay BD: inicializa Flask-Login, registra Blueprint de auth
3. Si no hay BD: log "modo desarrollo", corre sin auth

### Roles

| Rol | Acceso | Feedback | Admin |
|-----|--------|----------|-------|
| `admin` | Todas las tabs | Puede enviar feedback | Panel admin completo |
| `viewer` | Tabs de visualizacion | No ve botones de feedback | Sin acceso |
| Sin login (modo dev) | Todo | Feedback habilitado | Acceso admin |

### Login / Logout

- **`/login`** (GET): Formulario HTML renderizado inline desde `src/auth/routes.py`
- **`/login`** (POST): Valida email + password, crea sesion Flask-Login
- **`/logout`**: Cierra sesion y redirige a `/login`

### Modelos (SQLAlchemy)

```python
class User:
    id, email, password_hash, nombre, role, is_active, created_at, updated_at

class Feedback:
    id, graph_id, graph_label, tab, category, description,
    context (JSONB), status, admin_notes, github_issue_url,
    created_by, created_at, updated_at

class AppConfig:
    key, value  # ej: github_issues_enabled = 'true'
```

### Degradacion Graceful

Sin BD, el sistema:
- No muestra pagina de login
- Asigna rol `admin` a todos los visitantes
- El feedback se puede enviar pero solo se guarda en GitHub (si el token esta configurado)
- `auth_enabled()` retorna `False`

---

## 5. Estructura del Proyecto

Ver [docs/ESTRUCTURA_PROYECTO.md](docs/ESTRUCTURA_PROYECTO.md) para el arbol completo con descripciones.

Resumen:

```
src/
├── app.py              # Entry point
├── config.py           # Constantes y mapeos
├── auth/               # Autenticacion (Flask-Login + SQLAlchemy)
├── callbacks/          # 14 grupos de callbacks Dash
├── data/               # Cache, loader, processing
├── layout/             # Componentes UI (KPIs, feedback, main)
└── tabs/               # 11 pestanas del dashboard

scripts/                # Download, preprocess, init_db
tests/                  # pytest (5 archivos de tests)
data/                   # raw/ → processed/ → optimized/
assets/                 # custom.css
docs/                   # Documentacion adicional
```

---

## 6. Flujo de Datos

### Etapa 1 — Descarga

`scripts/download_oede.py` descarga archivos desde URLs oficiales a `data/raw/`:

| Archivo | Contenido | Fuente |
|---------|-----------|--------|
| `empleo_trimestral.xlsx` | Empleo C1-C7 | OEDE |
| `remuneraciones_mensual.xlsx` | Salarios R1-R4 | OEDE |
| `empresas_anual.xlsx` | Empresas E1-E3 | OEDE |
| `flujos_empleo.xlsx` | Flujos F1-F3 | OEDE |
| `genero.xlsx` | Genero G1-G3 | OEDE |
| `ipc_mensual.csv` | IPC | GitHub (matuteiglesias) |

### Etapa 2 — Preprocesamiento

Cada procesador en `scripts/preprocess/` extiende la clase abstracta `ExcelProcessor` (`base.py`):

1. Lee hojas del Excel crudo
2. Limpia y transforma (manejo de encabezados, valores especiales, periodos)
3. Genera CSV en `data/processed/` y Parquet en `data/optimized/`

Procesadores:
- `empleo_trimestral.py` → C1.1, C1.2, C2.1, C2.2, C3, C4, C5, C6, C7 + descriptores_CIIU
- `remuneraciones_mes.py` → R1, R2, R3, R4 + descriptores_remuneraciones
- `empresas.py` → E1, E2, E3
- `flujos.py` → F1, F2, F3
- `genero.py` → G1, G2, G3
- `ipc.py` → IPC

### Etapa 3 — Carga en Runtime

`src/data/loader.py` ejecuta `load_all_data()` una sola vez al inicio:

1. Intenta cargar desde PostgreSQL (si `DATABASE_URL` existe)
2. Fallback: carga desde Parquet (preferido) o CSV
3. Aplica `process_periods()` — parsea strings de periodo a fechas
4. Aplica `calculate_variations()` — calcula cambios trim/interanual + indice base 100
5. Genera datasets derivados: `R1_real`, `R2_real`, `R3_real` (salario deflactado por IPC)
6. Almacena todo en `DataCache` (singleton thread-safe)

### DataCache

Singleton en `src/data/cache.py`:
- `cache.load(load_all_data)` — carga una vez al inicio
- `cache.get_ref(key)` — lectura sin copia (para graficos, read-only)
- `cache.get(key)` — copia del DataFrame (para mutacion)
- `cache.periods` — lista de periodos disponibles
- `cache.last_period` — ultimo periodo
- `cache.data_keys` — claves disponibles

### Datasets Disponibles (26+)

| Grupo | Claves | Frecuencia |
|-------|--------|-----------|
| Empleo | C1.1, C1.2, C2.1, C2.2, C3, C4, C5, C6, C7 | Trimestral |
| Remuneraciones | R1, R2, R3, R4 | Mensual |
| Remuneraciones reales | R1_real, R2_real, R3_real | Mensual (calculado) |
| Empresas | E1, E2, E3 | Anual |
| Flujos | F1, F2, F3 | Trimestral |
| Genero | G1, G2, G3 | Trimestral |
| IPC | IPC | Mensual |
| Descriptores | descriptores_CIIU, descriptores_remuneraciones | Estatico |

---

## 7. Dashboard — Tabs

El dashboard tiene 11 pestanas. Cada archivo en `src/tabs/` exporta `create_<nombre>_layout()` y `register_<nombre>_callbacks(app)`.

### Tab 1: Resumen

**Archivo**: `src/tabs/resumen.py`

KPIs ejecutivos que cruzan todas las fuentes de datos. Muestra tarjetas con valores actuales, variaciones y sparklines de tendencia. Proporciona una vision general rapida del estado del empleo registrado.

### Tab 2: Analisis

**Archivo**: `src/tabs/analisis.py`

Tres sub-secciones:
- **Temporal**: Evolucion del empleo total (C1.1/C1.2), con opciones de serie original/desestacionalizada
- **Sectorial**: Empleo por sector economico (C2, C3, C4, C6, C7) con diferentes niveles de granularidad CIIU
- **Por tamano**: Empleo cruzado por sector y tamano de empresa (C5)

### Tab 3: Remuneraciones

**Archivo**: `src/tabs/remuneraciones.py`

Evolucion de salarios nominales (R1-R4) y reales (deflactados por IPC). Incluye barras por sector, tabla de detalle y comparaciones de poder adquisitivo.

### Tab 4: Empresas

**Archivo**: `src/tabs/empresas.py`

Cantidad de empresas por sector y tamano (E1-E3). Visualizaciones de evolucion temporal y composicion sectorial.

### Tab 5: Flujos

**Archivo**: `src/tabs/flujos.py`

Altas y bajas de empleo, creacion neta de puestos y tasas de rotacion (F1-F3). Permite analizar la dinamica del mercado laboral.

### Tab 6: Genero

**Archivo**: `src/tabs/genero.py`

Empleo registrado por genero y brecha salarial (G1-G3). Incluye evolucion de la participacion femenina y diferencias salariales por sector.

### Tab 7: Comparaciones

**Archivo**: `src/tabs/comparaciones.py`

Comparacion entre dos periodos seleccionados (A vs B). Incluye presets predefinidos (ej: ultimo trimestre vs mismo trimestre ano anterior). Muestra variaciones absolutas y porcentuales para todos los indicadores.

### Tab 8: Alertas

**Archivo**: `src/tabs/alertas.py`

Deteccion de anomalias multi-fuente. El usuario define umbrales y el sistema identifica variaciones inusuales en cualquier dataset. Util para detectar cambios estructurales o problemas de datos.

### Tab 9: Datos

**Archivo**: `src/tabs/datos.py`

Explorador de datos con metadatos de cada dataset. Permite ver tablas completas, aplicar filtros y descargar en formato CSV.

### Tab 10: Metodologia

**Archivo**: `src/tabs/metodologia.py`

Referencia metodologica estatica (HTML). Documenta fuentes, definiciones y criterios de calculo del OEDE/SIPA.

### Tab 11: Admin (solo admin)

**Archivo**: `src/tabs/admin.py`

Panel de administracion con 3 sub-tabs. Solo visible para usuarios con rol `admin`. Ver [seccion 9](#9-panel-de-administracion).

---

## 8. Sistema de Feedback

### Componentes con Feedback (31 total)

El sistema de feedback cubre 31 componentes del dashboard:
- **20 graficos** (charts Plotly en distintas tabs)
- **6 KPI cards** (tarjetas de indicadores)
- **5 tablas** (DataTables interactivas)

### Flujo

```
1. Usuario hace click en boton "Feedback" (icono en esquina del componente)
        │
        ▼
2. Se abre modal con: graph_id, categoria (dropdown), descripcion (textarea)
        │
        ▼
3. Callback en src/callbacks/feedback.py procesa el envio
        │
        ├──→ Guarda en BD (tabla feedback) — SIEMPRE si hay BD
        │
        └──→ Crea issue en GitHub — SOLO si github_issues_enabled = true
             y GITHUB_FEEDBACK_TOKEN esta configurado
        │
        ▼
4. Confirmacion al usuario
```

### Implementacion Tecnica

**Renderizado**: `graph_with_feedback(component, graph_id, graph_label)` en `src/layout/feedback_components.py` envuelve cualquier componente Dash en un `div` relativo con un boton absoluto.

**Visibilidad**: Controlada por CSS, no por logica Python. El layout principal asigna la clase `sipa-role-viewer` o `sipa-role-admin` al body. Los botones de feedback tienen clase `sipa-feedback-btn`. La regla CSS:

```css
.sipa-role-viewer .sipa-feedback-btn { display: none !important; }
```

Esto asegura que los botones no son visibles para viewers sin necesidad de renderizado condicional.

**Categorias de feedback**: Bug, Sugerencia, Datos incorrectos, Otro.

**Contexto automatico**: Cada feedback incluye metadata JSONB con tab activa, periodo seleccionado, filtros aplicados.

---

## 9. Panel de Administracion

**Archivo**: `src/tabs/admin.py` — Solo accesible para rol `admin`.

### Sub-tab 1: Gestion de Feedback

- Lista todos los feedbacks recibidos con filtros por estado/categoria
- Estados: `pendiente`, `en_revision`, `resuelto`, `descartado`
- Admin puede cambiar estado y agregar notas
- Link al issue de GitHub si fue creado

### Sub-tab 2: Gestion de Usuarios

- Lista usuarios registrados
- Crear nuevo usuario (email, nombre, password, rol)
- Cambiar rol (admin/viewer)
- Activar/desactivar usuarios

### Sub-tab 3: Configuracion

- Toggle `github_issues_enabled` — activa/desactiva la creacion de issues en GitHub
- Otras configuraciones via tabla `app_config` (key-value)

### Seguridad

Todos los callbacks del admin validan el rol server-side via `_is_request_admin()`. La verificacion no depende del frontend — un request directo sin rol admin es rechazado.

---

## 10. Callbacks

### Registro Centralizado

`src/callbacks/register.py` llama a 14 funciones de registro:

```
register_global_callbacks(app)        # Tab switching
register_feedback_callbacks(app)      # Modal + submit
register_admin_callbacks(app)         # Panel admin
register_resumen_callbacks(app)       # Tab Resumen
register_analisis_callbacks(app)      # Analisis temporal
register_sectorial_callbacks(app)     # Analisis sectorial
register_tamano_callbacks(app)        # Analisis por tamano
register_comparaciones_callbacks(app) # Comparaciones
register_alertas_callbacks(app)       # Alertas
register_datos_callbacks(app)         # Explorador de datos
register_remuneraciones_callbacks(app)# Remuneraciones
register_empresas_callbacks(app)      # Empresas
register_flujos_callbacks(app)        # Flujos
register_genero_callbacks(app)        # Genero
```

### Patron

Cada tab define sus callbacks en su propio archivo, dentro de una funcion `register_<nombre>_callbacks(app)`. Los callbacks:
- Reciben inputs del usuario (dropdowns, sliders, clicks)
- Leen datos de `cache.get_ref(key)` o `cache.get(key)`
- Generan figuras Plotly y/o datos para DataTables
- Retornan outputs al layout

---

## 11. Pipeline de Datos

### Scripts de Descarga

```bash
# Descargar todos los archivos
python scripts/download_oede.py --all

# Descargar solo un tipo
python scripts/download_oede.py --empleo
python scripts/download_oede.py --remuneraciones
```

Descarga desde URLs oficiales de argentina.gob.ar y GitHub.

### Scripts de Preprocesamiento

Todos en `scripts/preprocess/`, extienden `ExcelProcessor` (clase abstracta en `base.py`):

```bash
# Procesar empleo trimestral
python scripts/preprocess/empleo_trimestral.py

# Procesar remuneraciones
python scripts/preprocess/remuneraciones_mes.py

# Procesar empresas, flujos, genero, IPC
python scripts/preprocess/empresas.py
python scripts/preprocess/flujos.py
python scripts/preprocess/genero.py
python scripts/preprocess/ipc.py
```

Cada procesador:
1. Lee el Excel/CSV crudo de `data/raw/`
2. Extrae y limpia datos por hoja
3. Normaliza periodos, maneja valores especiales ("s.d.", "-", etc.)
4. Genera CSV en `data/processed/` y Parquet en `data/optimized/`

### Ingesta a PostgreSQL (opcional)

```bash
python scripts/cargar_datos.py data/raw/empleo_trimestral.xlsx
```

Carga datos procesados a las tablas PostgreSQL definidas en `scripts/schema.sql`.

---

## 12. Base de Datos

### Modelos ORM (src/auth/models.py)

Tres tablas gestionadas por SQLAlchemy:

**users**
| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | Integer PK | Autoincremental |
| email | String, unique | Login |
| password_hash | String | Werkzeug hash |
| nombre | String | Nombre para display |
| role | String | `admin` o `viewer` |
| is_active | Boolean | Permite desactivar sin borrar |
| created_at | DateTime | Automatico |
| updated_at | DateTime | Automatico |

**feedback**
| Columna | Tipo | Descripcion |
|---------|------|-------------|
| id | Integer PK | Autoincremental |
| graph_id | String | ID del componente (ej: `resumen-kpi-empleo`) |
| graph_label | String | Etiqueta legible |
| tab | String | Tab donde se envio |
| category | String | Bug, Sugerencia, Datos incorrectos, Otro |
| description | Text | Descripcion del usuario |
| context | JSONB | Metadata automatica (filtros, periodo, etc.) |
| status | String | pendiente, en_revision, resuelto, descartado |
| admin_notes | Text | Notas del admin |
| github_issue_url | String | URL del issue creado |
| created_by | Integer FK | Usuario que envio |
| created_at | DateTime | Automatico |
| updated_at | DateTime | Automatico |

**app_config**
| Columna | Tipo | Descripcion |
|---------|------|-------------|
| key | String PK | Clave de configuracion |
| value | String | Valor |

### Schema de Datos (scripts/schema.sql)

9 tablas para almacenamiento de datos + 11 indices:
- `periodos` — referencia de periodos/fechas
- `sectores_ciiu` — descriptores CIIU
- `empleo_total` — C1.1/C1.2
- `empleo_sectorial` — C3-C7
- `datasets` — metadata
- `remuneraciones` — R1-R4
- `empresas` — E1-E3
- `flujos` — F1-F3
- `genero` — G1-G3

### Inicializacion

```bash
python scripts/init_db.py
```

Crea las tablas ORM (users, feedback, app_config) y solicita interactivamente los datos del primer usuario admin.

---

## 13. CSS y Estilos

**Archivo**: `assets/custom.css` (625 lineas)

### Sistema de Variables

Todas las variables CSS usan el prefijo `--sipa-*`:

```css
--sipa-primary: #1B2A4A;
--sipa-primary-light: #2C5282;
--sipa-success: #276749;
--sipa-danger: #9B2C2C;
--sipa-warning: #975A16;
--sipa-info: #2B6CB0;
--sipa-bg: #F7FAFC;
--sipa-bg-secondary: #EDF2F7;
--sipa-border: #E2E8F0;
--sipa-text: #1A202C;
--sipa-text-muted: #718096;
```

### Clases Principales

- `.sipa-header` — Header institucional
- `.sipa-kpi-card` — Tarjetas de KPI
- `.sipa-card` — Cards genericas
- `.sipa-alert-*` — Alertas por tipo
- `.sipa-btn-*` — Botones
- `.sipa-feedback-btn` — Boton de feedback (absolute positioning)
- `.sipa-footer` — Footer institucional ("Fuente: SIPA | Ministerio de Capital Humano")
- `.sipa-metodo-section` — Secciones de metodologia
- `.admin-section` — Panel admin
- `.status-*` — Estados de feedback (pendiente, en_revision, resuelto, descartado)

### Visibilidad por Rol

El layout principal inyecta `sipa-role-admin` o `sipa-role-viewer` como clase CSS. Esto controla visibilidad:

```css
.sipa-role-viewer .sipa-feedback-btn { display: none !important; }
```

### Responsive

Breakpoint a 768px para adaptacion a dispositivos moviles.

---

## 14. Deploy en Produccion

### Render

El proyecto se despliega en [Render](https://render.com) con:

**Procfile** (raiz del proyecto):
```
web: gunicorn src.app:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

### Variables de Entorno en Render

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | PostgreSQL managed de Render |
| `SECRET_KEY` | Clave segura generada |
| `GITHUB_FEEDBACK_TOKEN` | Token de GitHub (opcional) |
| `PYTHON_VERSION` | `3.11.5` |

### Flujo de Deploy

```bash
git push origin master:main
```

Render detecta el push a `main` y auto-deploya:
1. Instala dependencias desde `requirements.txt`
2. Ejecuta `gunicorn src.app:server` desde Procfile

### PostgreSQL Managed

Render proporciona PostgreSQL managed. La URL se configura automaticamente como `DATABASE_URL`.

---

## 15. Desarrollo Local

### Sin Base de Datos (modo rapido)

```bash
python src/app.py
```

- No necesita PostgreSQL
- Dashboard corre publico con acceso admin completo
- Datos se cargan de archivos locales (Parquet/CSV)
- Ideal para desarrollo de visualizaciones

### Con Base de Datos

```bash
# Opcion 1: PostgreSQL local
DATABASE_URL=postgresql://user:pass@localhost/dbname python src/app.py

# Opcion 2: Conectar a BD remota (Render)
# Configurar DATABASE_URL en .env apuntando a la BD de produccion
python src/app.py
```

Con BD:
- Login habilitado en `/login`
- Roles admin/viewer activos
- Feedback se guarda en BD
- Panel admin funcional

### Agregar una Tab Nueva

1. Crear `src/tabs/nueva_tab.py` con `create_nueva_tab_layout()` y `register_nueva_tab_callbacks(app)`
2. Agregar el tab en `src/layout/main.py` (lista de tabs)
3. Registrar callbacks en `src/callbacks/register.py`
4. Agregar datos necesarios en `src/data/loader.py` si corresponde

### Agregar un Componente con Feedback

```python
from src.layout.feedback_components import graph_with_feedback

# Envolver cualquier componente
graph_with_feedback(
    dcc.Graph(id='mi-grafico', figure=fig),
    graph_id='tab-mi-grafico',
    graph_label='Mi Grafico'
)
```

---

## 16. Testing

### Ejecutar Tests

```bash
pytest tests/
```

### Archivos de Test

| Archivo | Que testea |
|---------|-----------|
| `tests/test_processing.py` | `parse_period_string()`, `process_periods()`, `calculate_variations()`, `filter_by_dates()` |
| `tests/test_cache.py` | Singleton `DataCache`, thread safety |
| `tests/test_loader.py` | Carga de datos desde archivos |
| `tests/test_ingestion.py` | Pipeline de ingesta a BD |
| `tests/test_tabs.py` | Smoke tests: todas las tabs renderizan sin error |

---

## 17. Troubleshooting

### El dashboard no arranca

| Sintoma | Causa probable | Solucion |
|---------|---------------|----------|
| `ModuleNotFoundError` | Dependencias faltantes | `pip install -r requirements.txt` |
| `FileNotFoundError: data/optimized/` | Datos no preprocesados | Ejecutar scripts de preprocess o verificar que `data/processed/` tiene CSVs |
| Error de conexion PostgreSQL | `DATABASE_URL` mal configurada | Verificar URL o ejecutar sin BD |
| Puerto en uso | Otro proceso en 8050 | `PORT=8051 python src/app.py` |

### Problemas de autenticacion

| Sintoma | Causa probable | Solucion |
|---------|---------------|----------|
| No aparece login | `DATABASE_URL` no configurada | Configurar en `.env` y reiniciar |
| "Invalid credentials" | Password incorrecto o usuario no existe | `python scripts/init_db.py` para crear admin |
| `DetachedInstanceError` | Problema de sesion SQLAlchemy | Ya resuelto con `expire_on_commit=False` |

### Problemas de datos

| Sintoma | Causa probable | Solucion |
|---------|---------------|----------|
| Graficos vacios | Datos no cargados | Verificar archivos en `data/optimized/` o `data/processed/` |
| "KeyError" en dataset | Dataset faltante | Ejecutar preprocesamiento del tipo faltante |
| Periodos incorrectos | Excel con formato nuevo | Verificar contra `docs/FORMATO_EXCEL.md` |

### Problemas de deploy

| Sintoma | Causa probable | Solucion |
|---------|---------------|----------|
| Build falla en Render | Dependencia no instalable | Verificar `requirements.txt` |
| Timeout al iniciar | Carga de datos muy lenta | Verificar que Parquet existe (es mucho mas rapido que CSV) |
| 500 en produccion | Variable de entorno faltante | Verificar env vars en Render dashboard |

---

## 18. Historial de Cambios

### v3.0 (2025-2026) — Modularizacion Completa

Refactorizacion total desde el dashboard monolitico:

- **Modularizacion**: `dashboard.py` (2,280 lineas) → modulos en `src/auth/`, `src/tabs/`, `src/callbacks/`, `src/data/`, `src/layout/`
- **Autenticacion**: Flask-Login + PostgreSQL, roles admin/viewer, degradacion graceful
- **Feedback**: Sistema de feedback por componente (31 componentes), almacenamiento en BD + GitHub Issues
- **Admin**: Panel de administracion (feedback, usuarios, configuracion)
- **Pipeline de datos**: Scripts modulares en `scripts/preprocess/` con clase base `ExcelProcessor`
- **Nuevas fuentes**: Remuneraciones (R1-R4), Empresas (E1-E3), Flujos (F1-F3), Genero (G1-G3), IPC
- **Nuevas tabs**: Remuneraciones, Empresas, Flujos, Genero (de 8 a 11 tabs)
- **Deploy**: Migrado de deploy/ subfolder a root con Procfile para Render
- **Tests**: pytest con 5 archivos de tests

### v2.3 (agosto 2025) — Optimizacion

- Conversion a formato Parquet (89% menos espacio, carga <0.1s)
- Dashboard monolitico con 8 vistas
- Datos solo de empleo trimestral (C1-C7)
- Deploy via carpeta `deploy/` con sync manual

### v1.0 (agosto 2025) — Inicial

- Script `preprocesamiento.py` + `dashboard.py`
- Procesamiento de Excel de empleo trimestral
- Dashboard basico con analisis temporal y sectorial
