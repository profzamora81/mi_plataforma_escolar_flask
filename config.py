# config.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_muy_dificil_de_adivinar_y_cambiar'
    # Configuración de la base de datos SQLite
    # Flask-SQLAlchemy necesita la URL de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Desactiva el seguimiento de modificaciones para ahorrar recursos