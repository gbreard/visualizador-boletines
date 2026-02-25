# Inicio Rapido

## Ejecutar el Dashboard

```bash
# 1. Instalar dependencias (una vez)
pip install -r requirements.txt

# 2. Arrancar
python src/app.py

# 3. Abrir http://localhost:8050
```

El dashboard carga todos los datos al iniciar y queda listo en segundos.

## Modo Desarrollo vs Produccion

| Modo | Cuando | Autenticacion | Acceso |
|------|--------|---------------|--------|
| **Desarrollo** | Sin `DATABASE_URL` | Deshabilitada | Admin publico completo |
| **Produccion** | Con `DATABASE_URL` | Flask-Login activo | Login requerido, roles admin/viewer |

Para desarrollo de visualizaciones, no necesitas base de datos. Solo ejecuta `python src/app.py`.

## Navegacion

El dashboard tiene 11 pestanas:

1. **Resumen** — KPIs ejecutivos de todas las fuentes
2. **Analisis** — Empleo temporal, sectorial y por tamano
3. **Remuneraciones** — Salarios nominales y reales
4. **Empresas** — Cantidad de empresas
5. **Flujos** — Altas, bajas, creacion neta
6. **Genero** — Empleo por genero y brecha salarial
7. **Comparaciones** — Periodo A vs B
8. **Alertas** — Deteccion de anomalias
9. **Datos** — Explorador con descarga CSV
10. **Metodologia** — Referencia metodologica
11. **Admin** — Panel de administracion (solo admin)

## Setup con Base de Datos (opcional)

Solo necesario si quieres autenticacion, feedback y panel admin:

```bash
# 1. Configurar variable de entorno
export DATABASE_URL=postgresql://user:pass@host/dbname

# 2. Inicializar BD + crear primer admin
python scripts/init_db.py

# 3. Arrancar
python src/app.py
```

## Archivos Clave

| Archivo | Que hace |
|---------|---------|
| `src/app.py` | Entry point del dashboard |
| `src/tabs/` | Las 11 pestanas (un archivo por tab) |
| `src/auth/` | Sistema de autenticacion |
| `src/callbacks/` | Logica interactiva (14 grupos) |
| `src/data/` | Carga y cacheo de datos |
| `src/layout/` | Componentes UI (KPIs, feedback, layout) |
| `assets/custom.css` | Estilos institucionales OEDE |
| `scripts/` | Descarga, preprocesamiento, init BD |

## Documentacion Detallada

- [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md) — Referencia tecnica completa
- [FLUJO_DESARROLLO.md](FLUJO_DESARROLLO.md) — Workflow desarrollo → produccion
- [docs/ESTRUCTURA_PROYECTO.md](docs/ESTRUCTURA_PROYECTO.md) — Arbol de archivos
- [INDICE_DOCUMENTACION.md](INDICE_DOCUMENTACION.md) — Indice de todos los docs
