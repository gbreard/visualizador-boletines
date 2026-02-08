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

-- Indices para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_empleo_total_periodo ON empleo_total(periodo_id);
CREATE INDEX IF NOT EXISTS idx_empleo_total_serie ON empleo_total(serie);
CREATE INDEX IF NOT EXISTS idx_empleo_sectorial_periodo ON empleo_sectorial(periodo_id);
CREATE INDEX IF NOT EXISTS idx_empleo_sectorial_tabla ON empleo_sectorial(tabla_origen);
CREATE INDEX IF NOT EXISTS idx_periodos_fecha ON periodos(fecha);
