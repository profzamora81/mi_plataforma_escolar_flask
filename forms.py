# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, IntegerField, FieldList, FormField, TextAreaField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange, Optional
from models import User, Subject, GradeLevel, Enrollment, SubjectActivityConfig, Grade # Importa los nuevos modelos
from wtforms_sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField

# Función para obtener solo los profesores
def get_teachers():
    return User.query.filter_by(role='Profesor').all()

class SubjectForm(FlaskForm): 
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
    student = QuerySelectField(
        'Estudiante',
        query_factory=lambda: User.query.filter_by(role='Estudiante').order_by(User.first_name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: f'{a.first_name} {a.last_name}',
        validators=[DataRequired()]
    )
    
    # No se usa QuerySelectField para activity_name y unit_number aquí,
    # ya que se poblarán dinámicamente o se basarán en la configuración de la asignatura.
    # Por ahora, los dejamos como StringField.
    # En la ruta, el profesor seleccionará la actividad específica que ya configuró.
    activity_name = StringField('Nombre de la Actividad/Parcial', validators=[DataRequired(), Length(max=128)])
    unit_number = SelectField('Unidad', choices=[
        ('Unidad I', 'Unidad I'),
        ('Unidad II', 'Unidad II'),
        ('Unidad III', 'Unidad III'),
        ('Unidad IV', 'Unidad IV'),
        ('N/A', 'N/A') # Para parciales que no encajen en una unidad específica
    ], validators=[DataRequired()])
    component_type = SelectField('Tipo de Componente', choices=[
        ('Zona', 'Zona'),
        ('Parcial', 'Parcial')
    ], validators=[DataRequired()])
    
    value = FloatField('Nota Obtenida', validators=[DataRequired(), NumberRange(min=0)]) # El rango max dependerá de la actividad

    submit = SubmitField('Guardar Nota')

    # Para validación del valor de la nota contra el punteo máximo de la actividad,
    # esto se hará en la ruta de Flask, no en el formulario directamente,
    # ya que el formulario no tiene acceso directo al SubjectActivityConfig.

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

# --- NUEVO: Formulario para Inscripciones (si el admin las gestiona directamente) ---
class EnrollmentForm(FlaskForm):
    student = QuerySelectField(
        'Estudiante',
        query_factory=lambda: User.query.filter_by(role='Estudiante').order_by(User.first_name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: f'{a.first_name} {a.last_name}',
        validators=[DataRequired()]
    )
    subject = QuerySelectField(
        'Asignatura',
        query_factory=lambda: Subject.query.order_by(Subject.name).all(),
        get_pk=lambda a: a.id,
        get_label=lambda a: a.name,
        validators=[DataRequired()]
    )
    submit = SubmitField('Inscribir Estudiante')

# ... (LoginForm, RegistrationForm, SubjectForm, AnnouncementForm, EnrollmentForm) ...

# --- NUEVO: Formulario para Solicitudes de Cambio de Nota ---
class GradeChangeRequestForm(FlaskForm):
    # HiddenField para pasar el ID de la nota que se quiere cambiar/eliminar
    grade_id = HiddenField(validators=[DataRequired()]) 
    
    # HiddenField para pasar el ID del estudiante (útil para validación/contexto en la ruta)
    student_id = HiddenField(validators=[DataRequired()])
    
    # HiddenField para pasar el ID de la asignatura (útil para validación/contexto en la ruta)
    subject_id = HiddenField(validators=[DataRequired()])

    request_type = SelectField('Tipo de Solicitud', 
                               choices=[('edit', 'Editar Nota'), ('delete', 'Eliminar Nota')], 
                               validators=[DataRequired()])
    
    # new_value será requerido solo si request_type es 'edit'
    new_value = FloatField('Nuevo Valor de la Nota (si es edición)', 
                           validators=[Optional(), NumberRange(min=0, message="El valor de la nota debe ser 0 o mayor.")])
    
    reason = TextAreaField('Razón del Cambio/Eliminación', 
                           validators=[DataRequired(), Length(min=10, max=500, message="La razón debe tener entre 10 y 500 caracteres.")])
    
    submit = SubmitField('Enviar Solicitud')

    def validate(self):
        initial_validation = super().validate()
        if not initial_validation:
            return False

        if self.request_type.data == 'edit':
            if self.new_value.data is None:
                self.new_value.errors.append('El nuevo valor de la nota es requerido para la edición.')
                return False
            if self.new_value.data < 0:
                self.new_value.errors.append('El nuevo valor no puede ser negativo.')
                return False
        elif self.request_type.data == 'delete':
            # Para una solicitud de eliminación, new_value no debería tener datos, o ser ignorado.
            # Asegurarse de que no se envíe un valor aquí si el tipo es delete.
            # Podrías agregar una validación para limpiar `new_value` si `request_type` es delete.
            pass # No hay validación especial para delete más allá de la razón.

        return True
    
# --- NUEVOS: Formularios para Configuración de Actividades ---

class SubjectActivityConfigItemForm(FlaskForm):
    """Formulario para un único item de configuración de actividad (dentro del FieldList)."""
    unit_number = SelectField('Unidad', choices=[
        ('Unidad I', 'Unidad I'),
        ('Unidad II', 'Unidad II'),
        ('Unidad III', 'Unidad III'),
        ('Unidad IV', 'Unidad IV')
    ], validators=[DataRequired()])
    activity_name = StringField('Nombre de la Actividad', validators=[DataRequired(), Length(max=128)])
    max_score = FloatField('Punteo Máximo', validators=[DataRequired(), NumberRange(min=0.1, max=60.0, message="El punteo debe ser entre 0.1 y 60.")])
    
    # Campo oculto para manejar el ID si se edita una actividad existente
    id = IntegerField('ID de Actividad (oculto)', render_kw={'type': 'hidden'})

    def validate_max_score(self, field):
        # Esta validación se hará a nivel de formulario principal para la suma total
        pass

class SubjectActivitiesConfigForm(FlaskForm):
    """Formulario principal para que el profesor configure las actividades de una asignatura."""
    
    activities = FieldList(
        FormField(SubjectActivityConfigItemForm), 
        min_entries=0, 
        max_entries=6, # Límite de 6 actividades
        label="Configuración de Actividades de Zona (Máx. 60 puntos)"
    )
    submit = SubmitField('Guardar Configuración de Actividades')

    def validate(self):
        if not super().validate():
            return False
        
        total_zone_score = 0
        for activity_form in self.activities.entries:
            # Solo sumar si la actividad está siendo realmente enviada (no vacía)
            if activity_form.form.activity_name.data and activity_form.form.max_score.data is not None:
                total_zone_score += activity_form.form.max_score.data
        
        if total_zone_score > 60:
            self.activities.errors = ['La suma total de los punteos de las actividades de zona no puede exceder los 60 puntos. Actualmente es: ' + str(total_zone_score)]
            return False
        
        return True
