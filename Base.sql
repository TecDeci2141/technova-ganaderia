CREATE DATABASE IF NOT EXISTS ganado_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE ganado_db;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    valor_total DECIMAL(12,2) DEFAULT 0,
    fecha_venta DATE,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS potreros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    corral_count INT DEFAULT 0,
    capacidad_por_corral INT DEFAULT 0,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS ganado (
    id INT AUTO_INCREMENT PRIMARY KEY,
    arete VARCHAR(100) UNIQUE,
    sexo VARCHAR(20),
    raza VARCHAR(100),
    fecha_ingreso DATE,
    edad_meses INT,
    peso_inicial_kg DECIMAL(10,2),
    peso_actual_kg DECIMAL(10,2),
    proveedor VARCHAR(150),
    potrero_actual VARCHAR(150),
    alimentacion TEXT,
    destino_carne VARCHAR(100),
    estado VARCHAR(50) DEFAULT 'En Engorda',
    peso_canal DECIMAL(10,2),
    precio_venta DECIMAL(12,2),
    valor_total DECIMAL(12,2),
    fecha_venta DATE
);

CREATE TABLE IF NOT EXISTS historial_peso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    arete VARCHAR(100) NOT NULL,
    fecha_medicion DATE NOT NULL,
    peso_kg DECIMAL(10,2) NOT NULL,
    incremento_kg DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (arete) REFERENCES ganado(arete)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medicamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    ingrediente_activo VARCHAR(150),
    uso TEXT
);

CREATE TABLE IF NOT EXISTS vacunacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    arete VARCHAR(100) NOT NULL,
    medicamento_id INT,
    fecha DATE NOT NULL,
    dosis VARCHAR(100),
    observaciones TEXT,
    FOREIGN KEY (arete) REFERENCES ganado(arete)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ingredientes VARCHAR(255) NOT NULL,
    cantidad DECIMAL(12,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS premezclas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    ingredientes TEXT,
    cantidad DECIMAL(12,2) DEFAULT 0,
    unidad VARCHAR(30) DEFAULT 'kg',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT
);

CREATE INDEX idx_ganado_estado ON ganado(estado);
CREATE INDEX idx_ganado_potrero ON ganado(potrero_actual);
CREATE INDEX idx_historial_arete_fecha ON historial_peso(arete, fecha_medicion);
CREATE INDEX idx_vacunacion_fecha ON vacunacion(fecha);
CREATE INDEX idx_ventas_fecha ON ventas(fecha_venta);
