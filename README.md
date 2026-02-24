# Visualizador de Boletines de Empleo - Argentina 🇦🇷

Dashboard interactivo para análisis de datos de empleo del Sistema Integrado Previsional Argentino (SIPA).

## 📊 Características

- 8 vistas interactivas de datos de empleo
- Análisis temporal desde 1996 hasta 2024
- Filtros por sector CIIU, tamaño de empresa y período
- Sistema de alertas automáticas
- Datos optimizados con formato Parquet para carga ultra-rápida

## 🚀 Despliegue Rápido

### En Render.com (Recomendado)

1. Fork este repositorio
2. Conecta tu cuenta de GitHub con Render
3. Crea nuevo Web Service
4. Selecciona este repositorio
5. Render detectará automáticamente la configuración

### En Heroku

```bash
heroku create nombre-app
git push heroku main
```

### Local

```bash
pip install -r requirements.txt
python dashboard.py
```

## 📁 Estructura

```
├── dashboard.py         # Aplicación principal
├── app.py              # Wrapper para Gunicorn
├── datos_rapidos/      # Datos optimizados Parquet
├── datos_limpios/      # Datos CSV (backup)
├── requirements.txt    # Dependencias
├── Procfile           # Configuración Heroku/Render
├── render.yaml        # Configuración específica Render
└── runtime.txt        # Versión Python
```

## 🔧 Configuración

- **Python**: 3.11.5
- **Framework**: Dash 2.14.2
- **Datos**: 61,790 registros optimizados
- **Memoria**: ~512MB mínimo

## 📈 Datos Incluidos

- **C1-C2**: Series temporales de empleo
- **C3**: 14 sectores agregados (letra CIIU)
- **C4**: 56 ramas de actividad (2 dígitos)
- **C5**: Análisis por tamaño de empresa
- **C6**: 147 ramas detalladas (3 dígitos)
- **C7**: 301 ramas máximo detalle (4 dígitos)

## 🌐 Variables de Entorno

No requiere configuración adicional. Todo incluido.

## 📝 Licencia

Datos públicos del Ministerio de Trabajo, Empleo y Seguridad Social de Argentina.

---
*Dashboard optimizado para carga instantánea con archivos Parquet*
