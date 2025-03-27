import pandas as pd
import numpy as np
import re
import os
from typing import List, Dict, Tuple, Optional, Union

# ------------------------------------------------------------------------------
# 1) Funciones para homogeneizar y limpiar los datos
# ------------------------------------------------------------------------------

def unify_period_string(period_str: str) -> str:
    """
    Unifica variaciones del texto del período a un formato estándar.
    Ejemplos:
      - "1er Trim 1996" -> "1º Trim 1996"
      - "2do Trim 2020" -> "2º Trim 2020"
      - "3° trim 2023" -> "3º Trim 2023"
    """
    if pd.isna(period_str):
        return ""
    
    p = str(period_str).strip()
    
    # Reemplazos comunes para números ordinales
    p = re.sub(r"1er\s+trim", "1º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"2do\s+trim", "2º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"3er\s+trim", "3º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"4to\s+trim", "4º Trim", p, flags=re.IGNORECASE)
    
    # Manejar variantes con grado (°)
    p = re.sub(r"1°\s+trim", "1º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"2°\s+trim", "2º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"3°\s+trim", "3º Trim", p, flags=re.IGNORECASE)
    p = re.sub(r"4°\s+trim", "4º Trim", p, flags=re.IGNORECASE)
    
    # Uniformar "trim" (asegurarse que sea "Trim" con T mayúscula)
    p = re.sub(r"\btrim\b", "Trim", p, flags=re.IGNORECASE)
    
    # Eliminar espacios dobles
    p = re.sub(r"\s+", " ", p)
    
    # Asegurarse que no hay espacio antes del asterisco (para casos como "3° trim 2024*")
    p = p.replace(" *", "*")
    
    return p

def clean_footnotes(df: pd.DataFrame, periodo_col="Período") -> pd.DataFrame:
    """
    Limpia el DataFrame:
      - Unifica el formato del Período.
      - Descarta filas cuyo valor en Período no sea exactamente un trimestre válido.
      - Si existe la columna "Valor", se descartan filas en las que ese valor no sea numérico.
      - Filtra filas que contengan palabras clave típicas de notas.
      
    Se considera un período válido si tiene un formato como:
       "1º Trim YYYY", "2° Trim YYYY", etc., incluyendo posibles variantes.
    """
    if periodo_col not in df.columns:
        return df

    # 1) Unificar el texto en la columna de período
    df[periodo_col] = df[periodo_col].astype(str).apply(unify_period_string)
    
    # 2) Expresión regular para detectar períodos válidos (más permisiva)
    pattern_periodo = re.compile(r"^[1-4][°º]\s*Trim\s+\d{4}(\*)?$", re.IGNORECASE)
    mask_periodo_valido = df[periodo_col].str.match(pattern_periodo)
    
    # 3) Descartar filas que tengan palabras clave de notas y aclaraciones
    keywords = ["nota", "fuente", "variación", "observación", 
                "comentario", "disclaimer", "empresas", "desocup",
                "aclaración", "volver", "índice"]
    pattern_keywords = re.compile("|".join(keywords), re.IGNORECASE)
    mask_no_keywords = ~df[periodo_col].str.contains(pattern_keywords, na=False)
    
    # 4) Si existe la columna "Valor", verificar que sea numérica
    if "Valor" in df.columns:
        mask_valor_numeric = pd.to_numeric(df["Valor"], errors="coerce").notnull()
    else:
        mask_valor_numeric = True
    
    # 5) Combinar todas las máscaras
    mask_total = mask_periodo_valido & mask_no_keywords & mask_valor_numeric
    
    df_limpio = df[mask_total].copy()
    return df_limpio

# ------------------------------------------------------------------------------
# 2) Funciones para detectar la estructura de las hojas
# ------------------------------------------------------------------------------

def detect_sheet_structure(file_path: str, sheet_name: str) -> str:
    """
    Detecta si una hoja tiene estructura vertical (Período en filas) 
    u horizontal (Período en columnas).
    
    Retorna: "vertical", "horizontal", o "unknown"
    """
    try:
        # Leer las primeras filas para analizar
        df_sample = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=10)
        
        # Buscar palabras clave en las primeras filas
        for i in range(min(5, len(df_sample))):
            row = df_sample.iloc[i].astype(str)
            row_text = ' '.join(row.values)
            
            # Verificar si "Período" está en la primera columna (vertical)
            if "Período" in str(row[0]):
                return "vertical"
                
            # Buscar patrones de períodos trimestrales en los encabezados (horizontal)
            trim_pattern = re.compile(r"[1-4][°º]\s*Trim\s+\d{4}", re.IGNORECASE)
            if any(trim_pattern.search(str(val)) for val in row.values[1:]):
                return "horizontal"
        
        # Verificar si hay "Sector" o "Rama de actividad" en las primeras columnas (horizontal)
        for i in range(min(5, len(df_sample))):
            if df_sample.iloc[i, 0] is not None:
                val = str(df_sample.iloc[i, 0]).lower().strip()
                if "sector" in val or "rama de actividad" in val or "categoría" in val:
                    return "horizontal"
        
        # Si no se puede determinar con certeza
        return "unknown"
    except Exception as e:
        print(f"Error detectando estructura de {sheet_name}: {e}")
        return "unknown"

def find_header_row(file_path: str, sheet_name: str) -> int:
    """
    Encuentra la fila que contiene los encabezados en la hoja.
    Retorna el índice de la fila de encabezados (0-based).
    """
    try:
        # Leer las primeras filas
        df_sample = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=15)
        
        # Buscar fila con "Período" o patrones trimestrales
        periodo_pattern = re.compile(r"Período", re.IGNORECASE)
        trim_pattern = re.compile(r"[1-4][°º]\s*Trim\s+\d{4}", re.IGNORECASE)
        
        for i in range(len(df_sample)):
            row = df_sample.iloc[i].astype(str)
            
            # Si encontramos "Período" en esta fila
            if any(periodo_pattern.search(str(val)) for val in row.values):
                return i
            
            # Si encontramos patrones de trimestres en las columnas después de la primera
            if i > 0 and any(trim_pattern.search(str(val)) for val in row.values[1:]):
                # Verificar si la fila anterior contiene "Sector" o similar
                prev_row = df_sample.iloc[i-1].astype(str)
                sector_pattern = re.compile(r"Sector|Rama|Categoría", re.IGNORECASE)
                if any(sector_pattern.search(str(val)) for val in prev_row.values):
                    return i - 1
                return i
        
        # Si no encontramos un patrón claro, usar fila 2 (índice 2) como valor predeterminado
        return 2
    except Exception as e:
        print(f"Error encontrando fila de encabezados en {sheet_name}: {e}")
        return 2  # Valor predeterminado

# ------------------------------------------------------------------------------
# 3) Funciones para extraer metadatos y procesar hojas
# ------------------------------------------------------------------------------

def extract_metadata(file_path: str, sheet_name: str) -> dict:
    """
    Lee las primeras filas de la hoja y extrae título y subtítulo.
    """
    try:
        # Leer las primeras 5 filas para buscar metadatos
        df_header = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=5)
        
        # Inicializar valores
        titulo = ""
        subtitulo = ""
        
        # Buscar título y subtítulo en las primeras filas
        if len(df_header) > 0 and len(df_header.columns) > 0:
            # El título suele estar en la primera celda de la primera fila
            val_titulo = df_header.iloc[0, 0]
            if pd.notna(val_titulo) and str(val_titulo).strip():
                titulo = str(val_titulo).strip()
                
            # Buscar subtítulo en la segunda fila
            if len(df_header) > 1:
                val_subtitulo = df_header.iloc[1, 0]
                if pd.notna(val_subtitulo) and str(val_subtitulo).strip():
                    subtitulo = str(val_subtitulo).strip()
        
        # Extraer información adicional del título y subtítulo
        sheet_type = "No especificado"
        if "desestacionalizada" in subtitulo.lower():
            sheet_type = "Desestacionalizada"
        elif "con estacionalidad" in subtitulo.lower():
            sheet_type = "Con estacionalidad"
        
        return {
            "Sheet": sheet_name,
            "Titulo": titulo,
            "Subtitulo": subtitulo,
            "TipoSerie": sheet_type
        }
    except Exception as e:
        print(f"Error al leer metadatos de {sheet_name}: {e}")
        return {
            "Sheet": sheet_name,
            "Titulo": "",
            "Subtitulo": "",
            "TipoSerie": "No especificado"
        }

def process_vertical_sheet(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Procesa hojas verticales (donde el período está en la primera columna).
    Detecta automáticamente la fila de encabezados.
    """
    try:
        # Encontrar la fila de encabezados
        header_row = find_header_row(file_path, sheet_name)
        
        # Leer una muestra para determinar columnas útiles
        df_sample = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row, nrows=5)
        valid_cols = [col for col in df_sample.columns 
                     if not (isinstance(col, str) and "Volver al índice" in col)]
        
        # Leer la hoja completa usando solo las columnas válidas
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row, usecols=valid_cols)
        
        # Renombrar la primera columna a "Período" si tiene otro nombre
        if len(df.columns) > 0 and df.columns[0] != "Período":
            df = df.rename(columns={df.columns[0]: "Período"})
        
        # Convertir tipos de datos para optimizar memoria
        if "Período" in df.columns:
            df["Período"] = df["Período"].astype(str).str.strip()
        
        # Agregar columna de fuente
        df["Fuente"] = sheet_name
        
        # Agregar clasificación de la hoja basada en su nombre
        if sheet_name in ["C1.1", "C1.2"]:
            df["TipoSerie"] = "Total"
        elif sheet_name in ["C2.1", "C2.2"]:
            df["TipoSerie"] = "Grandes divisiones"
        else:
            df["TipoSerie"] = "Otra"
        
        return df
    except Exception as e:
        print(f"Error procesando hoja vertical {sheet_name}: {e}")
        # Devolver DataFrame vacío en caso de error
        return pd.DataFrame(columns=["Período", "Fuente", "TipoSerie"])

def process_horizontal_sheet(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Procesa hojas horizontales (donde el período está en los encabezados de columnas).
    Detecta automáticamente la fila de encabezados.
    """
    try:
        # Encontrar la fila de encabezados
        header_row = find_header_row(file_path, sheet_name)
        
        # Leer una muestra para determinar columnas útiles
        df_sample = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row, nrows=5)
        valid_cols = [col for col in df_sample.columns 
                     if not (isinstance(col, str) and "Volver al índice" in col)]
        
        # Leer la hoja completa usando solo las columnas válidas
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row, usecols=valid_cols)
        
        # Identificar la primera columna (debería ser el sector o categoría)
        first_col = df.columns[0]
        categoria_col = "Categoría"
        
        # Renombrar la primera columna si es necesario
        if first_col != categoria_col:
            if pd.isna(first_col) or (isinstance(first_col, str) and first_col.strip() == ""):
                df = df.rename(columns={first_col: categoria_col})
            else:
                categoria_col = first_col
        
        # Eliminar filas donde la categoría es nula o vacía
        df = df[df[categoria_col].notna() & (df[categoria_col] != "")]
        
        # Procesamiento por lotes para evitar MemoryError
        result_chunks = []
        chunk_size = 50  # Ajustar según memoria disponible
        
        for i in range(0, len(df), chunk_size):
            try:
                chunk = df.iloc[i:i+chunk_size].copy()
                # Convertir de formato ancho a largo (melt)
                chunk_long = chunk.melt(id_vars=[categoria_col], var_name="Período", value_name="Valor")
                
                # Filtrar valores nulos o vacíos
                chunk_long = chunk_long[chunk_long["Valor"].notna()]
                
                # Agregar metadatos
                chunk_long["Fuente"] = sheet_name
                
                # Clasificar según la hoja
                if sheet_name == "C3":
                    chunk_long["NivelDetalle"] = "Letra CIIU"
                elif sheet_name == "C4":
                    chunk_long["NivelDetalle"] = "2 dígitos CIIU"
                elif sheet_name == "C6":
                    chunk_long["NivelDetalle"] = "3 dígitos CIIU"
                elif sheet_name == "C7":
                    chunk_long["NivelDetalle"] = "4 dígitos CIIU"
                elif sheet_name == "C5":
                    chunk_long["NivelDetalle"] = "Tamaño empresa"
                else:
                    chunk_long["NivelDetalle"] = "Otro"
                
                result_chunks.append(chunk_long)
            except Exception as e:
                print(f"Error procesando lote {i} de {sheet_name}: {e}")
                continue
        
        if result_chunks:
            return pd.concat(result_chunks, ignore_index=True)
        else:
            return pd.DataFrame(columns=[categoria_col, "Período", "Valor", "Fuente", "NivelDetalle"])
    except Exception as e:
        print(f"Error procesando hoja horizontal {sheet_name}: {e}")
        return pd.DataFrame(columns=["Categoría", "Período", "Valor", "Fuente", "NivelDetalle"])

# ------------------------------------------------------------------------------
# 4) Funciones para procesar los descriptores de actividad
# ------------------------------------------------------------------------------

def process_descriptores(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Procesa la hoja de descriptores de actividad.
    Intenta extraer códigos y descripciones de CIIU.
    """
    try:
        # Detectar estructura de la hoja y encabezados
        header_row = find_header_row(file_path, sheet_name)
        
        # Leer la hoja completa
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
        
        # Preparar para extraer códigos y descripciones
        descriptores = []
        
        # Procesar filas con contenido relevante
        for _, row in df.iterrows():
            # Tomar solo la primera columna que debería contener el código y descripción
            if len(row) > 0 and pd.notna(row[0]):
                cell_value = str(row[0]).strip()
                
                # Saltar filas de encabezado o vacías
                if not cell_value or "Descriptor" in cell_value or "CIIU" in cell_value:
                    continue
                
                # Intentar extraer código y descripción
                match = re.match(r"^([A-Z0-9]+)[,\s-]+(.+)$", cell_value)
                
                if match:
                    codigo = match.group(1).strip()
                    descripcion = match.group(2).strip()
                    descriptores.append({
                        "Codigo": codigo,
                        "Descripcion": descripcion
                    })
        
        # Crear DataFrame con los resultados
        if descriptores:
            return pd.DataFrame(descriptores)
        else:
            return pd.DataFrame(columns=["Codigo", "Descripcion"])
    except Exception as e:
        print(f"Error procesando descriptores: {e}")
        return pd.DataFrame(columns=["Codigo", "Descripcion"])

# ------------------------------------------------------------------------------
# 5) Script principal de preprocesamiento
# ------------------------------------------------------------------------------

def main_preprocessing():
    """
    Función principal que ejecuta todo el proceso de preprocesamiento.
    """
    # Configuración para reducir uso de memoria
    pd.options.mode.chained_assignment = None  
    
    # Ruta al archivo Excel
    file_path = "nacional_serie_empleo_trimestral_actualizado241312.xlsx"
    
    # Crear directorio de salida si no existe
    output_dir = "datos_procesados"
    os.makedirs(output_dir, exist_ok=True)
    
    # Obtener lista de hojas del Excel
    xl = pd.ExcelFile(file_path)
    all_sheets = xl.sheet_names
    
    # Excluir hojas que no contienen datos relevantes
    excluded_sheets = ["Carátula", "Indice"]
    sheets_to_process = [s for s in all_sheets if s not in excluded_sheets]
    
    # Listas para almacenar resultados
    vertical_dfs = []
    horizontal_dfs = []
    metadata_list = []
    
    # Procesar cada hoja
    print(f"Comenzando preprocesamiento del archivo: {file_path}")
    print(f"Total de hojas a procesar: {len(sheets_to_process)}")
    
    for sheet_name in sheets_to_process:
        print(f"\nProcesando hoja: {sheet_name}")
        
        # Extraer metadatos
        metadata = extract_metadata(file_path, sheet_name)
        metadata_list.append(metadata)
        
        # Si es la hoja de descriptores, procesarla de forma especial
        if "Descriptores" in sheet_name:
            print("  Procesando descriptores de actividad...")
            df_descriptores = process_descriptores(file_path, sheet_name)
            if not df_descriptores.empty:
                output_path = os.path.join(output_dir, "descriptores_actividad.csv")
                df_descriptores.to_csv(output_path, index=False)
                print(f"  ✓ Guardado: {output_path} ({len(df_descriptores)} registros)")
            continue
        
        # Detectar estructura de la hoja
        structure = detect_sheet_structure(file_path, sheet_name)
        print(f"  Estructura detectada: {structure}")
        
        # Procesar según la estructura
        if structure == "vertical":
            df = process_vertical_sheet(file_path, sheet_name)
            if not df.empty:
                vertical_dfs.append(df)
                print(f"  ✓ Procesada: {len(df)} filas")
            else:
                print("  ✗ No se obtuvieron datos")
        
        elif structure == "horizontal":
            df = process_horizontal_sheet(file_path, sheet_name)
            if not df.empty:
                horizontal_dfs.append(df)
                print(f"  ✓ Procesada: {len(df)} filas")
            else:
                print("  ✗ No se obtuvieron datos")
        
        else:
            print("  ✗ No se pudo determinar la estructura, omitiendo")
    
    # Concatenar y limpiar los datos
    print("\nConcatenando y limpiando datos...")
    
    # Datos verticales (series temporales)
    if vertical_dfs:
        df_vertical_combined = pd.concat(vertical_dfs, ignore_index=True)
        df_vertical_clean = clean_footnotes(df_vertical_combined, "Período")
        
        output_path = os.path.join(output_dir, "series_temporales.csv")
        df_vertical_clean.to_csv(output_path, index=False)
        print(f"  ✓ Series temporales guardadas: {output_path} ({len(df_vertical_clean)} filas)")
    else:
        print("  ! No hay datos verticales para guardar")
    
    # Datos horizontales (sectoriales)
    if horizontal_dfs:
        df_horizontal_combined = pd.concat(horizontal_dfs, ignore_index=True)
        df_horizontal_clean = clean_footnotes(df_horizontal_combined, "Período")
        
        output_path = os.path.join(output_dir, "datos_sectoriales.csv")
        df_horizontal_clean.to_csv(output_path, index=False)
        print(f"  ✓ Datos sectoriales guardados: {output_path} ({len(df_horizontal_clean)} filas)")
    else:
        print("  ! No hay datos horizontales para guardar")
    
    # Guardar metadatos
    df_metadata = pd.DataFrame(metadata_list)
    output_path = os.path.join(output_dir, "metadatos.csv")
    df_metadata.to_csv(output_path, index=False)
    print(f"  ✓ Metadatos guardados: {output_path}")
    
    print("\n¡Preprocesamiento completado con éxito!")
    print(f"Los archivos procesados se encuentran en el directorio: {output_dir}")
    
    # Retornar rutas de los archivos generados para uso posterior
    return {
        "series_temporales": os.path.join(output_dir, "series_temporales.csv") if vertical_dfs else None,
        "datos_sectoriales": os.path.join(output_dir, "datos_sectoriales.csv") if horizontal_dfs else None,
        "descriptores": os.path.join(output_dir, "descriptores_actividad.csv"),
        "metadatos": os.path.join(output_dir, "metadatos.csv")
    }

if __name__ == "__main__":
    try:
        main_preprocessing()
    except Exception as e:
        print(f"Error en el script principal: {e}")