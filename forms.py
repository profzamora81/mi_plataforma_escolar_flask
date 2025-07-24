# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectMultipleField, SubmitField, PasswordField, BooleanField, SelectField, FloatField # ¡Nuevos campos!
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

# --- Nuevo Formulario: GradeForm ---
class GradeForm(FlaskForm):
    # Campo para el valor de la nota
    value = FloatField('Nota', validators=[DataRequired(message="La nota es obligatoria.")])

    # Campo para seleccionar el estudiante (los estudiantes se filtrarán por asignatura en la ruta)
    # Por ahora, tendrá todos los estudiantes. La lógica de filtro por asignatura se hará en la ruta/vista.
    student = QuerySelectField(
        'Estudiante',
        query_factory=lambda: User.query.filter_by(role='Estudiante').order_by(User.last_name).all(),
        get_label=lambda user: f"{user.first_name} {user.last_name} ({user.username})",
        validators=[DataRequired(message="Debe seleccionar un estudiante.")],
        allow_blank=False
    )
    
    # Campo para el bimestre/período
    bimestre = SelectField(
        'Bimestre/Período',
        choices=[
            ('Bimestre 1', 'Bimestre 1'),
            ('Bimestre 2', 'Bimestre 2'),
            ('Bimestre 3', 'Bimestre 3'),
            ('Bimestre 4', 'Bimestre 4'),
            ('Examen Final', 'Examen Final') # Puedes añadir más opciones si es necesario
        ],
        validators=[DataRequired(message="Debe seleccionar un bimestre.")]
    )

    submit = SubmitField('Guardar Nota')

# --- Formulario de Anuncios ---
class AnnouncementForm(FlaskForm):
    title = StringField('Título del Anuncio', validators=[DataRequired(), Length(min=5, max=100)])
    content = TextAreaField('Contenido del Anuncio', validators=[DataRequired()])
    
    target_role = SelectField('Dirigido a', choices=[
        ('Todos', 'Todos'),
        ('Estudiante', 'Estudiantes'),
        ('Profesor', 'Profesores'),
        ('Administrador', 'Administradores')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Publicar Anuncio')

    # Para el campo 'user' (quién lo publica), no lo incluimos directamente en el formulario
    # Lo asignaremos automáticamente en la ruta usando current_user.id