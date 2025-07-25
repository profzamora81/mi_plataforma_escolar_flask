# app.py

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from config import Config # Asegúrate de que tienes un archivo config.py con tu configuración
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config.from_object(Config) # Carga la configuración desde config.py

db = SQLAlchemy(app) # Inicializa la base de datos con tu aplicación Flask
csrf = CSRFProtect(app) # Inicializa CSRFProtect con tu aplicación

# --- Configuración de Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app) # Inicializa Flask-Login con tu aplicación
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- User Loader para Flask-Login ---
# Esta función le dice a Flask-Login cómo cargar un usuario dado su ID
@login_manager.user_loader
def load_user(user_id):
    # Importa el modelo User SOLO AQUÍ, si es absolutamente necesario para evitar circular imports en otros lugares
    # O, mejor, asegúrate de que 'from models import User' ya esté hecho globalmente después de db = SQLAlchemy(app)
    # Para la práctica común, ya se debería haber importado globalmente.
    return User.query.get(int(user_id))

# Importa tus modelos (asegúrate de que estén definidos en models.py)
# Esta importación debe ir DESPUÉS de db = SQLAlchemy(app)
from models import User, GradeLevel, Subject, Grade, Announcement, Enrollment, SubjectActivityConfig, GradeChangeRequest

# Importa tus rutas (las crearemos en el siguiente paso o ya las tienes)
# Esto debe ir DESPUÉS de que app, db y los modelos estén inicializados.
import routes # Esto registrará las rutas definidas en routes.py

# Contexto de shell para facilitar el trabajo con la base de datos
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'GradeLevel': GradeLevel,
        'Subject': Subject,
        'Grade': Grade, # Incluye todos tus modelos para fácil acceso en el shell
        'Announcement': Announcement,
        'Enrollment': Enrollment,
        'SubjectActivityConfig': SubjectActivityConfig,
        'GradeChangeRequest': GradeChangeRequest,
        'generate_password_hash': generate_password_hash
    }

if __name__ == '__main__':
    app.run(debug=True)