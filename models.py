# models.py

from app import db # Importamos 'db' desde app.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for many-to-many relationship between Subject and GradeLevel
subject_grade_level_association = db.Table(
    'subject_grade_level_association',
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True),
    db.Column('grade_level_id', db.Integer, db.ForeignKey('grade_level.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Estudiante') # Roles: 'Estudiante', 'Profesor', 'Administrador'
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        """Genera un hash de la contraseña y lo guarda."""
        self.password = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    teacher_obj = db.relationship('User', backref='subjects_taught', lazy=True)

    grade_levels = db.relationship(
        'GradeLevel', secondary=subject_grade_level_association,
        back_populates='subjects'
    )
    activity_configs = db.relationship('SubjectActivityConfig', backref='subject_obj', lazy='dynamic')
    enrollments = db.relationship('Enrollment', backref='subject_obj', lazy='dynamic')

    def __repr__(self):
        return f'<Subject {self.name} ({self.code})>'

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    
    value = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    activity_name = db.Column(db.String(128), nullable=False) 
    unit_number = db.Column(db.String(20), nullable=False) 
    component_type = db.Column(db.String(20), nullable=False) # 'Zona', 'Parcial'
    
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)

    # NUEVA RELACIÓN: Solicitudes de cambio para esta nota
    change_requests = db.relationship('GradeChangeRequest', backref='grade', lazy='dynamic')

    student = db.relationship('User', backref='grades', lazy=True)
    subject = db.relationship('Subject', backref='grades', lazy=True)
    
    def __repr__(self):
        return f'<Grade {self.value} for {self.student.username} in {self.subject.name} - {self.activity_name} ({self.unit_number})>'

# --- NUEVO MODELO: ANNOUNCEMENT ---
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_role = db.Column(db.String(20), nullable=False)

    user = db.relationship('User', backref='announcements', lazy=True)

    def __repr__(self):
        return f'<Announcement {self.title} by {self.user.username}>'

# --- NUEVO MODELO: Enrollment (Inscripción de Estudiante a Asignatura) ---
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('student_id', 'subject_id', name='_student_subject_uc'),)

    def __repr__(self):
        return f'<Enrollment Student:{self.student_obj.username} Subject:{self.subject_obj.name}>'

class SubjectActivityConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    
    unit_number = db.Column(db.String(20), nullable=False)
    activity_number = db.Column(db.Integer, nullable=False)
    activity_name = db.Column(db.String(128), nullable=False)
    max_score = db.Column(db.Float, nullable=False)

    __table_args__ = (db.UniqueConstraint('subject_id', 'unit_number', 'activity_number', name='_subject_unit_activity_uc'),)

    def __repr__(self):
        return f'<SubjectActivityConfig {self.subject_obj.name} - {self.unit_number} - {self.activity_name} ({self.max_score} pts)>'

# --- NUEVO MODELO: GradeChangeRequest (Solicitud de Cambio de Nota) ---
class GradeChangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    
    # Quién solicitó el cambio (el profesor)
    requested_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    reason = db.Column(db.Text, nullable=False)
    
    request_type = db.Column(db.String(10), nullable=False) # 'edit' o 'delete'
    new_value = db.Column(db.Float, nullable=True) # Para solicitudes de 'edit', el nuevo valor de la nota

    status = db.Column(db.String(20), default='pending', nullable=False) # 'pending', 'approved', 'rejected'
    
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Quién aprobó/rechazó (el administrador)
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approval_date = db.Column(db.DateTime, nullable=True)

    # ¡¡¡AÑADE ESTAS DOS LÍNEAS!!! Son las que faltan.
    # Relación con el usuario que solicitó el cambio
    requested_by = db.relationship('User', backref='grade_requests_made', lazy=True, foreign_keys=[requested_by_user_id])
    # Relación con el usuario que aprobó/rechazó el cambio
    approved_by = db.relationship('User', backref='grade_requests_approved', lazy=True, foreign_keys=[approved_by_user_id])
    # La relación con el modelo Grade se maneja por backref='grade_obj' en el modelo Grade

    def __repr__(self):
        return f'<GradeChangeRequest ID:{self.id} Grade:{self.grade_id} Type:{self.request_type} Status:{self.status}>'
    
class GradeLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    subjects = db.relationship(
        'Subject', secondary=subject_grade_level_association,
        back_populates='grade_levels'
    )

    def __repr__(self):
        return f'<GradeLevel {self.name}>'    