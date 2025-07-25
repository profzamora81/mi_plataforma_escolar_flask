# routes.py

from app import app, db 
from models import User, Subject, GradeLevel, Grade, Announcement, Enrollment, SubjectActivityConfig, GradeChangeRequest # ¡Nuevas importaciones!
from forms import SubjectForm, LoginForm, RegistrationForm, GradeForm, AnnouncementForm, SubjectActivitiesConfigForm, SubjectActivityConfigItemForm # Importaciones existentes
from forms import GradeChangeRequestForm 
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps 
from wtforms.validators import DataRequired, Length, NumberRange 


# --- Decoradores de Rol ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Administrador':
            flash('Acceso no autorizado. Se requiere rol de Administrador.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Profesor':
            flash('Acceso no autorizado. Se requiere rol de Profesor.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Estudiante':
            flash('Acceso no autorizado. Se requiere rol de Estudiante.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rutas Públicas ---
@app.route('/')
@app.route('/home')
def home():
    current_year = datetime.now().year
    return render_template('index.html', title='Inicio', current_year=current_year)

@app.route('/about')
def about():
    current_year = datetime.now().year
    return render_template('about.html', title='Acerca de', current_year=current_year)

# --- Rutas de Autenticación ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Tu cuenta ha sido creada exitosamente!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registrarse', form=form, current_year=datetime.now().year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'Administrador':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'Profesor':
            return redirect(url_for('teacher_dashboard'))
        elif current_user.role == 'Estudiante':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña inválidos', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        flash('Has iniciado sesión exitosamente!', 'success')
        
        if user.role == 'Administrador':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'Profesor':
            return redirect(url_for('teacher_dashboard'))
        elif user.role == 'Estudiante':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('home'))
            
    return render_template('login.html', title='Iniciar Sesión', form=form, current_year=datetime.now().year)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('home'))

# --- Dashboard del Administrador ---
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    subjects = Subject.query.all()
    users = User.query.all()
    
    # Obtener solicitudes de cambio de notas pendientes
    pending_grade_requests = GradeChangeRequest.query.filter_by(status='pending').order_by(GradeChangeRequest.request_date.asc()).all()

    # Obtener anuncios para el administrador ---
    admin_announcements = Announcement.query.filter(
        (Announcement.target_role == 'Todos') | (Announcement.target_role == 'Administrador')
    ).order_by(Announcement.date_posted.desc()).all()

    current_year = datetime.now().year
    return render_template('admin/admin_dashboard.html', 
                           title='Dashboard de Administrador',
                           subjects=subjects,
                           users=users,
                           pending_grade_requests=pending_grade_requests, # Pasa las solicitudes al template
                           current_year=current_year)

# --- Gestión de Asignaturas (Admin) ---
@app.route('/admin/asignaturas')
@login_required
@admin_required
def admin_list_subjects():
    subjects = Subject.query.all()
    current_year = datetime.now().year
    return render_template('admin/list_subjects.html', 
                           title='Gestión de Asignaturas', 
                           subjects=subjects, 
                           current_year=current_year)

@app.route('/admin/asignatura/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_subject():
    form = SubjectForm()
    if form.validate_on_submit():
        teacher_obj = form.teacher.data 
        
        subject = Subject(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            teacher_obj=teacher_obj 
        )
        
        for level in form.grade_levels.data:
            subject.grade_levels.append(level)
            
        db.session.add(subject)
        db.session.commit()
        flash('Asignatura creada exitosamente!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_subject.html', title='Crear Asignatura', form=form, current_year=datetime.now().year)

@app.route('/admin/asignatura/<int:subject_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    form = SubjectForm(obj=subject) 

    if form.validate_on_submit():
        form.populate_obj(subject) 
        
        subject.grade_levels.clear() 
        for level in form.grade_levels.data:
            subject.grade_levels.append(level) 
            
        db.session.commit()
        flash('Asignatura actualizada exitosamente!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/edit_subject.html', title='Editar Asignatura', form=form, subject=subject, current_year=datetime.now().year)

@app.route('/admin/asignatura/<int:subject_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def admin_delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Asignatura eliminada exitosamente!', 'success')
    return redirect(url_for('admin_dashboard'))

# --- Gestión de Anuncios (Admin) ---
@app.route('/admin/anuncio/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_announcement():
    form = AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            target_role=form.target_role.data,
            user=current_user 
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Anuncio publicado exitosamente!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('announcements/create_announcement.html', title='Crear Anuncio', form=form, current_year=datetime.now().year)

# --- NUEVAS RUTAS ADMIN: Gestión de Solicitudes de Cambio de Notas ---
@app.route('/admin/solicitudes_cambio_notas')
@login_required
@admin_required
def admin_view_grade_change_requests():
    pending_requests = GradeChangeRequest.query.filter_by(status='pending').order_by(GradeChangeRequest.request_date.asc()).all()
    approved_requests = GradeChangeRequest.query.filter_by(status='approved').order_by(GradeChangeRequest.approval_date.desc()).all()
    rejected_requests = GradeChangeRequest.query.filter_by(status='rejected').order_by(GradeChangeRequest.approval_date.desc()).all()
    
    current_year = datetime.now().year
    return render_template('admin/manage_grade_requests.html',
                           title='Gestión de Solicitudes de Cambio de Notas',
                           pending_requests=pending_requests,
                           approved_requests=approved_requests,
                           rejected_requests=rejected_requests,
                           current_year=current_year)

@app.route('/admin/solicitud_cambio_nota/<int:request_id>/<action>', methods=['POST'])
@login_required
@admin_required
def admin_process_grade_change_request(request_id, action):
    req = GradeChangeRequest.query.get_or_404(request_id)

    if req.status != 'pending':
        flash('Esta solicitud ya ha sido procesada.', 'warning')
        return redirect(url_for('admin_view_grade_change_requests'))

    if action == 'approve':
        grade = req.grade # Accede a la nota relacionada
        if req.request_type == 'edit':
            grade.value = req.new_value
            flash(f'Nota de {grade.student.first_name} en {grade.subject.name} (Actividad: {grade.activity_name}) actualizada a {req.new_value}.', 'success')
        elif req.request_type == 'delete':
            db.session.delete(grade)
            flash(f'Nota de {grade.student.first_name} en {grade.subject.name} (Actividad: {grade.activity_name}) eliminada.', 'success')
        
        req.status = 'approved'
        req.approved_by_user_id = current_user.id
        req.approval_date = datetime.utcnow()
        db.session.commit()
        flash(f'Solicitud de cambio de nota aprobada para {grade.student.first_name}.', 'success')
    elif action == 'reject':
        req.status = 'rejected'
        req.approved_by_user_id = current_user.id
        req.approval_date = datetime.utcnow()
        db.session.commit()
        flash('Solicitud de cambio de nota rechazada.', 'info')
    else:
        flash('Acción no válida.', 'danger')

    return redirect(url_for('admin_view_grade_change_requests'))

# --- Gestión de Usuarios (Admin) ---
@app.route('/admin/usuarios')
@login_required
@admin_required
def admin_manage_users():
    users = User.query.all()
    current_year = datetime.now().year
    return render_template('admin/manage_users.html', title='Gestionar Usuarios', users=users, current_year=current_year)

# NUEVA RUTA: Listar Profesores (Pública)
# Esta ruta es para que cualquier usuario pueda ver la lista de profesores sin necesidad de autenticación
@app.route('/profesores') 
def listar_profesores(): 
    # Obtener solo usuarios con rol 'Profesor'
    professors = User.query.filter_by(role='Profesor').order_by(User.last_name).all()
    current_year = datetime.now().year
    return render_template('public_list_teachers.html', # Asegúrate de que esta plantilla exista
                           title='Nuestros Profesores', 
                           professors=professors, 
                           current_year=current_year)

# NUEVA RUTA: Listar Profesores
@app.route('/admin/listar_profesores')
@login_required
@admin_required
def admin_list_teachers():
    professors = User.query.filter_by(role='Profesor').order_by(User.last_name).all()
    current_year = datetime.now().year
    return render_template('admin/list_teachers.html',
                           title='Lista de Profesores', 
                           professors=professors, 
                           current_year=current_year)

# --- Dashboard de Profesor ---
@app.route('/profesor/dashboard')
@login_required
@teacher_required 
def teacher_dashboard():
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


# --- Ruta: Configuración de Actividades para una Asignatura (Profesor) ---
@app.route('/profesor/asignatura/<int:subject_id>/configurar_actividades', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_configure_subject_activities(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    if subject.teacher_id != current_user.id:
        flash('No tienes permiso para configurar esta asignatura.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    form = SubjectActivitiesConfigForm()

    if request.method == 'GET':
        existing_configs = SubjectActivityConfig.query.filter_by(subject_id=subject.id).order_by(
            SubjectActivityConfig.unit_number, SubjectActivityConfig.activity_number).all()
        
        while len(form.activities) > 0:
            form.activities.pop_entry()

        for config in existing_configs:
            activity_entry = form.activities.append_entry()
            activity_entry.form.id.data = config.id
            activity_entry.form.unit_number.data = config.unit_number
            activity_entry.form.activity_name.data = config.activity_name
            activity_entry.form.max_score.data = config.max_score
        
        if not existing_configs:
            for _ in range(4): 
                form.activities.append_entry()

    if form.validate_on_submit():
        existing_config_ids = {config.id for config in SubjectActivityConfig.query.filter_by(subject_id=subject.id).all()}
        submitted_config_ids = set()

        for entry_form in form.activities.entries:
            if entry_form.form.activity_name.data and entry_form.form.max_score.data is not None:
                config_id = entry_form.form.id.data
                
                if config_id: 
                    config = SubjectActivityConfig.query.get(config_id)
                    if config and config.subject_id == subject.id: 
                        config.unit_number = entry_form.form.unit_number.data
                        config.activity_name = entry_form.form.activity_name.data
                        config.max_score = entry_form.form.max_score.data
                        submitted_config_ids.add(config_id)
                    else:
                        flash(f'Error: Intento de modificar una configuración no válida con ID {config_id}.', 'warning')
                        continue 
                else: 
                    new_config = SubjectActivityConfig(
                        subject_id=subject.id,
                        unit_number=entry_form.form.unit_number.data,
                        activity_name=entry_form.form.activity_name.data,
                        max_score=entry_form.form.max_score.data
                    )
                    db.session.add(new_config)
        
        configs_to_delete = existing_config_ids - submitted_config_ids
        for config_id in configs_to_delete:
            config = SubjectActivityConfig.query.get(config_id)
            if config:
                db.session.delete(config)

        db.session.commit()
        flash('Configuración de actividades guardada exitosamente!', 'success')
        return redirect(url_for('teacher_dashboard'))
    
    current_year = datetime.now().year
    return render_template('profesores/configure_activities.html',
                           title=f'Configurar Actividades: {subject.name}',
                           subject=subject,
                           form=form,
                           current_year=current_year)


# --- Ruta para Profesor: Gestionar Notas de una Asignatura ---
# ESTA ES LA RUTA PRINCIPAL PARA LA GESTIÓN DE NOTAS DEL PROFESOR
@app.route('/profesor/asignatura/<int:subject_id>/gestionar_notas')
@login_required
@teacher_required
def teacher_manage_grades(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    if subject.teacher_id != current_user.id:
        flash('No tienes permiso para gestionar notas en esta asignatura.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    enrolled_students = [e.student_obj for e in Enrollment.query.filter_by(subject_id=subject.id).all()]
    
    configured_activities = SubjectActivityConfig.query.filter_by(subject_id=subject.id).order_by(
        SubjectActivityConfig.unit_number, SubjectActivityConfig.activity_number).all()

    grades_data = {}
    for student in enrolled_students:
        grades_data[student.id] = {}
        for activity_config in configured_activities:
            grade = Grade.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                activity_name=activity_config.activity_name,
                unit_number=activity_config.unit_number,
                component_type='Zona' 
            ).first()
            grades_data[student.id][activity_config.id] = grade 
        
        parciales = Grade.query.filter_by(
            student_id=student.id,
            subject_id=subject.id,
            component_type='Parcial'
        ).order_by(Grade.activity_name).all() 
        grades_data[student.id]['parciales'] = parciales


    current_year = datetime.now().year
    return render_template('profesores/manage_grades.html',
                           title=f'Gestionar Notas: {subject.name}',
                           subject=subject,
                           enrolled_students=enrolled_students,
                           configured_activities=configured_activities,
                           grades_data=grades_data,
                           current_year=current_year)


# --- NUEVA RUTA: Profesor solicita añadir/editar nota ---
# El profesor ya NO puede añadir/editar directamente, debe solicitar.
@app.route('/profesor/asignatura/<int:subject_id>/estudiante/<int:student_id>/solicitar_nota', methods=['GET', 'POST'])
@app.route('/profesor/asignatura/<int:subject_id>/estudiante/<int:student_id>/solicitar_nota/<int:grade_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_request_grade_change(subject_id, student_id, grade_id=None):
    subject = Subject.query.get_or_404(subject_id)
    student = User.query.get_or_404(student_id)

    if subject.teacher_id != current_user.id:
        flash('No tienes permiso para gestionar notas en esta asignatura.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    enrollment = Enrollment.query.filter_by(student_id=student.id, subject_id=subject.id).first()
    if not enrollment:
        flash('El estudiante no está inscrito en esta asignatura.', 'danger')
        return redirect(url_for('teacher_manage_grades', subject_id=subject.id))

    grade_to_change = None
    original_value = None
    if grade_id:
        grade_to_change = Grade.query.get_or_404(grade_id)
        if grade_to_change.subject_id != subject.id or grade_to_change.student_id != student.id:
            flash('Nota no válida para esta asignatura o estudiante.', 'danger')
            return redirect(url_for('teacher_manage_grades', subject_id=subject.id))
        original_value = grade_to_change.value
        form = GradeChangeRequestForm(obj=grade_to_change) # Pre-rellena algunos campos si es edición
        form.request_type.data = 'edit' # Asegura que el tipo de solicitud es edición
        form.grade_id.data = grade_to_change.id # Pasa el ID de la nota a cambiar
        title = 'Solicitar Edición de Nota'
    else:
        # Si no hay grade_id, es una solicitud para AÑADIR una nueva nota (en realidad, se edita a 0 y luego se cambia)
        # O es una solicitud para añadir una nota completamente nueva (no un cambio de una existente).
        # Para simplificar el flujo con GradeChangeRequest, vamos a asumir que para "añadir",
        # el profesor primero debería haber puesto un 0 (o una nota temporal) para luego "editarla" formalmente.
        # Si la nota no existe, el profesor DEBE crearla con un valor temporal (ej. 0) antes de solicitar un cambio.
        # Por ahora, esta ruta es primariamente para CAMBIAR/EDITAR una nota EXISTENTE.
        # Para "añadir nueva", necesitaríamos una lógica diferente o que se añada primero con valor 0.
        # Si el profesor quiere añadir una nota que no existe, no puede usar esta ruta directamente como "editar".
        
        # Para el propósito de esta solicitud, esta ruta es para EDITAR o ELIMINAR una nota existente.
        # La funcionalidad de 'añadir' una nota inicial se puede hacer mediante una ruta separada
        # que permita al profesor registrar una nota (inicialmente con 0 o N/A) y luego la edita.
        
        flash("Para añadir una nota por primera vez, utiliza la opción de 'Añadir Nueva Nota' (se implementará por separado). Esta función es para editar o eliminar notas existentes.", "info")
        return redirect(url_for('teacher_manage_grades', subject_id=subject.id))
        
        # Originalmente (sin solicitud de admin), aquí se añadía la nota directamente:
        # form = GradeForm()
        # title = 'Añadir Nueva Nota'
        # if request.method == 'GET':
        #     form.student.data = student

    # Aquí poblaríamos las opciones dinámicamente si fuese un GradeForm directo.
    # Para GradeChangeRequestForm, el foco es el `grade_id`, `request_type`, `new_value`, `reason`.
    
    # Se debe deshabilitar o pre-seleccionar los campos de estudiante y asignatura
    form.student_id.data = student.id # Esto es un HiddenField, se establece el ID
    form.subject_id.data = subject.id # Esto es un HiddenField, se establece el ID

    if form.validate_on_submit():
        if grade_to_change is None:
            # Esto no debería pasar si la lógica de arriba redirige para "añadir nueva"
            flash('Error: No se encontró la nota a modificar.', 'danger')
            return redirect(url_for('teacher_manage_grades', subject_id=subject.id))

        req_type = form.request_type.data
        new_val = form.new_value.data if req_type == 'edit' else None

        # Validar que si es edición, el nuevo valor no exceda el máximo de la actividad
        if req_type == 'edit':
            activity_config = SubjectActivityConfig.query.filter_by(
                subject_id=grade_to_change.subject_id,
                unit_number=grade_to_change.unit_number,
                activity_name=grade_to_change.activity_name
            ).first()
            
            max_score_for_activity = None
            if activity_config:
                max_score_for_activity = activity_config.max_score
            elif grade_to_change.component_type == 'Parcial':
                max_score_for_activity = 20.0 # Valor fijo para parciales
            
            if max_score_for_activity is not None and new_val > max_score_for_activity:
                flash(f'El nuevo valor ({new_val}) excede el punteo máximo de la actividad ({max_score_for_activity}).', 'danger')
                return render_template('profesores/request_grade_change.html', 
                                       title=title, 
                                       subject=subject, 
                                       student=student, 
                                       grade=grade_to_change, 
                                       original_value=original_value,
                                       form=form, 
                                       current_year=datetime.now().year)
            
            if new_val == original_value:
                flash('El nuevo valor es igual al valor original. No se necesita una solicitud de cambio.', 'info')
                return redirect(url_for('teacher_manage_grades', subject_id=subject.id))


        new_request = GradeChangeRequest(
            grade_id=grade_to_change.id,
            requested_by_user_id=current_user.id,
            reason=form.reason.data,
            request_type=req_type,
            new_value=new_val,
            status='pending' # Siempre inicia como pendiente
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Solicitud de cambio de nota enviada a administración.', 'success')
        return redirect(url_for('teacher_manage_grades', subject_id=subject.id))

    current_year = datetime.now().year
    return render_template('profesores/request_grade_change.html',
                           title=title,
                           subject=subject,
                           student=student,
                           grade=grade_to_change, # Pasa el objeto grade_to_change para acceder a sus datos
                           original_value=original_value,
                           form=form,
                           current_year=current_year)


# --- ELIMINADA: Ruta directa para Añadir/Editar Nota Individual (ahora es solicitud) ---
# Ya no es @app.route('/profesor/asignatura/<int:subject_id>/estudiante/<int:student_id>/nota', methods=['GET', 'POST'])
# Ya no es @app.route('/profesor/asignatura/<int:subject_id>/estudiante/<int:student_id>/nota/<int:grade_id>/editar', methods=['GET', 'POST'])
# La lógica ha sido reemplazada por teacher_request_grade_change

# --- ELIMINADA: Ruta directa para Eliminar Nota (ahora es solicitud) ---
# Ya no es @app.route('/profesor/nota/<int:grade_id>/eliminar', methods=['POST'])
# La lógica ha sido reemplazada por teacher_request_grade_change

# --- Dashboard del Estudiante ---
@app.route('/estudiante/dashboard')
@login_required
@student_required
def student_dashboard():
    estudiante = current_user
    
    enrolled_subjects = [e.subject_obj for e in Enrollment.query.filter_by(student_id=estudiante.id).all()]
    
    all_grades = Grade.query.filter_by(student_id=estudiante.id).all()
    total_grade_sum = sum(g.value for g in all_grades)
    overall_average_grade = (total_grade_sum / len(all_grades)) if all_grades else 0
    
    subjects_with_grades = []
    for subject in enrolled_subjects:
        subjects_with_grades.append(subject)

    # --- Obtener anuncios para el estudiante ---
    student_announcements = Announcement.query.filter(
        (Announcement.target_role == 'Todos') | (Announcement.target_role == 'Estudiante')
    ).order_by(Announcement.date_posted.desc()).all()

    current_year = datetime.now().year
    return render_template('estudiantes/student_dashboard.html', 
                           estudiante=estudiante,
                           subjects_with_grades=subjects_with_grades,
                           overall_average_grade=overall_average_grade, 
                           title=f'Dashboard de {estudiante.first_name}',
                           current_year=current_year)

# --- Ruta para Estudiante: Ver Notas por Asignatura ---
@app.route('/estudiante/asignatura/<int:subject_id>/mis_notas')
@login_required
@student_required
def student_view_grades(subject_id):
    estudiante = current_user
    subject = Subject.query.get_or_404(subject_id)

    enrollment = Enrollment.query.filter_by(student_id=estudiante.id, subject_id=subject.id).first()
    if not enrollment:
        flash('No estás inscrito en esta asignatura.', 'danger')
        return redirect(url_for('student_dashboard'))

    grades = Grade.query.filter_by(student_id=estudiante.id, subject_id=subject.id).order_by(
        Grade.unit_number, Grade.activity_name).all()

    configured_activities = SubjectActivityConfig.query.filter_by(subject_id=subject.id).order_by(
        SubjectActivityConfig.unit_number, SubjectActivityConfig.activity_number).all()
    
    grades_by_unit = {}
    zona_total = 0
    parcial_total = 0
    total_general = 0
    
    PARCIAL_MAX_SCORE = 20.0

    for config in configured_activities:
        if config.unit_number not in grades_by_unit:
            grades_by_unit[config.unit_number] = {'activities': {}, 'zona_subtotal': 0.0, 'zona_max_subtotal': 0.0}
        grades_by_unit[config.unit_number]['activities'][config.activity_name] = {
            'value': 'N/A', 
            'max_score': config.max_score,
            'grade_obj': None
        }

    for grade in grades:
        if grade.component_type == 'Zona':
            if grade.unit_number in grades_by_unit and grade.activity_name in grades_by_unit[grade.unit_number]['activities']:
                grades_by_unit[grade.unit_number]['activities'][grade.activity_name]['value'] = grade.value
                grades_by_unit[grade.unit_number]['activities'][grade.activity_name]['grade_obj'] = grade
                grades_by_unit[grade.unit_number]['zona_subtotal'] += grade.value
                grades_by_unit[grade.unit_number]['zona_max_subtotal'] += grades_by_unit[grade.unit_number]['activities'][grade.activity_name]['max_score']
            zona_total += grade.value 
        elif grade.component_type == 'Parcial':
            if 'parciales' not in grades_by_unit:
                grades_by_unit['parciales'] = {}
            grades_by_unit['parciales'][grade.activity_name] = {
                'value': grade.value,
                'max_score': PARCIAL_MAX_SCORE,
                'grade_obj': grade
            }
            parcial_total += grade.value 
    
    total_general = zona_total + parcial_total 

    current_year = datetime.now().year
    return render_template('estudiantes/view_grades.html',
                           title=f'Mis Notas en {subject.name}',
                           estudiante=estudiante,
                           subject=subject,
                           grades=grades, 
                           grades_by_unit=grades_by_unit, 
                           zona_total=zona_total,
                           parcial_total=parcial_total,
                           total_general=total_general,
                           current_year=current_year)