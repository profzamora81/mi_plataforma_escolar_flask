# routes.py

from app import app, db # Asegúrate de que db esté importado
from models import User, Subject, GradeLevel
from forms import SubjectForm, LoginForm, RegistrationForm # ¡Nuevos formularios!
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from flask_login import login_user, logout_user, current_user, login_required

# --- Rutas Públicas (p. ej., página de inicio) ---
@app.route('/')
@app.route('/home')
def home():
    current_year = datetime.now().year # Obtiene el año actual
    return render_template('index.html', title='Inicio', current_year=current_year) # Pásalo al contexto

@app.route('/about')
def about():
    current_year = datetime.now().year # También necesitas pasarlo aquí si usas base.html
    return render_template('about.html', title='Acerca de', current_year=current_year)

# --- Rutas de Autenticación ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Si el usuario ya está logeado, redirigir a home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data) # Hashear la contraseña
        db.session.add(user)
        db.session.commit()
        flash('¡Tu cuenta ha sido creada exitosamente! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    
    current_year = datetime.now().year
    return render_template('auth/register.html', title='Registrar', form=form, current_year=current_year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está logeado, redirigir a home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Nombre de usuario o contraseña inválidos', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data) # Logear al usuario
        # Redirigir al usuario a la página que intentaba acceder antes de ser redirigido al login
        next_page = request.args.get('next')
        return redirect(next_page or url_for('home'))
    
    current_year = datetime.now().year
    return render_template('auth/login.html', title='Iniciar Sesión', form=form, current_year=current_year)

@app.route('/logout')
@login_required # Requiere que el usuario esté logeado para hacer logout
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('home'))

# --- Decoradores de Rol para Autorización ---
# Necesitamos funciones auxiliares para verificar roles
def role_required(role_name):
    def decorator(f):
        @wraps(f) # Importa wraps desde functools
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Necesitas iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('login', next=request.url))
            if current_user.role != role_name and current_user.role != 'Administrador': # Admin siempre tiene acceso
                flash(f'No tienes permiso para acceder a esta página. Tu rol es {current_user.role}.', 'danger')
                return redirect(url_for('home')) # O a un dashboard de su rol
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Decoradores específicos para roles
from functools import wraps # ¡Importar wraps!

def admin_required(f):
    return role_required('Administrador')(f)

def teacher_required(f):
    return role_required('Profesor')(f)

def student_required(f):
    return role_required('Estudiante')(f)


# --- Rutas de Profesores ---
@app.route('/profesores')
@login_required
def listar_profesores():
    profesores = User.query.filter_by(role='Profesor').all()
    current_year = datetime.now().year # Y aquí
    return render_template('profesores/lista_profesores.html', profesores=profesores, title='Profesores', current_year=current_year)

@app.route('/profesores/<int:user_id>/asignaturas')
@login_required
def asignaturas_profesor(user_id):
    profesor = User.query.get_or_404(user_id)
    asignaturas = profesor.subjects_taught
    current_year = datetime.now().year # Y aquí
    return render_template('profesores/asignaturas_profesor.html', profesor=profesor, asignaturas=asignaturas, title=f'Asignaturas de {profesor.first_name}', current_year=current_year)

# --- Rutas de Gestión de Asignaturas por ADMINISTRADORES ---

@app.route('/admin/asignaturas/nueva', methods=['GET', 'POST'])
@login_required # Requiere login
@admin_required # ¡Solo administradores!
def admin_create_subject():
    form = SubjectForm()

    if form.validate_on_submit():
        selected_teacher = form.teacher.data 

        new_subject = Subject(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            teacher_obj=selected_teacher
        )
        
        for grade_level in form.grade_levels.data:
            new_subject.grade_levels.append(grade_level)

        db.session.add(new_subject)
        db.session.commit()
        flash('¡Asignatura creada exitosamente!', 'success')
        return redirect(url_for('admin_list_subjects'))

    current_year = datetime.now().year
    return render_template('subjects/create_subject.html', title='Crear Nueva Asignatura (Admin)', form=form, current_year=current_year)

@app.route('/admin/asignaturas', methods=['GET'])
@login_required # Requiere login
@admin_required # ¡Solo administradores!
def admin_list_subjects():
    subjects = Subject.query.all()
    current_year = datetime.now().year
    return render_template('subjects/admin_list_subjects.html', subjects=subjects, title='Gestión de Asignaturas (Admin)', current_year=current_year)

# --- Dashboard de Profesor (¡Nuevo!) ---
@app.route('/profesor/dashboard')
@login_required
@teacher_required # Solo profesores
def teacher_dashboard():
    # current_user es el objeto User del profesor logeado
    profesor_asignado = current_user
    asignaturas = profesor_asignado.subjects_taught # Obtiene las asignaturas de ESTE profesor

    current_year = datetime.now().year
    return render_template('profesores/teacher_dashboard.html', 
                           profesor=profesor_asignado, 
                           asignaturas=asignaturas, 
                           title=f'Dashboard de {profesor_asignado.first_name}',
                           current_year=current_year)

# --- Dashboard de Estudiante (¡Nuevo!) ---
@app.route('/estudiante/dashboard')
@login_required
@student_required # Solo estudiantes
def student_dashboard():
    # Aquí iría la lógica para mostrar las notas del estudiante logeado
    # Por ahora, solo un mensaje
    current_year = datetime.now().year
    return render_template('estudiantes/student_dashboard.html', 
                           title=f'Dashboard de {current_user.first_name}',
                           current_year=current_year)