# 🚀 GUÍA DE INICIO RÁPIDO

## 1️⃣ EJECUTAR DASHBOARD (30 segundos)

### Opción A: Super Fácil
**Doble clic en:** `ejecutar_local.bat`

### Opción B: Terminal
```bash
cd src
python dashboard.py
```

**Abrir navegador:** http://localhost:8050

---

## 2️⃣ HACER CAMBIOS

### Editar Dashboard
📝 Archivo: `src/dashboard.py`

### Probar Cambios
- Guardar archivo
- Refrescar navegador (F5)
- ¡Listo!

---

## 3️⃣ SUBIR A PRODUCCIÓN

**Doble clic en:** `sincronizar.bat`

El script:
1. ✅ Detecta cambios
2. ✅ Pide confirmación
3. ✅ Sube a GitHub
4. ✅ Render despliega automático

---

## 📁 ARCHIVOS IMPORTANTES

```
ejecutar_local.bat    → Ejecutar dashboard
sincronizar.bat       → Subir a producción
src/dashboard.py      → Código del dashboard
data/                 → Todos los datos
```

---

## ❓ AYUDA RÁPIDA

### Dashboard no abre
```bash
pip install -r requirements.txt
```

### Puerto ocupado
```bash
# Cambiar puerto
cd src
python dashboard.py --port 8051
```

### Actualizar datos
```bash
cd src
python preprocesamiento.py
python preprocesar_csv_a_parquet.py
```

---

## 📊 NAVEGACIÓN DEL DASHBOARD

### Pestañas Disponibles
1. **Vista General** - Resumen ejecutivo
2. **Análisis Temporal** - Gráficos de tiempo
3. **Análisis Sectorial** - Por sector CIIU
4. **Por Tamaño** - Micro/Pequeña/Mediana/Grande
5. **Comparaciones** - Entre períodos
6. **Alertas** - Anomalías automáticas
7. **Datos Crudos** - Tabla completa
8. **Metodología** - Documentación

### Controles
- 📅 **Selector fechas** - Arriba
- 📈 **Tipo métrica** - Niveles/Var%/Índice
- 📊 **Serie base** - Con/sin estacionalidad

---

## 🔄 FLUJO TÍPICO

```
1. Abrir: ejecutar_local.bat
2. Editar: src/dashboard.py
3. Probar: http://localhost:8050
4. Subir: sincronizar.bat
```

---

## 💡 TIPS

- **Desarrollo**: Editar siempre en `src/`
- **Datos**: Parquet es 100x más rápido que Excel
- **Deploy**: Render actualiza automático al push
- **Backup**: Se crea automático al sincronizar

---

**¿Necesitas más ayuda?** 
Ver [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md)

---

*Dashboard listo en 30 segundos* ⚡