import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import os
import random
import string

load_dotenv()  # Cargar variables de entorno desde el archivo .env

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Necesario para mostrar mensajes flash

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelo de datos para la base de datos
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    contrasena = db.Column(db.String(100), nullable=False)
    habilidad = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(100), nullable=False)
    codigo_verificacion = db.Column(db.String(6), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def generar_codigo_verificacion():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def show_register():
    return render_template('register.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    nombre = request.form['name']
    correo = request.form['email']
    contrasena = request.form['password']
    habilidad = request.form['skill']
    ubicacion = request.form['location']
    codigo_verificacion = generar_codigo_verificacion()
    nuevo_usuario = Usuario(nombre=nombre, correo=correo, contrasena=contrasena, habilidad=habilidad, ubicacion=ubicacion, codigo_verificacion=codigo_verificacion)
    db.session.add(nuevo_usuario)
    db.session.commit()
    try:
        enviar_correo_verificacion(correo, codigo_verificacion)
    except Exception as e:
        logging.error(f'Error sending email: {e}')
        return 'Error enviando correo de verificación. Por favor, contacta al soporte técnico.'
    return redirect(url_for('login'))

def enviar_correo_verificacion(correo, codigo_verificacion):
    msg = Message('Código de Verificación - RivalTeamFinder', sender=os.getenv('MAIL_USERNAME'), recipients=[correo])
    msg.body = f'Tu código de verificación es: {codigo_verificacion}'
    mail.send(msg)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/iniciar_sesion', methods=['POST'])
def iniciar_sesion():
    correo = request.form['email']
    contrasena = request.form['password']
    usuario = Usuario.query.filter_by(correo=correo).first()
    if usuario and usuario.contrasena == contrasena:
        login_user(usuario)
        flash('Inicio de sesión exitoso')
        return redirect(url_for('perfil'))
    else:
        flash('Correo o contraseña incorrectos')
        return redirect(url_for('login'))

@app.route('/buscar')
@login_required
def buscar():
    return render_template('buscar.html')

@app.route('/buscar_rivales', methods=['GET'])
@login_required
def buscar_rivales():
    ubicacion = request.args.get('location')
    habilidad = request.args.get('skill')
    edad = request.args.get('age')
    genero = request.args.get('gender')
    deporte = request.args.get('sport')
    
    # Filtro por múltiples criterios
    query = Usuario.query
    if ubicacion:
        query = query.filter_by(ubicacion=ubicacion)
    if habilidad:
        query = query.filter_by(habilidad=habilidad)
    if edad:
        query = query.filter_by(edad=edad)
    if genero:
        query = query.filter_by(genero=genero)
    if deporte:
        query = query.filter_by(deporte=deporte)
    
    resultados = query.all()
    return render_template('buscar.html', resultados=resultados)

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html', usuario=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente')
    return redirect(url_for('index'))

@app.route('/usuarios')
def mostrar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/eliminar/<int:id>')
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return redirect(url_for('mostrar_usuarios'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)













