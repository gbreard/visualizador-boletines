# 📊 Visualizador de Boletines de Empleo - Argentina

> Sistema integral de análisis y visualización de datos de empleo del SIPA  
> **Estado**: ✅ En Producción | **Versión**: 2.3 | **Datos**: 1996-2024

## 🚀 Inicio Rápido

### Ejecutar Dashboard (3 pasos)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ir a la carpeta src
cd src

# 3. Ejecutar dashboard
python dashboard.py
```

**O simplemente:** Doble clic en `ejecutar_local.bat`

Abrir navegador en: **http://localhost:8050**

## 📸 Capturas

### Dashboard Principal
- 8 vistas interactivas
- 61,790 registros procesados
- Filtros dinámicos por fecha y sector
- Sistema de alertas automáticas

## 🎯 Características Principales

| Característica | Descripción |
|---------------|-------------|
| **📈 Series Temporales** | 28 años de datos (1996-2024) |
| **🏭 Análisis Sectorial** | 14 sectores principales + 301 ramas detalladas |
| **📏 Análisis por Tamaño** | Micro, Pequeña, Mediana, Grande empresa |
| **⚡ Performance** | Carga en <1 segundo con Parquet |
| **🚨 Alertas** | Detección automática de anomalías |
| **📊 Exportación** | Descarga en CSV, gráficos en PNG |

## 📁 Estructura del Proyecto

```
├── src/                  # 💻 Código fuente (desarrollo)
├── data/                 # 📊 Datos (raw/processed/optimized)
├── deploy/               # 🚀 Producción (GitHub)
├── docs/                 # 📚 Documentación completa
├── ejecutar_local.bat    # ▶️ Ejecutar dashboard
└── sincronizar.bat       # 🔄 Sincronizar a producción
```

## 🔧 Desarrollo

### Flujo de Trabajo

1. **Editar** → `src/dashboard.py`
2. **Probar** → `ejecutar_local.bat`
3. **Sincronizar** → `sincronizar.bat`
4. **Deploy automático** → Render.com

### Actualizar Datos

```bash
# 1. Colocar Excel en data/raw/
# 2. Procesar datos
cd src
python preprocesamiento.py
python preprocesar_csv_a_parquet.py

# 3. Sincronizar a producción
cd ..
sincronizar.bat
```

## 📊 Datos Procesados

- **Fuente**: Sistema Integrado Previsional Argentino (SIPA)
- **Período**: 1º Trimestre 1996 - 2º Trimestre 2024
- **Registros**: 61,790
- **Sectores CIIU**: 526 descriptores
- **Actualización**: Trimestral

## 🌐 Despliegue

### GitHub
```bash
cd deploy
git push origin master
```

### Render.com
- Deploy automático al detectar cambios en GitHub
- URL producción: [Configurar en Render]

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md) | 📖 Documentación exhaustiva (15 secciones) |
| [FLUJO_DESARROLLO.md](FLUJO_DESARROLLO.md) | 🔄 Guía desarrollo y producción |
| [docs/GEMINI.md](docs/GEMINI.md) | 🔧 Documentación técnica detallada |
| [docs/FORMATO_EXCEL.md](docs/FORMATO_EXCEL.md) | 📋 Especificación formato datos |

## 🛠️ Tecnologías

- **Python 3.11.5** - Backend
- **Dash 2.14.2** - Framework web
- **Plotly 5.18.0** - Visualizaciones
- **Pandas 2.1.4** - Procesamiento datos
- **Parquet** - Optimización almacenamiento

## ⚡ Performance

| Métrica | Valor |
|---------|-------|
| Tiempo de carga | <1 segundo |
| Tamaño optimizado | 362 KB (vs 3.2 MB original) |
| Compresión | 89% |
| Memoria RAM | ~50 MB |

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama (`git checkout -b feature/NuevaCaracteristica`)
3. Commit cambios (`git commit -m 'Agregar característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abrir Pull Request

## 📝 Licencia

- **Código**: Open Source
- **Datos**: Públicos del Ministerio de Trabajo, Empleo y Seguridad Social

## 🆘 Soporte

- 📚 Ver [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md)
- 🐛 Reportar issues en [GitHub](https://github.com/gbreard/visualizador-boletines/issues)
- ❓ FAQ en la sección 14 de la documentación

---

**Desarrollado para el análisis de datos de empleo en Argentina** 🇦🇷

*Última actualización: 13 de agosto de 2025*