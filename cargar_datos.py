
import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "ganado.db"

conexion = sqlite3.connect(DB_NAME)
cursor = conexion.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

try:
    # =====================================================
    # 1. USUARIOS: 10 registros
    # =====================================================
    usuarios = [
        (f"usuario{i:02}", generate_password_hash(f"Demo{i}2026!"),
         f"Usuario de prueba {i}")
        for i in range(1, 11)
    ]

    cursor.executemany("""
        INSERT INTO usuarios (username, password, nombre_completo)
        VALUES (?, ?, ?)
    """, usuarios)

    # =====================================================
    # 2. POTREROS: 10 registros
    # =====================================================
    potreros = [
        (f"Potrero {i}", 4 + i % 4, 20 + i * 5,
         f"Área de manejo ganadero {i}")
        for i in range(1, 11)
    ]

    cursor.executemany("""
        INSERT INTO potreros
        (nombre, corral_count, capacidad_por_corral, observaciones)
        VALUES (?, ?, ?, ?)
    """, potreros)

    # =====================================================
    # 3. MEDICAMENTOS: 10 registros
    # =====================================================
    medicamentos = [
        ("Ivermectina", "Ivermectina", "Antiparasitario"),
        ("Albendazol", "Albendazol", "Antiparasitario"),
        ("Vacuna clostridial", "Antígenos clostridiales",
         "Prevención de clostridiosis"),
        ("Vacuna respiratoria", "Antígenos respiratorios",
         "Prevención de enfermedades respiratorias"),
        ("Oxitetraciclina", "Oxitetraciclina", "Antibiótico"),
        ("Flunixin", "Flunixin meglumine", "Antiinflamatorio"),
        ("Electrolitos", "Sales electrolíticas", "Rehidratación"),
        ("Vitamina ADE", "Vitaminas A, D y E", "Suplementación"),
        ("Selenio y vitamina E", "Selenio y vitamina E",
         "Suplementación mineral"),
        ("Vacuna reproductiva", "Antígenos reproductivos",
         "Prevención reproductiva")
    ]

    cursor.executemany("""
        INSERT INTO medicamentos (nombre, ingrediente_activo, uso)
        VALUES (?, ?, ?)
    """, medicamentos)

    # =====================================================
    # 4. INVENTARIO: 10 registros
    # =====================================================
    inventario = [
        ("Maíz molido", 2500),
        ("Sorgo", 1800),
        ("Pasta de soya", 900),
        ("Alfalfa", 1200),
        ("Rastrojo de maíz", 3000),
        ("Sal mineralizada", 250),
        ("Melaza", 600),
        ("Afrecho de trigo", 750),
        ("Heno", 1500),
        ("Alimento concentrado", 2000)
    ]

    cursor.executemany("""
        INSERT INTO inventario (ingredientes, cantidad)
        VALUES (?, ?)
    """, inventario)

    # =====================================================
    # 5. PREMEZCLAS: 10 registros
    # Requiere que ya hayas creado esta tabla.
    # =====================================================
    premezclas = [
        ("Mineral para engorda", "Mineral",
         "Calcio y fósforo", 100, "kg", "Proveedor A",
         "Para suplementación de bovinos"),
        ("Vitaminas ADE", "Vitamina",
         "Vitaminas A, D y E", 50, "kg", "Proveedor B",
         "Uso según formulación"),
        ("Premezcla de crecimiento", "Nutricional",
         "Vitaminas y minerales", 80, "kg", "Proveedor C",
         "Etapa de crecimiento"),
        ("Premezcla de finalización", "Nutricional",
         "Microminerales y vitaminas", 120, "kg", "Proveedor D",
         "Etapa de finalización"),
        ("Premezcla reproductiva", "Reproductiva",
         "Minerales y vitaminas", 60, "kg", "Proveedor E",
         "Manejo reproductivo"),
        ("Premezcla con magnesio", "Mineral",
         "Magnesio", 40, "kg", "Proveedor F",
         "Uso según dieta"),
        ("Premezcla con zinc", "Mineral",
         "Zinc", 35, "kg", "Proveedor G",
         "Uso según formulación"),
        ("Premezcla para becerros", "Nutricional",
         "Vitaminas y minerales", 45, "kg", "Proveedor H",
         "Para animales jóvenes"),
        ("Premezcla de transición", "Nutricional",
         "Minerales y vitaminas", 55, "kg", "Proveedor I",
         "Adaptación alimenticia"),
        ("Premezcla mineral completa", "Mineral",
         "Calcio, fósforo y microminerales", 90, "kg",
         "Proveedor J", "Complemento de la ración")
    ]

    cursor.executemany("""
        INSERT INTO premezclas
        (nombre, tipo, ingrediente_activo, cantidad, unidad,
         proveedor, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, premezclas)

    # =====================================================
    # 6. GANADO: 10 registros
    # =====================================================
    razas = [
        "Brangus", "Angus", "Hereford", "Charolais", "Simmental",
        "Brahman", "Beefmaster", "Limousin", "Suizo Europeo", "Cebú"
    ]

    ganado = []

    for i, raza in enumerate(razas, start=1):
        peso = 300 + i * 15

        ganado.append((
            f"NV{i:04}",
            "Macho" if i % 2 else "Hembra",
            raza,
            f"2026-09-{i:02}",
            12 + i,
            peso - 20,
            peso,
            f"Proveedor {i}",
            f"Potrero {i}",
            "Forraje y alimento concentrado",
            "Carne",
            "En Engorda",
            None, None, None, None
        ))

    cursor.executemany("""
        INSERT INTO ganado (
            arete, sexo, raza, fecha_ingreso, edad_meses,
            peso_inicial_kg, peso_actual_kg, proveedor,
            potrero_actual, alimentacion, destino_carne,
            estado, peso_canal, precio_venta, valor_total, fecha_venta
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ganado)

    # =====================================================
    # 7. HISTORIAL DE PESO: 10 registros
    # =====================================================
    historial = []

    for i in range(1, 11):
        peso_actual = 300 + i * 15

        historial.append((
            f"NV{i:04}",
            "2026-10-01",
            peso_actual,
            20
        ))

    cursor.executemany("""
        INSERT INTO historial_peso
        (arete, fecha_medicion, peso_kg, incremento_kg)
        VALUES (?, ?, ?, ?)
    """, historial)

    # =====================================================
    # 8. VACUNACIÓN: 10 registros
    # =====================================================
    vacunaciones = []

    for i in range(1, 11):
        vacunaciones.append((
            f"NV{i:04}",
            ((i - 1) % 10) + 1,
            f"2026-10-{i:02}",
            "Según etiqueta del producto y criterio veterinario",
            "Registro de demostración; verificar aplicación real"
        ))

    cursor.executemany("""
        INSERT INTO vacunacion
        (arete, medicamento_id, fecha, dosis, observaciones)
        VALUES (?, ?, ?, ?, ?)
    """, vacunaciones)

    # =====================================================
    # 9. VENTAS: 10 registros
    # =====================================================
    ventas = [
        (25000, "2026-09-01", "Venta de bovinos"),
        (28750, "2026-09-03", "Venta de ganado"),
        (31200, "2026-09-05", "Lote de engorda"),
        (26500, "2026-09-08", "Venta de bovinos"),
        (34000, "2026-09-10", "Lote de finalización"),
        (29800, "2026-09-12", "Venta de ganado"),
        (35500, "2026-09-15", "Venta de bovinos"),
        (27600, "2026-09-18", "Lote de engorda"),
        (32000, "2026-09-22", "Venta de ganado"),
        (38000, "2026-09-25", "Venta de bovinos")
    ]

    cursor.executemany("""
        INSERT INTO ventas (valor_total, fecha_venta, observaciones)
        VALUES (?, ?, ?)
    """, ventas)

    # Guardar todo únicamente si no hubo errores
    conexion.commit()

    print("\nDatos cargados correctamente.")
    print("Registros agregados por tabla:")

    tablas = [
        "usuarios", "potreros", "medicamentos", "inventario",
        "premezclas", "ganado", "historial_peso",
        "vacunacion", "ventas"
    ]

    for tabla in tablas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        total = cursor.fetchone()[0]
        print(f"{tabla}: {total} registros en total")

except sqlite3.Error as error:
    conexion.rollback()
    print(f"Error de SQLite: {error}")
    print("Se revirtieron los cambios de esta ejecución.")

except Exception as error:
    conexion.rollback()
    print(f"Error: {error}")
    print("Se revirtieron los cambios de esta ejecución.")

finally:
    conexion.close()
