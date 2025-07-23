# app.py

from flask import Flask, render_template, redirect, url_for, flash # Añade redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required # ¡Nuevas importaciones!
from werkzeug.security import generate_password_hash, check_password_hash # Para manejar contraseñas


app = Flask(__name__)
app.config.from_object(Config) # Carga la configuración desde config.py

db = SQLAlchemy(app) # Inicializa la base de datos con tu aplicación Flask

# --- Configuración de Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Importa tus modelos (asegúrate de que estén definidos en models.py)
from models import User, GradeLevel, Subject

# --- User Loader para Flask-Login ---
# Esta función le dice a Flask-Login cómo cargar un usuario dado su ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Importa tus rutas (las crearemos en el siguiente paso)
import routes

# Contexto de shell para facilitar el trabajo con la base de datos
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'GradeLevel': GradeLevel, 
        'Subject': Subject,
        'generate_password_hash': generate_password_hash
    }

if __name__ == '__main__':
    app.run(debug=True)