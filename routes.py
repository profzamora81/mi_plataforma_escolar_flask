# routes.py

from app import app, db # Asegúrate de que db esté importado
from models import User, Subject, GradeLevel, Grade, Announcement
from forms import SubjectForm, LoginForm, RegistrationForm, GradeForm, AnnouncementForm
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

# --- Rutas de Gestión de Notas por Profesor ---

@app.route('/profesor/asignatura/<int:subject_id>/notas', methods=['GET'])
@login_required
@teacher_required
def teacher_manage_grades(subject_id):
    # Verificar que la asignatura pertenezca al profesor logeado
    subject = Subject.query.get_or_404(subject_id)
    if subject.teacher_id != current_user.id:
        flash('No tienes permiso para gestionar notas de esta asignatura.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    # Obtener todos los estudiantes que tienen una nota en esta asignatura
    # Opcional: Podrías querer obtener todos los estudiantes del nivel de esta asignatura
    # For simplicity, let's get students who *already* have grades OR all students
    # currently we don't have a direct link between Student and GradeLevel in User model
    # Let's assume for now, any student can be graded in any subject assigned to their teacher
    
    # Obtener todas las notas registradas para esta asignatura
    grades = Grade.query.filter_by(subject_id=subject.id).order_by(Grade.student_id, Grade.bimestre).all()

    # Organizar las notas por estudiante para mostrarlas más fácilmente
    grades_by_student = {}
    for grade in grades:
        if grade.student.id not in grades_by_student:
            grades_by_student[grade.student.id] = {
                'student_obj': grade.student,
                'grades': []
            }
        grades_by_student[grade.student.id]['grades'].append(grade)

    # Si no tienes un sistema de inscripción, una forma simplista de obtener "todos" los estudiantes
    # que podrían recibir una nota en esta asignatura (ej. todos los estudiantes en el nivel de la asignatura)
    # Por simplicidad, por ahora, mostraremos todos los estudiantes que tienen una nota en esa asignatura.
    # En el futuro, necesitaríamos un modelo de "inscripción" de estudiante a asignatura/nivel.

    current_year = datetime.now().year
    return render_template('profesores/manage_grades.html',
                           title=f'Gestionar Notas de {subject.name}',
                           subject=subject,
                           grades_by_student=grades_by_student,
                           current_year=current_year)


@app.route('/profesor/asignatura/<int:subject_id>/nota/nueva', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_add_grade(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject.teacher_id != current_user.id:
        flash('No tienes permiso para añadir notas a esta asignatura.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    form = GradeForm()
    
    # ¡Importante! Filtrar los estudiantes para el QuerySelectField
    # Aquí es donde limitamos los estudiantes a los que un profesor puede calificar.
    # Por ahora, asumimos que puede calificar a cualquier 'Estudiante'
    # En un sistema real, un estudiante estaría 'inscrito' en esta asignatura.
    # Si quisieras limitar a estudiantes de los niveles de la asignatura:
    # student_ids_in_subject_levels = set()
    # for level in subject.grade_levels:
    #     for user_in_level in level.users_in_level: # Asumiendo una relación en User/GradeLevel
    #         student_ids_in_subject_levels.add(user_in_level.id)
    # form.student.query = User.query.filter(User.id.in_(student_ids_in_subject_levels)).filter_by(role='Estudiante').order_by(User.last_name)
    
    # Por ahora, mostramos todos los estudiantes tipo 'Estudiante'
    form.student.query = User.query.filter_by(role='Estudiante').order_by(User.last_name)

    if form.validate_on_submit():
        # Antes de guardar, verificar si ya existe una nota para este estudiante, asignatura y bimestre
        existing_grade = Grade.query.filter_by(
            student_id=form.student.data.id,
            subject_id=subject.id,
            bimestre=form.bimestre.data
        ).first()

        if existing_grade:
            flash(f'Ya existe una nota para {form.student.data.first_name} en {subject.name} para el {form.bimestre.data}. Por favor, edítala si deseas cambiarla.', 'warning')
            # Podrías redirigir a una página de edición o precargar el formulario con la nota existente
            return redirect(url_for('teacher_manage_grades', subject_id=subject.id))
        
        new_grade = Grade(
            student_id=form.student.data.id,
            subject_id=subject.id,
            value=form.value.data,
            bimestre=form.bimestre.data
        )
        db.session.add(new_grade)
        db.session.commit()
        flash('¡Nota registrada exitosamente!', 'success')
        return redirect(url_for('teacher_manage_grades', subject_id=subject.id))

    current_year = datetime.now().year
    return render_template('profesores/add_grade.html',
                           title=f'Añadir Nota a {subject.name}',
                           subject=subject,
                           form=form,
                           current_year=current_year)


@app.route('/profesor/nota/<int:grade_id>/editar', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_edit_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    
    # Verificar que la nota pertenezca a una asignatura del profesor logeado
    if grade.subject.teacher_id != current_user.id:
        flash('No tienes permiso para editar esta nota.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    form = GradeForm(obj=grade) # Precarga el formulario con los datos de la nota existente
    
    # Filtrar estudiantes (igual que en add_grade)
    form.student.query = User.query.filter_by(role='Estudiante').order_by(User.last_name)
    # Deshabilitar la selección de estudiante y bimestre en la edición para evitar errores lógicos
    form.student.render_kw = {'disabled': 'disabled'}
    form.bimestre.render_kw = {'disabled': 'disabled'}

    if form.validate_on_submit():
        grade.value = form.value.data
        # student_id y bimestre NO se editan aquí, se asume que se creó mal y se borraría para recrear
        # O se permitiría editarlos si se considera parte de la edición
        db.session.commit()
        flash('¡Nota actualizada exitosamente!', 'success')
        return redirect(url_for('teacher_manage_grades', subject_id=grade.subject.id))

    current_year = datetime.now().year
    return render_template('profesores/edit_grade.html',
                           title=f'Editar Nota de {grade.student.first_name} en {grade.subject.name}',
                           grade=grade,
                           form=form,
                           current_year=current_year)

@app.route('/profesor/nota/<int:grade_id>/eliminar', methods=['POST'])
@login_required
@teacher_required
def teacher_delete_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    
    # Verificar que la nota pertenezca a una asignatura del profesor logeado
    if grade.subject.teacher_id != current_user.id:
        flash('No tienes permiso para eliminar esta nota.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    subject_id = grade.subject.id # Guarda el ID de la asignatura antes de borrar la nota
    db.session.delete(grade)
    db.session.commit()
    flash('¡Nota eliminada exitosamente!', 'info')
    return redirect(url_for('teacher_manage_grades', subject_id=subject_id))

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
    profesor = current_user
    subjects_taught = Subject.query.filter_by(teacher_id=profesor.id).all()

    relevant_announcements = Announcement.query.filter(
        (Announcement.target_role == 'Todos') | (Announcement.target_role == 'Profesor')
    ).order_by(Announcement.date_posted.desc()).all()

    current_year = datetime.now().year
    return render_template('profesores/teacher_dashboard.html', 
                           profesor=profesor,
                           subjects_taught=subjects_taught,
                           relevant_announcements=relevant_announcements,
                           title=f'Dashboard de {profesor.first_name}',
                           current_year=current_year)

# --- Dashboard de Estudiante ---
@app.route('/estudiante/dashboard')
@login_required
@student_required # Solo estudiantes
def student_dashboard():    
    estudiante = current_user
    subjects_data = []

    subjects_of_student = db.session.query(Subject).join(Grade).filter(Grade.student_id == estudiante.id).distinct().all()

    for subject in subjects_of_student:
        grades_for_subject = Grade.query.filter_by(
            student_id=estudiante.id, 
            subject_id=subject.id
        ).all()

        subject_average_grade = 0
        if grades_for_subject: # Solo calcular si hay notas para evitar división por cero
            subject_total_grade_value = sum(g.value for g in grades_for_subject)
            subject_average_grade = subject_total_grade_value / len(grades_for_subject)
        
        subjects_data.append({
            'subject_obj': subject,
            'average_grade': subject_average_grade
        })

        all_student_grades = Grade.query.filter_by(student_id=estudiante.id).all()
        overall_total_grade_value = sum(g.value for g in all_student_grades)
        overall_average_grade = overall_total_grade_value / len(all_student_grades) if all_student_grades else 0

        relevant_announcements = Announcement.query.filter(
        (Announcement.target_role == 'Todos') | (Announcement.target_role == 'Estudiante')
        ).order_by(Announcement.date_posted.desc()).all()

    current_year = datetime.now().year
    return render_template('estudiantes/student_dashboard.html', 
                           estudiante=estudiante,
                           subjects_data=subjects_data,
                           overall_average_grade=overall_average_grade,
                           relevant_announcements=relevant_announcements,
                           title=f'Dashboard de {estudiante.first_name}',
                           current_year=current_year)

# --- Ruta para Estudiante: Ver Notas por Asignatura ---
@app.route('/estudiante/asignatura/<int:subject_id>/mis_notas')
@login_required
@student_required
def student_view_grades(subject_id):
    estudiante = current_user
    subject = Subject.query.get_or_404(subject_id)

    # Obtener todas las notas del estudiante para esta asignatura
    grades = Grade.query.filter_by(student_id=estudiante.id, subject_id=subject.id).order_by(Grade.bimestre).all()

    # Opcional: Calcular promedio si hay notas
    total_grade_value = sum(g.value for g in grades)
    average_grade = total_grade_value / len(grades) if grades else 0

    current_year = datetime.now().year
    return render_template('estudiantes/view_grades.html',
                           title=f'Mis Notas en {subject.name}',
                           estudiante=estudiante,
                           subject=subject,
                           grades=grades,
                           average_grade=average_grade,
                           current_year=current_year)

# --- Rutas de Gestión de Anuncios (Admin) ---
@app.route('/admin/anuncios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_announcement():
    form = AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            target_role=form.target_role.data,
            user=current_user # El usuario logeado es quien publica el anuncio
        )
        db.session.add(announcement)
        db.session.commit()
        flash('¡Anuncio publicado exitosamente!', 'success')
        return redirect(url_for('admin_list_announcements'))
    
    current_year = datetime.now().year
    return render_template('announcements/create_announcement.html',
                           title='Publicar Nuevo Anuncio (Admin)',
                           form=form,
                           current_year=current_year)

@app.route('/admin/anuncios', methods=['GET'])
@login_required
@admin_required
def admin_list_announcements():
    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).all()
    
    current_year = datetime.now().year
    return render_template('announcements/list_announcements.html',
                           title='Gestionar Anuncios (Admin)',
                           announcements=announcements,
                           current_year=current_year)