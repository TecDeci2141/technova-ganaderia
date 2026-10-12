import sqlite3

DB_NAME = "ganado.db"

# Conectar / crear la base de datos
conexion = sqlite3.connect(DB_NAME)
cursor = conexion.cursor()

# Activar llaves foráneas
cursor.execute("PRAGMA foreign_keys = ON")

# ============================================================
# ELIMINAR TABLAS EXISTENTES
# ============================================================

cursor.execute("DROP TABLE IF EXISTS vacunacion")
cursor.execute("DROP TABLE IF EXISTS historial_peso")
cursor.execute("DROP TABLE IF EXISTS ganado")
cursor.execute("DROP TABLE IF EXISTS inventario")
cursor.execute("DROP TABLE IF EXISTS medicamentos")
cursor.execute("DROP TABLE IF EXISTS potreros")
cursor.execute("DROP TABLE IF EXISTS ventas")
cursor.execute("DROP TABLE IF EXISTS usuarios")


# ============================================================
# 1. USUARIOS
# ============================================================

cursor.execute("""
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    nombre_completo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")


# ============================================================
# 2. VENTAS
# ============================================================

cursor.execute("""
CREATE TABLE ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    valor_total REAL DEFAULT 0,
    fecha_venta DATE,
    observaciones TEXT
)
""")


# ============================================================
# 3. POTREROS
# ============================================================

cursor.execute("""
CREATE TABLE potreros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    corral_count INTEGER DEFAULT 0,
    capacidad_por_corral INTEGER DEFAULT 0,
    observaciones TEXT
)
""")


# ============================================================
# 4. MEDICAMENTOS
# ============================================================

cursor.execute("""
CREATE TABLE medicamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    ingrediente_activo TEXT,
    uso TEXT
)
""")


# ============================================================
# 5. INVENTARIO
# ============================================================

cursor.execute("""
CREATE TABLE inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredientes TEXT NOT NULL,
    cantidad REAL DEFAULT 0
)
""")

# ============================================================
# 6. PREMEZCLAS
# ============================================================

cursor.execute("""
CREATE TABLE premezclas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo TEXT,
    ingrediente_activo TEXT,
    cantidad REAL DEFAULT 0,
    unidad TEXT DEFAULT 'kg',
    proveedor TEXT,
    observaciones TEXT
)
""")


# ============================================================
# 7. GANADO
# ============================================================

cursor.execute("""
CREATE TABLE ganado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arete TEXT NOT NULL UNIQUE,
    sexo TEXT,
    raza TEXT,
    fecha_ingreso DATE,
    edad_meses INTEGER,
    peso_inicial_kg REAL,
    peso_actual_kg REAL,
    proveedor TEXT,
    potrero_actual TEXT,
    alimentacion TEXT,
    destino_carne TEXT,
    estado TEXT DEFAULT 'En Engorda',
    peso_canal REAL,
    precio_venta REAL,
    valor_total REAL,
    fecha_venta DATE
)
""")


# ============================================================
# 8. HISTORIAL DE PESO
# ============================================================

cursor.execute("""
CREATE TABLE historial_peso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arete TEXT NOT NULL,
    fecha_medicion DATE NOT NULL,
    peso_kg REAL NOT NULL,
    incremento_kg REAL DEFAULT 0,

    FOREIGN KEY (arete)
        REFERENCES ganado(arete)
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
""")


# ============================================================
# 8. VACUNACIÓN
# ============================================================

cursor.execute("""
CREATE TABLE vacunacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arete TEXT NOT NULL,
    medicamento_id INTEGER,
    fecha DATE NOT NULL,
    dosis TEXT,
    observaciones TEXT,

    FOREIGN KEY (arete)
        REFERENCES ganado(arete)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (medicamento_id)
        REFERENCES medicamentos(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
)
""")


# ============================================================
# ÍNDICES
# ============================================================

cursor.execute("""
CREATE INDEX idx_ganado_arete
ON ganado(arete)
""")

cursor.execute("""
CREATE INDEX idx_ganado_estado
ON ganado(estado)
""")

cursor.execute("""
CREATE INDEX idx_ganado_raza
ON ganado(raza)
""")

cursor.execute("""
CREATE INDEX idx_ganado_potrero
ON ganado(potrero_actual)
""")

cursor.execute("""
CREATE INDEX idx_historial_arete
ON historial_peso(arete)
""")

cursor.execute("""
CREATE INDEX idx_historial_fecha
ON historial_peso(fecha_medicion)
""")

cursor.execute("""
CREATE INDEX idx_vacunacion_arete
ON vacunacion(arete)
""")

cursor.execute("""
CREATE INDEX idx_vacunacion_fecha
ON vacunacion(fecha)
""")

cursor.execute("""
CREATE INDEX idx_medicamentos_nombre
ON medicamentos(nombre)
""")

cursor.execute("""
CREATE INDEX idx_inventario_ingredientes
ON inventario(ingredientes)
""")


# ============================================================
# DATOS INICIALES
# ============================================================

# Potreros
cursor.executemany("""
INSERT INTO potreros
(nombre, corral_count, capacidad_por_corral, observaciones)
VALUES (?, ?, ?, ?)
""", [
    ("Potrero 1", 5, 20, "Área de engorda"),
    ("Potrero 2", 4, 25, "Área de crecimiento"),
    ("Potrero 3", 3, 15, "Área de recuperación")
])


# Medicamentos
cursor.executemany("""
INSERT INTO medicamentos
(nombre, ingrediente_activo, uso)
VALUES (?, ?, ?)
""", [
    ("Desparasitante", "Ivermectina",
     "Control de parásitos internos y externos"),

    ("Vacuna Bovilis", "Antígenos bovinos",
     "Prevención de enfermedades bovinas"),

    ("Antibiótico Bovino", "Oxitetraciclina",
     "Tratamiento de infecciones bacterianas")
])


# Inventario
cursor.executemany("""
INSERT INTO inventario
(ingredientes, cantidad)
VALUES (?, ?)
""", [
    ("Alimento concentrado", 1000),
    ("Maíz", 2500),
    ("Forraje", 3000),
    ("Minerales", 500)
])


# ============================================================
# GANADO DE PRUEBA
# ============================================================

cursor.executemany("""
INSERT INTO ganado (
    arete,
    sexo,
    raza,
    fecha_ingreso,
    edad_meses,
    peso_inicial_kg,
    peso_actual_kg,
    proveedor,
    potrero_actual,
    alimentacion,
    destino_carne,
    estado
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", [
    (
        "MX001",
        "Macho",
        "Brangus",
        "2026-09-01",
        18,
        420,
        450,
        "Proveedor A",
        "Potrero 1",
        "Concentrado y forraje",
        "Carne",
        "En Engorda"
    ),

    (
        "MX002",
        "Hembra",
        "Brangus",
        "2026-09-02",
        20,
        390,
        425,
        "Proveedor B",
        "Potrero 2",
        "Forraje y minerales",
        "Carne",
        "En Engorda"
    )
])


# ============================================================
# HISTORIAL DE PESO
# ============================================================

cursor.executemany("""
INSERT INTO historial_peso
(arete, fecha_medicion, peso_kg, incremento_kg)
VALUES (?, ?, ?, ?)
""", [
    ("MX001", "2026-09-01", 420, 420),
    ("MX001", "2026-09-15", 435, 15),
    ("MX001", "2026-09-28", 450, 15),

    ("MX002", "2026-09-02", 390, 390),
    ("MX002", "2026-09-15", 408, 18),
    ("MX002", "2026-09-28", 425, 17)
])


# ============================================================
# VACUNACIONES
# ============================================================

cursor.executemany("""
INSERT INTO vacunacion
(arete, medicamento_id, fecha, dosis, observaciones)
VALUES (?, ?, ?, ?, ?)
""", [
    (
        "MX001",
        1,
        "2026-09-05",
        "1 ml",
        "Aplicación preventiva"
    ),

    (
        "MX002",
        2,
        "2026-09-06",
        "2 ml",
        "Aplicación preventiva"
    )
])


# ============================================================
# VENTA
# ============================================================

cursor.execute("""
INSERT INTO ventas
(valor_total, fecha_venta, observaciones)
VALUES (?, ?, ?)
""", (
    0,
    None,
    "Sin ventas registradas"
))

# ============================================================
# DATOS INICIALES DE PREMEZCLAS
# ============================================================

cursor.executemany("""
INSERT INTO premezclas
(nombre, tipo, ingrediente_activo, cantidad, unidad, proveedor, observaciones)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", [
    (
        "Premezcla Mineral",
        "Mineral",
        "Calcio y fósforo",
        100,
        "kg",
        "Proveedor A",
        "Para ganado de engorda"
    ),
    (
        "Premezcla Engorda",
        "Nutricional",
        "Vitaminas y minerales",
        50,
        "kg",
        "Proveedor B",
        "Mezcla para etapa de finalización"
    )
])

# ============================================================
# GUARDAR CAMBIOS
# ============================================================

conexion.commit()

# Mostrar tablas creadas
cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

tablas = cursor.fetchall()

print("\n========================================")
print(" BASE DE DATOS CREADA CORRECTAMENTE")
print("========================================")
print(f"\nArchivo: {DB_NAME}")
print("\nTablas creadas:")

for tabla in tablas:
    print(f"  ✓ {tabla[0]}")

print("\nBase de datos lista para usar.")

conexion.close()

