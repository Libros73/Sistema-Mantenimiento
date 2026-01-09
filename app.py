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

# --- 3. MODELOS DE LA BASE DE DATOS (Las Tablas) ---

# Tabla de Usuarios (Para futuros logins)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Tabla de Equipos (El Inventario GNB)
class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)      
    tipo = db.Column(db.String(50), nullable=False)         
    serial = db.Column(db.String(50), unique=True)          
    ubicacion = db.Column(db.String(100), nullable=False)   
    estado = db.Column(db.String(20), default='Operativo') 

    # Función para convertir a JSON (Para reportes futuros)
    def to_json(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "serial": self.serial,
            "ubicacion": self.ubicacion,
            "estado": self.estado
        }

# Función necesaria para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Crear las tablas automáticamente al iniciar
with app.app_context():
    db.create_all()

# --- 4. RUTAS DEL SISTEMA ---

@app.route('/')
def dashboard():
    return "<h1>🏗️ Sistema de Mantenimiento GNB - En Construcción</h1>"

# RUTA DE INICIALIZACIÓN (Solo la usaremos una vez)
@app.route('/setup-inicial')
def setup_inicial():
    # 1. Verificamos si ya hay equipos para no duplicar
    if Equipo.query.first():
        return "¡El inventario ya tiene datos! No es necesario inicializar."

    # 2. Creamos 3 equipos de prueba
    e1 = Equipo(nombre="Panel Principal Fike", tipo="Panel Control", serial="FK-001", ubicacion="Sótano 1 - Cuarto Control")
    e2 = Equipo(nombre="Sensor Humo Servidores", tipo="Sensor Fotoeléctrico", serial="SH-102", ubicacion="Piso 2 - Data Center")
    e3 = Equipo(nombre="Estación Manual Lobby", tipo="Palanca", serial="EM-005", ubicacion="Lobby Principal")

    # 3. Guardamos en la DB
    db.session.add_all([e1, e2, e3])
    db.session.commit()

    return "✅ Inventario Inicial Cargado con Éxito. ¡La Base de Datos responde!"

# --- 5. ARRANQUE ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)