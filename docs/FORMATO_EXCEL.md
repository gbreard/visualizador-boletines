# Especificación del Formato Excel Esperado

## 📋 Documento de Referencia para Actualizaciones

Este documento describe **EXACTAMENTE** el formato que debe tener el archivo Excel para que el sistema funcione correctamente con nuevas versiones.

## 🔴 CRÍTICO: Estructura General

### Nombre del Archivo
- Patrón recomendado: `nacional_serie_empleo_trimestral_actualizado[FECHA].xlsx`
- Ejemplo: `nacional_serie_empleo_trimestral_actualizado241312.xlsx`

### Hojas Requeridas (OBLIGATORIAS)
El archivo DEBE contener estas 9 hojas con los nombres EXACTOS:
- `C1.1` - Serie temporal con estacionalidad
- `C1.2` - Serie temporal desestacionalizada  
- `C2.1` - Serie por sector con estacionalidad
- `C2.2` - Serie por sector desestacionalizada
- `C3` - Empleo por letra CIIU
- `C4` - Empleo por 2 dígitos CIIU
- `C5` - Empleo por sector y tamaño
- `C6` - Empleo por 3 dígitos CIIU
- `C7` - Empleo por 4 dígitos CIIU

## 📊 Estructura Detallada por Tipo de Hoja

### 1️⃣ HOJAS C1.1 y C1.2 (Series Temporales Simples)

```
Fila 1: [Título del cuadro - IGNORADO]
Fila 2: [Subtítulo - IGNORADO]
Fila 3: Período | Empleo | Var. % interanual | [Var. % trimestral solo en C1.2]
Fila 4: 1º Trim 1996 | 3251846 | -2.0 | [0.5]
Fila 5: 2º Trim 1996 | 3321456 | -1.5 | [2.1]
...
```

**Columnas C1.1:**
- Col A: Período
- Col B: Empleo (valor numérico)
- Col C: Var. % interanual

**Columnas C1.2:**
- Col A: Período
- Col B: Empleo (valor numérico)
- Col C: Var. % trimestral
- Col D: Var. % interanual

### 2️⃣ HOJAS C2.1 y C2.2 (Series por Sector)

```
Fila 1: [Título - IGNORADO]
Fila 2: [Subtítulo - IGNORADO]
Fila 3: Período | Agricultura... | Minería... | Industria | Electricidad... | Construcción | Comercio | Servicios | Total
Fila 4: 1º Trim 1996 | 232639 | 33052 | 879184 | 44277 | 180367 | 517374 | 1509886 | 3396779
...
```

**Columnas (ambas hojas):**
- Col A: Período
- Col B: Agricultura, ganadería y pesca
- Col C: Minería y petróleo (3)
- Col D: Industria
- Col E: Electricidad, gas y agua (3)
- Col F: Construcción
- Col G: Comercio
- Col H: Servicios
- Col I: Total

### 3️⃣ HOJAS C3, C4, C6, C7 (Tablas Sectoriales con Códigos CIIU)

```
Fila 1: [Título - IGNORADO]
Fila 2: [Subtítulo - IGNORADO]
Fila 3: Código | Descripción | 1º Trim 1996 | 2º Trim 1996 | 3º Trim 1996 | ...
Fila 4: A | Agricultura, ganadería... | 123456 | 124567 | 125678 | ...
Fila 5: B | Pesca y servicios conexos | 23456 | 23567 | 23678 | ...
...
```

**Estructura:**
- Col A: Código CIIU (letra para C3, números para C4/C6/C7)
- Col B: Descripción del sector/rama
- Col C en adelante: Períodos con valores de empleo

**Códigos esperados por hoja:**
- **C3**: Letras A hasta O (14 sectores)
- **C4**: Números 1-99 (56 ramas de 2 dígitos)
- **C6**: Números 10-999 (147 ramas de 3 dígitos)
- **C7**: Números 100-9999 (301 ramas de 4 dígitos)

### 4️⃣ HOJA C5 (Estructura Jerárquica Especial)

```
Fila 1: [Título - IGNORADO]
Fila 2: [Subtítulo - IGNORADO]
Fila 3: Sector/Tamaño | 1º Trim 1996 | 2º Trim 1996 | ...
Fila 4: Industria | 884282 | 892050 | ...
Fila 5:   Grandes | 454570 | 450388 | ...
Fila 6:   Medianas | 197134 | 202336 | ...
Fila 7:   Pequeñas | 168144 | 173142 | ...
Fila 8:   Micro | 64434 | 66184 | ...
Fila 9: Comercio | 520178 | 527860 | ...
Fila 10:  Grandes | 162488 | 163931 | ...
...
```

**Categorías válidas:**
- Sectores: `Industria`, `Comercio`, `Servicios`, `Total`
- Tamaños: `Grandes`, `Medianas`, `Pequeñas`, `Micro`

## ⚠️ Elementos Problemáticos que el Sistema Maneja

### 1. Columnas de Comparación
**Problema:** Columnas con formato "2º Trim 2024 / 2º Trim 1998"
**Solución:** El sistema las detecta por el "/" y las excluye automáticamente

### 2. Valores Especiales
**Problema:** Celdas con "s.d.", "sd", "n.d.", "-", "..."
**Solución:** Se convierten a NULL/None automáticamente

### 3. Filas de Notas
**Problema:** Filas al final con "Nota:", "Fuente:", "Aclaración:"
**Solución:** Se detectan por palabras clave y se excluyen

### 4. Filas de Totales
**Problema:** Filas con "Total general" en hojas sectoriales
**Solución:** Se excluyen automáticamente

### 5. Variaciones en Formato de Período
**Formatos aceptados:**
- 1º Trim 2024 ✅
- 1° Trim 2024 ✅
- 1er Trim 2024 ✅
- 2do Trim 2024 ✅
- 3er Trim 2024 ✅
- 4to Trim 2024 ✅

**Se normalizan todos a:** `Nº Trim YYYY`

## 🔍 Validación Pre-Procesamiento

### Script de Validación Rápida
```python
import openpyxl

def validar_excel(archivo):
    """Valida que el Excel tenga la estructura esperada"""
    
    errores = []
    advertencias = []
    
    try:
        wb = openpyxl.load_workbook(archivo, data_only=True)
    except:
        return ["Error: No se puede abrir el archivo Excel"], []
    
    # Verificar hojas requeridas
    hojas_requeridas = ['C1.1', 'C1.2', 'C2.1', 'C2.2', 'C3', 'C4', 'C5', 'C6', 'C7']
    for hoja in hojas_requeridas:
        if hoja not in wb.sheetnames:
            errores.append(f"Falta hoja requerida: {hoja}")
    
    # Verificar estructura básica de cada hoja
    for sheet_name in wb.sheetnames:
        if sheet_name in hojas_requeridas:
            ws = wb[sheet_name]
            
            # Verificar que hay datos
            if ws.max_row < 4:
                errores.append(f"{sheet_name}: Muy pocas filas (< 4)")
            
            # Verificar encabezados en fila 3
            fila3 = [cell.value for cell in ws[3]]
            if all(v is None for v in fila3):
                errores.append(f"{sheet_name}: Fila 3 vacía (esperaba encabezados)")
            
            # Buscar columnas con "/"
            for cell in ws[3]:
                if cell.value and '/' in str(cell.value):
                    advertencias.append(f"{sheet_name}: Columna con '/' encontrada (será excluida)")
    
    wb.close()
    return errores, advertencias

# Usar así:
errores, advertencias = validar_excel('archivo.xlsx')
if errores:
    print("ERRORES CRÍTICOS:")
    for e in errores:
        print(f"  ❌ {e}")
if advertencias:
    print("ADVERTENCIAS:")
    for a in advertencias:
        print(f"  ⚠️ {a}")
if not errores and not advertencias:
    print("✅ Archivo válido para procesamiento")
```

## 📝 Checklist para Nueva Versión del Excel

Antes de procesar un nuevo archivo Excel, verificar:

- [ ] El archivo se abre correctamente en Excel
- [ ] Contiene las 9 hojas con nombres exactos (C1.1, C1.2, etc.)
- [ ] Los encabezados están en la fila 3 de cada hoja
- [ ] La columna A tiene períodos o códigos según el tipo de hoja
- [ ] No hay celdas fusionadas en las áreas de datos
- [ ] Los valores numéricos no tienen formato de texto
- [ ] Los períodos siguen el formato "Nº Trim YYYY"
- [ ] En C3-C7, la columna B tiene las descripciones

## 🚨 Problemas Comunes y Soluciones

| Síntoma | Causa Probable | Solución |
|---------|---------------|----------|
| 0 registros procesados | Encabezados no en fila 3 | Verificar estructura del Excel |
| Faltan descriptores | Columna B vacía en C3-C7 | Agregar descripciones en Excel |
| Períodos incorrectos | Formato no estándar | El sistema normaliza automáticamente |
| Valores como texto | Formato de celda incorrecto | Convertir a número en Excel |
| Hojas no encontradas | Nombres incorrectos | Renombrar a C1.1, C1.2, etc. |

## 💡 Tips para Preparar el Excel

1. **Limpiar formato**: Quitar colores, bordes y formatos especiales
2. **Eliminar hojas extras**: Solo dejar las 9 requeridas
3. **Verificar fórmulas**: Convertir a valores si hay fórmulas
4. **Revisar decimales**: Usar punto (.) como separador decimal
5. **Quitar espacios**: En nombres de hojas y encabezados

## 📊 Ejemplo de Validación Manual

### Para C4 (2 dígitos CIIU):
```
Abrir hoja C4
Verificar:
- Fila 3, Col A: Debe decir algo como "Rama" o "Código"
- Fila 3, Col B: Debe decir algo como "Descripción" o "Actividad"
- Fila 3, Col C: Debe ser un período como "1º Trim 1996"
- Fila 4, Col A: Debe ser un número entre 1 y 99
- Fila 4, Col B: Debe ser una descripción de texto
- Fila 4, Col C: Debe ser un valor numérico
```

---

**IMPORTANTE**: Este documento es la referencia definitiva para el formato del Excel. 
Si el procesamiento falla, verificar PRIMERO que el Excel cumple con estas especificaciones.

*Última actualización: 12 de agosto de 2025*