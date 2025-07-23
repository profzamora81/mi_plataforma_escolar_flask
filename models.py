# models.py

from app import db # Importamos 'db' desde app.py
from datetime import datetime
from flask_login import UserMixin # ¡Nueva importación!
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin): # ¡Ahora hereda de UserMixin!
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128)) # Para contraseñas hasheadas
    role = db.Column(db.String(50), nullable=False, default='Estudiante') # e.g., 'Administrador', 'Profesor', 'Estudiante'
    first_name = db.Column(db.String(60))
    last_name = db.Column(db.String(60))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(200))
    date_of_birth = db.Column(db.Date)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación uno a muchos: Un profesor tiene muchas asignaturas
    subjects_taught = db.relationship('Subject', backref='teacher_obj', lazy=True, foreign_keys='Subject.teacher_id')

    # Métodos para Flask-Login
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} - {self.role}>"

class GradeLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    # Relación muchos a muchos con Subject a través de la tabla de unión
    # subjects = db.relationship('Subject', secondary='subject_grade_level', backref='grade_levels_obj')

    def __repr__(self):
        return f"<GradeLevel {self.name}>"

# Tabla de unión para la relación muchos a muchos entre Subject y GradeLevel
# Flask-SQLAlchemy necesita una tabla explícita para relaciones de muchos a muchos
subject_grade_level = db.Table('subject_grade_level',
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True),
    db.Column('grade_level_id', db.Integer, db.ForeignKey('grade_level.id'), primary_key=True)
)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Clave foránea al usuario que es el profesor
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # nullable=True permite que sea opcional

    # Relación muchos a muchos con GradeLevel
    grade_levels = db.relationship('GradeLevel', secondary=subject_grade_level, lazy='subquery',
                                   backref=db.backref('subjects', lazy=True))

    def __repr__(self):
        return f"<Subject {self.name} ({self.code})>"

# Aquí se pueden añadir más modelos (Course, Attendance, Grades, etc.)