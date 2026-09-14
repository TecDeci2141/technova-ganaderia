from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import sqlite3
import datetime
import time
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# ---------- Configuración básica ----------
app = Flask(__name__)
app.secret_key = 'cambios_secret_muy_seguro_2024'
DB_NAME = "ganado.db"

# 🔐 CREDENCIALES MAESTRAS (para autorizar creación y edición de usuarios)
MASTER_USER = "Diego"
MASTER_PASS = "D3c1d3r10"

# ---------- Helpers ----------
def get_db_connection():
    """Abre conexión a SQLite con reintentos automáticos para evitar bloqueos."""
    for _ in range(5):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                time.sleep(0.2)
            else:
                raise
    raise Exception("No se pudo establecer conexión con la base de datos después de varios intentos.")

def init_db():
    """Inicializa tablas esenciales si no existen."""
    conn = get_db_connection()
    
    # Tabla de usuarios
    conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nombre_completo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    admin_exists = conn.execute('SELECT id FROM usuarios WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        conn.execute('INSERT INTO usuarios (username, password, nombre_completo) VALUES (?, ?, ?)',
                     ('admin', generate_password_hash('admin123'), 'Administrador del Sistema'))
    
    # Tabla de ventas
    conn.execute('''CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        valor_total REAL DEFAULT 0,
        fecha_venta DATE,
        observaciones TEXT
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente.")

def format_number(num):
    try:
        return f"{float(num):,.2f}"
    except (ValueError, TypeError):
        return "0.00"

def verify_master(master_user, master_pass):
    """Verifica si las credenciales maestras son correctas."""
    return master_user == MASTER_USER and master_pass == MASTER_PASS

def es_admin():
    """Verifica si el usuario actual es Diego o admin."""
    return session.get('username') in ['Diego', 'admin']

def login_required(f):
    """Decorador para proteger rutas que requieren autenticación."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_helpers():
    return dict(
        format_number=format_number,
        now=datetime.datetime.now,
        current_user=session.get('username', ''),
        current_user_id=session.get('user_id'),
        current_user_name=session.get('nombre_completo', '')
    )

# ================= AUTENTICACIÓN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Por favor completa todos los campos.', 'danger')
            return render_template('login.html')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['nombre_completo'] = user['nombre_completo']
            flash(f'¡Bienvenido, {user["nombre_completo"] or username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        nombre_completo = request.form.get('nombre_completo', '').strip()
        master_user = request.form.get('master_user', '').strip()
        master_pass = request.form.get('master_pass', '')
        
        if not username or not password:
            flash('Usuario y contraseña son obligatorios.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('register.html')
        
        # 🔐 Validación de credenciales maestras
        if not verify_master(master_user, master_pass):
            flash('❌ Credenciales de autorización incorrectas. Solo personal autorizado puede crear usuarios.', 'danger')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO usuarios (username, password, nombre_completo) VALUES (?, ?, ?)',
                         (username, hashed_password, nombre_completo))
            conn.commit()
            conn.close()
            flash(f'✅ Usuario "{username}" registrado exitosamente.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El nombre de usuario ya existe. Elige otro.', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('login'))

# ================= PERFIL DE USUARIO =================
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Permite a CUALQUIER usuario cambiar su propio nombre y contraseña."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if not user:
        session.clear()
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nuevo_nombre = request.form.get('nombre_completo', '').strip()
        nueva_password = request.form.get('new_password', '').strip()
        confirmar_password = request.form.get('confirm_password', '').strip()
        password_actual = request.form.get('current_password', '')
        
        # Verificar contraseña actual (obligatoria para cualquier cambio)
        if not check_password_hash(user['password'], password_actual):
            flash('❌ La contraseña actual es incorrecta.', 'danger')
            return render_template('profile.html', user=user)
        
        # Validar nueva contraseña si se proporcionó
        if nueva_password:
            if nueva_password != confirmar_password:
                flash('Las contraseñas nuevas no coinciden.', 'danger')
                return render_template('profile.html', user=user)
            if len(nueva_password) < 6:
                flash('La nueva contraseña debe tener al menos 6 caracteres.', 'danger')
                return render_template('profile.html', user=user)
        
        # Actualizar en la base de datos
        conn = get_db_connection()
        try:
            if nueva_password:
                hashed = generate_password_hash(nueva_password)
                conn.execute('UPDATE usuarios SET nombre_completo = ?, password = ? WHERE id = ?',
                             (nuevo_nombre, hashed, session['user_id']))
            else:
                conn.execute('UPDATE usuarios SET nombre_completo = ? WHERE id = ?',
                             (nuevo_nombre, session['user_id']))
            conn.commit()
            session['nombre_completo'] = nuevo_nombre
            flash('✅ Perfil actualizado correctamente.', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f'Error al actualizar: {str(e)}', 'danger')
        finally:
            conn.close()
    
    return render_template('profile.html', user=user)

# ================= ADMIN DE USUARIOS (SOLO DIEGO/ADMIN) =================
@app.route('/admin/users')
@login_required
def admin_users():
    """Lista todos los usuarios del sistema (solo para Diego o admin)."""
    if not es_admin():
        flash('❌ No tienes permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    usuarios = conn.execute('SELECT id, username, nombre_completo, created_at FROM usuarios ORDER BY id').fetchall()
    conn.close()
    return render_template('admin/users.html', usuarios=usuarios)

@app.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_users_edit(id):
    """Editar cualquier usuario (requiere credenciales maestras)."""
    if not es_admin():
        flash('❌ No tienes permisos.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
    
    if not user:
        conn.close()
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('admin_users'))
    
    if request.method == 'POST':
        master_user = request.form.get('master_user', '').strip()
        master_pass = request.form.get('master_pass', '')
        
        # 🔐 Validar credenciales maestras
        if not verify_master(master_user, master_pass):
            conn.close()
            flash('❌ Credenciales maestras incorrectas.', 'danger')
            return render_template('admin/edit_user.html', user=user)
        
        nuevo_username = request.form.get('username', '').strip()
        nuevo_nombre = request.form.get('nombre_completo', '').strip()
        nueva_password = request.form.get('new_password', '').strip()
        
        if not nuevo_username:
            flash('El nombre de usuario es obligatorio.', 'danger')
            return render_template('admin/edit_user.html', user=user)
        
        if nueva_password and len(nueva_password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('admin/edit_user.html', user=user)
        
        try:
            if nueva_password:
                hashed = generate_password_hash(nueva_password)
                conn.execute('UPDATE usuarios SET username = ?, nombre_completo = ?, password = ? WHERE id = ?',
                             (nuevo_username, nuevo_nombre, hashed, id))
            else:
                conn.execute('UPDATE usuarios SET username = ?, nombre_completo = ? WHERE id = ?',
                             (nuevo_username, nuevo_nombre, id))
            conn.commit()
            flash(f'✅ Usuario "{nuevo_username}" actualizado correctamente.', 'success')
            conn.close()
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            flash('El nombre de usuario ya existe.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            conn.close()
    
    conn.close()
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
def admin_users_delete(id):
    """Eliminar un usuario (requiere credenciales maestras)."""
    if not es_admin():
        flash('❌ No tienes permisos.', 'danger')
        return redirect(url_for('index'))
    
    master_user = request.form.get('master_user', '').strip()
    master_pass = request.form.get('master_pass', '')
    
    if not verify_master(master_user, master_pass):
        flash('❌ Credenciales maestras incorrectas. No se puede eliminar.', 'danger')
        return redirect(url_for('admin_users'))
    
    if id == session['user_id']:
        flash('❌ No puedes eliminar tu propio usuario.', 'danger')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
        conn.commit()
        flash('✅ Usuario eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users'))

# ---------- Dashboard ----------
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    try:
        total_all = conn.execute('SELECT COUNT(*) FROM ganado').fetchone()[0] or 0
        listoventa = conn.execute("SELECT COUNT(*) FROM ganado WHERE estado IN ('Vendido','Listo para Venta')").fetchone()[0] or 0
        
        try:
            ingresos = conn.execute('SELECT SUM(valor_total) FROM ventas').fetchone()[0] or 0
        except sqlite3.OperationalError:
            ingresos = 0
        
        try:
            total_kg = conn.execute('SELECT SUM(cantidad) FROM inventario').fetchone()[0] or 0
        except sqlite3.OperationalError:
            total_kg = 0
        
        por_estado = conn.execute("SELECT estado, COUNT(*) as cnt FROM ganado GROUP BY estado").fetchall()
        por_potrero = conn.execute('SELECT potrero_actual, COUNT(*) as cnt FROM ganado GROUP BY potrero_actual').fetchall()
        potreros = conn.execute('SELECT * FROM potreros').fetchall()
        
    except Exception as e:
        flash(f'Error al cargar el dashboard: {str(e)}', 'danger')
        total_all = listoventa = ingresos = total_kg = 0
        por_estado = por_potrero = []
        potreros = []
    finally:
        conn.close()

    return render_template('index.html',
                           total_all=total_all,
                           listoventa=listoventa,
                           ingresos=ingresos,
                           total_kg=total_kg,
                           por_estado=por_estado,
                           por_potrero=por_potrero,
                           potreros=potreros)

# ================= CRUD GANADO =================
@app.route('/ganado/list')
@login_required
def ganado_list():
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM ganado ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('ganado/list.html', data=data)

@app.route('/ganado/insert', methods=['GET','POST'])
@login_required
def ganado_insert():
    if request.method == 'POST':
        f = request.form
        conn = get_db_connection()
        conn.execute('''INSERT INTO ganado (arete, sexo, raza, fecha_ingreso, edad_meses, peso_inicial_kg, peso_actual_kg,
                      proveedor, potrero_actual, alimentacion, destino_carne, estado, peso_canal, precio_venta, valor_total, fecha_venta)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            f.get('arete'), f.get('sexo'), f.get('raza'), f.get('fecha_ingreso'),
            f.get('edad_meses') or None, f.get('peso_inicial_kg') or None, f.get('peso_actual_kg') or None,
            f.get('proveedor'), f.get('potrero_actual'), f.get('alimentacion'), f.get('destino_carne'),
            f.get('estado') or 'En Engorda', f.get('peso_canal') or None, f.get('precio_venta') or None,
            f.get('valor_total') or None, f.get('fecha_venta') or None
        ))
        conn.commit()
        conn.close()
        flash('Ganado agregado.', 'success')
        return redirect(url_for('ganado_list'))
    return render_template('ganado/insert.html')

@app.route('/ganado/update/<int:id>', methods=['GET','POST'])
@login_required
def ganado_update(id):
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM ganado WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        flash('Registro no encontrado.', 'warning')
        return redirect(url_for('ganado_list'))
    if request.method == 'POST':
        f = request.form
        conn.execute('''UPDATE ganado SET sexo=?, raza=?, fecha_ingreso=?, edad_meses=?, peso_inicial_kg=?, peso_actual_kg=?,
                        proveedor=?, potrero_actual=?, alimentacion=?, destino_carne=?, estado=?, peso_canal=?, precio_venta=?, valor_total=?, fecha_venta=?
                        WHERE id=?''', (
            f.get('sexo'), f.get('raza'), f.get('fecha_ingreso'), f.get('edad_meses') or None,
            f.get('peso_inicial_kg') or None, f.get('peso_actual_kg') or None, f.get('proveedor'),
            f.get('potrero_actual'), f.get('alimentacion'), f.get('destino_carne'),
            f.get('estado'), f.get('peso_canal') or None, f.get('precio_venta') or None,
            f.get('valor_total') or None, f.get('fecha_venta') or None, id
        ))
        conn.commit()
        conn.close()
        flash('Ganado actualizado.', 'info')
        return redirect(url_for('ganado_list'))
    conn.close()
    return render_template('ganado/update.html', row=row)

@app.route('/ganado/delete/<int:id>', methods=['POST'])
@login_required
def ganado_delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM ganado WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Registro eliminado.', 'danger')
    return redirect(url_for('ganado_list'))

# ================= CRUD PESAJES =================
@app.route('/pesajes/list')
@login_required
def pesajes_list():
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM historial_peso ORDER BY fecha_medicion DESC').fetchall()
    conn.close()
    return render_template('pesajes/list.html', data=data)

@app.route('/pesajes/insert', methods=['GET','POST'])
@login_required
def pesajes_insert():
    conn = get_db_connection()
    animales = conn.execute('SELECT arete FROM ganado').fetchall()
    conn.close()
    if request.method == 'POST':
        f = request.form
        arete = f.get('arete')
        fecha = f.get('fecha_medicion')
        peso = float(f.get('peso_kg') or 0)
        conn = get_db_connection()
        last = conn.execute('SELECT peso_kg FROM historial_peso WHERE arete=? ORDER BY fecha_medicion DESC LIMIT 1', (arete,)).fetchone()
        incremento = peso - last['peso_kg'] if last else peso
        conn.execute('INSERT INTO historial_peso (arete, fecha_medicion, peso_kg, incremento_kg) VALUES (?, ?, ?, ?)',
                     (arete, fecha, peso, incremento))
        conn.commit()
        conn.close()
        flash('Registro de peso agregado.', 'success')
        return redirect(url_for('pesajes_list'))
    return render_template('pesajes/insert.html', animales=animales)

@app.route('/pesajes/update/<int:id>', methods=['GET','POST'])
@login_required
def pesajes_update(id):
    conn = get_db_connection()
    registro = conn.execute('SELECT * FROM historial_peso WHERE id=?', (id,)).fetchone()
    animales = conn.execute('SELECT arete FROM ganado').fetchall()
    conn.close()
    if not registro:
        flash('Registro no encontrado.', 'warning')
        return redirect(url_for('pesajes_list'))
    if request.method == 'POST':
        f = request.form
        arete = f.get('arete')
        fecha = f.get('fecha_medicion')
        peso = float(f.get('peso_kg') or 0)
        conn = get_db_connection()
        last = conn.execute('SELECT peso_kg FROM historial_peso WHERE arete=? AND id<>? ORDER BY fecha_medicion DESC LIMIT 1', (arete, id)).fetchone()
        incremento = peso - last['peso_kg'] if last else peso
        conn.execute('UPDATE historial_peso SET arete=?, fecha_medicion=?, peso_kg=?, incremento_kg=? WHERE id=?',
                     (arete, fecha, peso, incremento, id))
        conn.commit()
        conn.close()
        flash('Registro de peso actualizado.', 'info')
        return redirect(url_for('pesajes_list'))
    return render_template('pesajes/update.html', registro=registro, animales=animales)

@app.route('/pesajes/delete/<int:id>', methods=['POST'])
@login_required
def pesajes_delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM historial_peso WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Registro de peso eliminado.', 'danger')
    return redirect(url_for('pesajes_list'))

# ================= CRUD VACUNACION =================
@app.route('/vacunacion/list')
@login_required
def vacunacion_list():
    conn = get_db_connection()
    data = conn.execute('''
        SELECT v.id, v.arete, v.fecha, v.dosis, v.observaciones, m.nombre as medicamento
        FROM vacunacion v
        LEFT JOIN medicamentos m ON v.medicamento_id = m.id
        ORDER BY v.fecha DESC
    ''').fetchall()
    conn.close()
    return render_template('vacunacion/list.html', data=data)

@app.route('/vacunacion/insert', methods=['GET','POST'])
@login_required
def vacunacion_insert():
    conn = get_db_connection()
    animales = conn.execute('SELECT arete FROM ganado').fetchall()
    medicamentos = conn.execute('SELECT * FROM medicamentos').fetchall()
    conn.close()
    if request.method == 'POST':
        f = request.form
        conn = get_db_connection()
        conn.execute('INSERT INTO vacunacion (arete, medicamento_id, fecha, dosis, observaciones) VALUES (?, ?, ?, ?, ?)',
                     (f.get('arete'), f.get('medicamento_id'), f.get('fecha'), f.get('dosis'), f.get('observaciones')))
        conn.commit()
        conn.close()
        flash('Vacunación registrada.', 'success')
        return redirect(url_for('vacunacion_list'))
    return render_template('vacunacion/insert.html', animales=animales, medicamentos=medicamentos)

@app.route('/vacunacion/update/<int:id>', methods=['GET','POST'])
@login_required
def vacunacion_update(id):
    conn = get_db_connection()
    registro = conn.execute('SELECT * FROM vacunacion WHERE id=?', (id,)).fetchone()
    animales = conn.execute('SELECT arete FROM ganado').fetchall()
    medicamentos = conn.execute('SELECT * FROM medicamentos').fetchall()
    conn.close()
    if not registro:
        flash('Registro no encontrado.', 'warning')
        return redirect(url_for('vacunacion_list'))
    if request.method == 'POST':
        f = request.form
        conn = get_db_connection()
        conn.execute('UPDATE vacunacion SET arete=?, medicamento_id=?, fecha=?, dosis=?, observaciones=? WHERE id=?',
                     (f.get('arete'), f.get('medicamento_id'), f.get('fecha'), f.get('dosis'), f.get('observaciones'), id))
        conn.commit()
        conn.close()
        flash('Registro de vacunación actualizado.', 'info')
        return redirect(url_for('vacunacion_list'))
    return render_template('vacunacion/update.html', registro=registro, animales=animales, medicamentos=medicamentos)

@app.route('/vacunacion/delete/<int:id>', methods=['POST'])
@login_required
def vacunacion_delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM vacunacion WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Registro eliminado.', 'danger')
    return redirect(url_for('vacunacion_list'))

# ================= CRUD INVENTARIO =================
@app.route('/inventario/list')
@login_required
def inventario_list():
    search = request.args.get('search', '').strip()
    conn = get_db_connection()
    try:
        if search:
            rows = conn.execute("SELECT * FROM inventario WHERE ingredientes LIKE ? ORDER BY id DESC", 
                                ('%' + search + '%',)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM inventario ORDER BY id DESC").fetchall()
    except sqlite3.OperationalError as e:
        flash(f'Error en la base de datos: {str(e)}', 'danger')
        rows = []
    conn.close()
    return render_template('inventario/list.html', data=rows, search=search)

@app.route('/inventario/insert', methods=['GET', 'POST'])
@login_required
def inventario_insert():
    if request.method == 'POST':
        f = request.form
        ingredientes = (f.get('ingredientes') or '').strip()
        cantidad_raw = (f.get('cantidad') or '0').strip()
        
        if not ingredientes:
            flash('El nombre del ingrediente es obligatorio.', 'danger')
            return render_template('inventario/insert.html')
        
        try:
            cantidad = float(cantidad_raw) if cantidad_raw else 0
        except ValueError:
            flash('La cantidad debe ser un número válido.', 'danger')
            return render_template('inventario/insert.html')
        
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO inventario (ingredientes, cantidad) VALUES (?, ?)",
                         (ingredientes, cantidad))
            conn.commit()
            flash(f'✅ Ingrediente "{ingredientes}" agregado correctamente.', 'success')
            return redirect(url_for('inventario_list'))
        except sqlite3.OperationalError as e:
            flash(f'❌ Error de base de datos: {str(e)}', 'danger')
            return render_template('inventario/insert.html')
        finally:
            conn.close()
    
    return render_template('inventario/insert.html')

@app.route('/inventario/update/<int:id>', methods=['GET', 'POST'])
@login_required
def inventario_update(id):
    conn = get_db_connection()
    try:
        item = conn.execute("SELECT * FROM inventario WHERE id = ?", (id,)).fetchone()
    except sqlite3.OperationalError as e:
        conn.close()
        flash(f'Error al buscar registro: {str(e)}', 'danger')
        return redirect(url_for('inventario_list'))
    
    if not item:
        conn.close()
        flash('Registro no encontrado.', 'warning')
        return redirect(url_for('inventario_list'))
    
    if request.method == 'POST':
        f = request.form
        ingredientes = (f.get('ingredientes') or '').strip()
        cantidad_raw = (f.get('cantidad') or '0').strip()
        
        if not ingredientes:
            flash('El nombre del ingrediente es obligatorio.', 'danger')
            return render_template('inventario/update.html', item=item)
        
        try:
            cantidad = float(cantidad_raw) if cantidad_raw else 0
        except ValueError:
            flash('La cantidad debe ser un número válido.', 'danger')
            return render_template('inventario/update.html', item=item)
        
        try:
            conn.execute("UPDATE inventario SET ingredientes = ?, cantidad = ? WHERE id = ?",
                         (ingredientes, cantidad, id))
            conn.commit()
            flash(f'✅ Ingrediente "{ingredientes}" actualizado.', 'info')
            return redirect(url_for('inventario_list'))
        except sqlite3.OperationalError as e:
            flash(f'❌ Error de base de datos: {str(e)}', 'danger')
        finally:
            conn.close()
        return render_template('inventario/update.html', item=item)
    
    conn.close()
    return render_template('inventario/update.html', item=item)

@app.route('/inventario/delete/<int:id>', methods=['POST'])
@login_required
def inventario_delete(id):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM inventario WHERE id = ?", (id,))
        conn.commit()
        flash('Registro eliminado correctamente.', 'danger')
    except sqlite3.OperationalError as e:
        flash(f'Error al eliminar: {str(e)}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('inventario_list'))

# ================= CRUD POTREROS =================
@app.route('/potreros/list')
@login_required
def potreros_list():
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM potreros ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('potreros/list.html', data=data)

@app.route('/potreros/insert', methods=['GET','POST'])
@login_required
def potreros_insert():
    if request.method == 'POST':
        f = request.form
        conn = get_db_connection()
        conn.execute('INSERT INTO potreros (nombre, corral_count, capacidad_por_corral, observaciones) VALUES (?, ?, ?, ?)',
                     (f.get('nombre'), f.get('corral_count') or 0, f.get('capacidad_por_corral') or 0, f.get('observaciones')))
        conn.commit()
        conn.close()
        flash('Potrero agregado.', 'success')
        return redirect(url_for('potreros_list'))
    return render_template('potreros/insert.html')

@app.route('/potreros/update/<int:id>', methods=['GET','POST'])
@login_required
def potreros_update(id):
    conn = get_db_connection()
    potrero = conn.execute('SELECT * FROM potreros WHERE id=?', (id,)).fetchone()
    if not potrero:
        conn.close()
        flash('Registro no encontrado.', 'warning')
        return redirect(url_for('potreros_list'))
    if request.method == 'POST':
        f = request.form
        conn.execute('UPDATE potreros SET nombre=?, corral_count=?, capacidad_por_corral=?, observaciones=? WHERE id=?',
                     (f.get('nombre'), f.get('corral_count') or 0, f.get('capacidad_por_corral') or 0, f.get('observaciones'), id))
        conn.commit()
        conn.close()
        flash('Registro actualizado.', 'info')
        return redirect(url_for('potreros_list'))
    conn.close()
    return render_template('potreros/update.html', potrero=potrero)

@app.route('/potreros/delete/<int:id>', methods=['POST'])
@login_required
def potreros_delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM potreros WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Registro eliminado.', 'danger')
    return redirect(url_for('potreros_list'))

# ================= CRUD MEDICAMENTOS =================
@app.route('/medicamentos/list')
@login_required
def medicamentos_list():
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM medicamentos ORDER BY nombre').fetchall()
    conn.close()
    return render_template('medicamentos/list.html', data=data)

@app.route('/medicamentos/insert', methods=['GET','POST'])
@login_required
def medicamentos_insert():
    if request.method == 'POST':
        f = request.form
        conn = get_db_connection()
        conn.execute('INSERT INTO medicamentos (nombre, ingrediente_activo, uso) VALUES (?, ?, ?)',
                     (f.get('nombre'), f.get('ingrediente_activo'), f.get('uso')))
        conn.commit()
        conn.close()
        flash('Medicamento agregado.', 'success')
        return redirect(url_for('medicamentos_list'))
    return render_template('medicamentos/insert.html')

@app.route('/medicamentos/update/<int:id>', methods=['GET','POST'])
@login_required
def medicamentos_update(id):
    conn = get_db_connection()
    med = conn.execute('SELECT * FROM medicamentos WHERE id=?', (id,)).fetchone()
    if not med:
        conn.close()
        flash('Registro no encontrado.', 'warning')
        return redirect(url_for('medicamentos_list'))
    if request.method == 'POST':
        f = request.form
        conn.execute('UPDATE medicamentos SET nombre=?, ingrediente_activo=?, uso=? WHERE id=?',
                     (f.get('nombre'), f.get('ingrediente_activo'), f.get('uso'), id))
        conn.commit()
        conn.close()
        flash('Medicamento actualizado.', 'info')
        return redirect(url_for('medicamentos_list'))
    conn.close()
    return render_template('medicamentos/update.html', med=med)

@app.route('/medicamentos/delete/<int:id>', methods=['POST'])
@login_required
def medicamentos_delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM medicamentos WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Registro eliminado.', 'danger')
    return redirect(url_for('medicamentos_list'))

# ================= MAIN =================
if __name__ == '__main__':
    init_db()
    app.run(debug=True)