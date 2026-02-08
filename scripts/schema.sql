-- Schema para el Visualizador de Boletines de Empleo
-- Compatible con PostgreSQL (Neon free tier)

CREATE TABLE IF NOT EXISTS periodos (
    id SERIAL PRIMARY KEY,
    periodo_texto VARCHAR(20) UNIQUE NOT NULL,
    anio SMALLINT NOT NULL,
    trimestre SMALLINT NOT NULL,
    fecha DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS sectores_ciiu (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL,
    descripcion TEXT NOT NULL,
    nivel VARCHAR(20) NOT NULL,
    tabla_origen VARCHAR(5) NOT NULL,
    UNIQUE(codigo, tabla_origen)
);

CREATE TABLE IF NOT EXISTS empleo_total (
    id SERIAL PRIMARY KEY,
    periodo_id INTEGER REFERENCES periodos(id),
    serie VARCHAR(10) NOT NULL,
    sector VARCHAR(50),
    empleo REAL,
    var_trim REAL,
    var_interanual REAL,
    UNIQUE(periodo_id, serie, sector)
);

CREATE TABLE IF NOT EXISTS empleo_sectorial (
    id SERIAL PRIMARY KEY,
    periodo_id INTEGER REFERENCES periodos(id),
    tabla_origen VARCHAR(5) NOT NULL,
    codigo_sector VARCHAR(50) NOT NULL,
    empleo REAL,
    UNIQUE(periodo_id, tabla_origen, codigo_sector)
);

-- Tabla de metadata de fuentes
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    frecuencia VARCHAR(20) NOT NULL,
    ultima_actualizacion TIMESTAMP,
    registros INTEGER DEFAULT 0
);

-- Remuneraciones (mensual)
CREATE TABLE IF NOT EXISTS remuneraciones (
    id SERIAL PRIMARY KEY,
    periodo_texto VARCHAR(30) NOT NULL,
    fecha DATE NOT NULL,
    sector VARCHAR(10),
    remuneracion_promedio REAL,
    remuneracion_mediana REAL,
    UNIQUE(periodo_texto, sector)
);

-- Empresas (anual)
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    anio SMALLINT NOT NULL,
    sector VARCHAR(10),
    tamano VARCHAR(30),
    cantidad REAL,
    UNIQUE(anio, sector, tamano)
);

-- Flujos de empleo (trimestral)
CREATE TABLE IF NOT EXISTS flujos (
    id SERIAL PRIMARY KEY,
    periodo_id INTEGER REFERENCES periodos(id),
    sector VARCHAR(10),
    altas REAL,
    bajas REAL,
    creacion_neta REAL,
    empleo_total REAL,
    tasa_entrada REAL,
    tasa_salida REAL,
    tasa_rotacion REAL,
    UNIQUE(periodo_id, sector)
);

-- Empleo por genero (trimestral)
CREATE TABLE IF NOT EXISTS genero (
    id SERIAL PRIMARY KEY,
    periodo_texto VARCHAR(30) NOT NULL,
    fecha DATE NOT NULL,
    sexo VARCHAR(10) NOT NULL,
    sector VARCHAR(50),
    empleo REAL,
    remuneracion REAL,
    brecha REAL,
    UNIQUE(periodo_texto, sexo, sector)
);

-- Indices para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_empleo_total_periodo ON empleo_total(periodo_id);
CREATE INDEX IF NOT EXISTS idx_empleo_total_serie ON empleo_total(serie);
CREATE INDEX IF NOT EXISTS idx_empleo_sectorial_periodo ON empleo_sectorial(periodo_id);
CREATE INDEX IF NOT EXISTS idx_empleo_sectorial_tabla ON empleo_sectorial(tabla_origen);
CREATE INDEX IF NOT EXISTS idx_periodos_fecha ON periodos(fecha);
CREATE INDEX IF NOT EXISTS idx_remuneraciones_fecha ON remuneraciones(fecha);
CREATE INDEX IF NOT EXISTS idx_remuneraciones_sector ON remuneraciones(sector);
CREATE INDEX IF NOT EXISTS idx_empresas_anio ON empresas(anio);
CREATE INDEX IF NOT EXISTS idx_flujos_periodo ON flujos(periodo_id);
CREATE INDEX IF NOT EXISTS idx_genero_fecha ON genero(fecha);
CREATE INDEX IF NOT EXISTS idx_genero_sexo ON genero(sexo);
