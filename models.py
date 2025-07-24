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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False) # 'Administrador', 'Profesor', 'Estudiante'
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)

    # Relaciones:
    subjects_taught = db.relationship('Subject', backref='teacher_obj', lazy='dynamic', foreign_keys='Subject.teacher_id')
    announcements_created = db.relationship('Announcement', backref='user', lazy='dynamic')
    grades_received = db.relationship('Grade', backref='student', lazy='dynamic')
    enrollments = db.relationship('Enrollment', backref='student_obj', lazy='dynamic')
    
    # NUEVAS RELACIONES: Solicitudes de cambio de notas
    grade_change_requests_made = db.relationship('GradeChangeRequest', 
                                                foreign_keys='GradeChangeRequest.requested_by_user_id',
                                                backref='requested_by_user', 
                                                lazy='dynamic')
    grade_change_requests_approved = db.relationship('GradeChangeRequest', 
                                                    foreign_keys='GradeChangeRequest.approved_by_user_id',
                                                    backref='approved_by_user', 
                                                    lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class GradeLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))

    subjects = db.relationship(
        'Subject', secondary=subject_grade_level_association,
        back_populates='grade_levels'
    )

    def __repr__(self):
        return f'<GradeLevel {self.name}>'

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    grade_levels = db.relationship(
        'GradeLevel', secondary=subject_grade_level_association,
        back_populates='subjects'
    )
    grades = db.relationship('Grade', backref='subject', lazy='dynamic')
    activity_configs = db.relationship('SubjectActivityConfig', backref='subject_obj', lazy='dynamic')
    enrollments = db.relationship('Enrollment', backref='subject_obj', lazy='dynamic')

    def __repr__(self):
        return f'<Subject {self.name} ({self.code})>'

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    
    value = db.Column(db.Float, nullable=False)
    
    activity_name = db.Column(db.String(128), nullable=False) 
    unit_number = db.Column(db.String(20), nullable=False) 
    component_type = db.Column(db.String(20), nullable=False) # 'Zona', 'Parcial'
    
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)

    # NUEVA RELACIÓN: Solicitudes de cambio para esta nota
    change_requests = db.relationship('GradeChangeRequest', backref='grade', lazy='dynamic')


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

    def __repr__(self):
        return f'<GradeChangeRequest ID:{self.id} Grade:{self.grade_id} Type:{self.request_type} Status:{self.status}>'