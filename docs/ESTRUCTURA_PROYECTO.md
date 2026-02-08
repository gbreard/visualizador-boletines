# Estructura del Proyecto - Visualizador de Boletines de Empleo

## Archivos Principales

### 1. Scripts de Procesamiento
- **`preprocesamiento.py`** - Convierte Excel → CSV (NO MODIFICAR - lógica compleja)
- **`preprocesar_csv_a_parquet.py`** - Convierte CSV → Parquet para optimización

### 2. Dashboard
- **`dashboard.py`** - Dashboard principal con 8 vistas interactivas
  - Usa Parquet si existe, sino CSV
  - Diseño completo con todas las funcionalidades

### 3. Documentación
- **`GEMINI.md`** - Documentación técnica completa del proyecto
- **`README.md`** - Guía de instalación y uso
- **`FORMATO_EXCEL.md`** - Especificación del formato Excel esperado
- **`ESTRUCTURA_PROYECTO.md`** - Este archivo

### 4. Datos
- **`nacional_serie_empleo_trimestral_actualizado241312.xlsx`** - Datos fuente originales

## Directorios

### datos_limpios/
Archivos CSV generados por `preprocesamiento.py`:
- C1.1.csv, C1.2.csv - Series temporales con/sin estacionalidad
- C2.1.csv, C2.2.csv - Series temporales adicionales
- C3.csv - Sectores por letra CIIU (14 sectores)
- C4.csv - Ramas 2 dígitos (56 ramas)
- C5.csv - Sector × Tamaño empresa
- C6.csv - Ramas 3 dígitos (147 ramas)
- C7.csv - Ramas 4 dígitos (301 ramas)
- descriptores_CIIU.csv - Tabla maestra de descriptores

### datos_rapidos/
Archivos Parquet optimizados generados por `preprocesar_csv_a_parquet.py`:
- c11.parquet, c12.parquet, etc. - Versiones Parquet de los CSV
- 10-50x más rápidos de leer
- 89% más compactos

### produccion/
Archivos para despliegue en servidor:
- app.py - Wrapper para Gunicorn
- dashboard_original_optimizado.py - Dashboard con diseño original + Parquet
- requirements.txt - Dependencias Python
- render.yaml - Configuración para Render.com
- Copias de datos_rapidos/ y datos_limpios/

## Flujo de Trabajo

```
1. Excel (3.2 MB)
   ↓
2. preprocesamiento.py
   ↓
3. CSV en datos_limpios/ (1.7 MB)
   ↓
4. preprocesar_csv_a_parquet.py
   ↓
5. Parquet en datos_rapidos/ (362 KB)
   ↓
6. dashboard.py (usa Parquet o CSV)
```

## Comandos Útiles

### Procesar datos desde cero:
```bash
# 1. Excel a CSV
python preprocesamiento.py

# 2. CSV a Parquet
python preprocesar_csv_a_parquet.py

# 3. Ejecutar dashboard
python dashboard.py
```

### Desplegar a producción:
```bash
cd produccion
git add -A
git commit -m "Actualización"
git push origin master
```

## Notas Importantes

1. **NO MODIFICAR `preprocesamiento.py`** - Contiene lógica compleja para manejar el formato Excel
2. **OneDrive causa lentitud** - Para desarrollo, copiar proyecto a C:\proyectos\
3. **Parquet es opcional** - El dashboard funciona con CSV si no hay Parquet
4. **Diseño original preservado** - Todas las optimizaciones mantienen el diseño intacto

## Métricas de Performance

| Formato | Tamaño | Tiempo Carga | 
|---------|--------|--------------|
| Excel | 3.2 MB | ~20 segundos |
| CSV | 1.7 MB | ~5 segundos |
| Parquet | 362 KB | <0.1 segundos |

## Estado Actual

✅ Proyecto completamente funcional y optimizado
- 61,790 registros procesados correctamente
- 526 descriptores CIIU preservados
- Dashboard con 8 vistas interactivas
- Performance optimizada con Parquet
- Desplegado en Render.com