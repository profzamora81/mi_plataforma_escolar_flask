# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectMultipleField, SubmitField, PasswordField, BooleanField, SelectField # ¡Nuevos campos!
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from models import GradeLevel, User # Importa User

# Función para obtener solo los profesores
def get_teachers():
    return User.query.filter_by(role='Profesor').all()

class SubjectForm(FlaskForm): # ¡ESTA ES LA CLASE QUE FALTABA!
    name = StringField('Nombre de la Asignatura', validators=[DataRequired(), Length(min=2, max=100)])
    code = StringField('Código de la Asignatura', validators=[DataRequired(), Length(min=2, max=20)])
    description = TextAreaField('Descripción (Opcional)')
    
    # Campo para seleccionar el Profesor (solo roles de Profesor)
    teacher = QuerySelectField(
        'Profesor Asignado',
        query_factory=get_teachers, # Usa la función para obtener solo profesores
        get_label=lambda user: f"{user.first_name} {user.last_name} ({user.username})", # Cómo mostrar el profesor
        allow_blank=True, # Permite dejarlo en blanco si una asignatura no tiene profesor asignado aún
        blank_text='-- Seleccionar Profesor --'
    )
    
    # Campo para seleccionar Nivel/Grado (relación Muchos a Muchos)
    grade_levels = QuerySelectMultipleField(
        'Niveles Educativos',
        query_factory=lambda: GradeLevel.query.all(),
        get_label='name',
        validators=[DataRequired(message="Debe seleccionar al menos un nivel educativo.")], # Asegura que se seleccione al menos uno
        widget=None, # Para que se renderice como un select múltiple HTML por defecto
        option_widget=None # Para evitar que cada opción sea un widget separado
    )
    
    submit = SubmitField('Guardar Asignatura')

# --- Formularios de Autenticación ---

class LoginForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme') # Para recordar la sesión
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    password2 = PasswordField(
        'Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Rol', choices=[('Estudiante', 'Estudiante'), ('Profesor', 'Profesor'), ('Administrador', 'Administrador')], validators=[DataRequired()])
    first_name = StringField('Nombre', validators=[DataRequired()])
    last_name = StringField('Apellido', validators=[DataRequired()])
    
    submit = SubmitField('Registrar')

    # Validadores personalizados para asegurar que el nombre de usuario y el email sean únicos
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Ese nombre de usuario ya está en uso. Por favor, elige uno diferente.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Ese email ya está registrado. Por favor, usa uno diferente.')