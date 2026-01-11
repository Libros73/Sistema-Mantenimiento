from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
import os

# --- 1. CONFIGURACIÓN ---
app = Flask(__name__)
app.secret_key = 'secreto_gnb_mantenimiento' 

# Configuración Híbrida de Base de Datos (Nube / Local)
uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///mantenimiento.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 2. GESTOR DE LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)

# --- 3. MODELOS DE LA BASE DE DATOS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    serial = db.Column(db.String(50), unique=True)
    ubicacion = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='Operativo')
    observaciones = db.Column(db.String(200)) # Campo Nuevo

    def to_json(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "serial": self.serial,
            "ubicacion": self.ubicacion,
            "estado": self.estado,      # <--- ¡LA COMA QUE FALTABA!
            "observaciones": self.observaciones
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- 4. RUTAS ---

@app.route('/')
def dashboard():
    # Consulta a la base de datos
    todos_los_equipos = Equipo.query.all()
    return render_template('index.html', equipos=todos_los_equipos)

@app.route('/setup-inicial')
def setup_inicial():
    if Equipo.query.first():
        return "¡El inventario ya tiene datos!"

    e1 = Equipo(nombre="Panel Principal Fike", tipo="Panel Control", serial="FK-001", 
                ubicacion="Sótano 1", observaciones="Mantenimiento preventivo OK. Baterías al 98%.")
    
    e2 = Equipo(nombre="Sensor Humo Servidores", tipo="Sensor Fotoeléctrico", serial="SH-102", 
                ubicacion="Data Center", observaciones="Lente requiere limpieza en próxima visita.")
    
    e3 = Equipo(nombre="Estación Manual Lobby", tipo="Palanca", serial="EM-005", 
                ubicacion="Lobby Principal", estado="Falla", observaciones="Vidrio roto por impacto accidental.")

    db.session.add_all([e1, e2, e3])
    db.session.commit()

    return "✅ Base de Datos Reconstruida con Observaciones."

# RUTA PARA AGREGAR EQUIPOS (API)
@app.route('/api/equipos', methods=['POST'])
def agregar_equipo():
    datos = request.json
    
    # Validación básica de Ingeniero
    if not datos or 'serial' not in datos:
        return jsonify({"mensaje": "Datos incompletos"}), 400

    # Crear el objeto
    nuevo = Equipo(
        nombre=datos['nombre'],
        tipo=datos['tipo'],
        serial=datos['serial'],
        ubicacion=datos['ubicacion'],
        observaciones=datos.get('observaciones', '')
    )

    # Guardar en DB
    try:
        db.session.add(nuevo)
        db.session.commit()
        return jsonify({"mensaje": "Equipo guardado correctamente"})
    except Exception as e:
        db.session.rollback() # Si falla (ej: serial repetido), cancelamos
        return jsonify({"mensaje": "Error: El serial probablemente ya existe"}), 400
    
    # RUTA PARA EDITAR EQUIPO (PUT)
@app.route('/api/equipos/<int:id>', methods=['PUT'])
def actualizar_equipo(id):
    # 1. Buscar el equipo por ID
    equipo = Equipo.query.get(id)
    if not equipo:
        return jsonify({"mensaje": "Equipo no encontrado"}), 404

    # 2. Recibir los datos nuevos
    datos = request.json

    # 3. Sobrescribir propiedades (Update)
    equipo.nombre = datos['nombre']
    equipo.tipo = datos['tipo']
    equipo.serial = datos['serial']
    equipo.ubicacion = datos['ubicacion']
    equipo.observaciones = datos.get('observaciones', '')
    
    # IMPORTANTE: Si quisieras cambiar el estado a "Falla", aquí lo harías
    # Por ahora asumimos que el estado se maneja igual, o podrías recibirlo del form.
    if 'estado' in datos:
        equipo.estado = datos['estado']

    # 4. Guardar cambios (Commit)
    try:
        db.session.commit()
        return jsonify({"mensaje": "Equipo actualizado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"mensaje": "Error al actualizar"}), 500
    # RUTA PARA ELIMINAR EQUIPO (DELETE)
@app.route('/api/equipos/<int:id>', methods=['DELETE'])
def eliminar_equipo(id):
    # 1. Buscar
    equipo = Equipo.query.get(id)
    if not equipo:
        return jsonify({"mensaje": "Equipo no encontrado"}), 404

    # 2. Eliminar y Confirmar
    try:
        db.session.delete(equipo)
        db.session.commit()
        return jsonify({"mensaje": "Equipo eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"mensaje": "Error al eliminar"}), 500
# --- 5. ARRANQUE ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)