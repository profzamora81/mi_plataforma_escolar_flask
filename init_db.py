# init_db.py

from app import create_app, db
from models import User, GradeLevel, Subject, Grade, Announcement, Enrollment, SubjectActivityConfig, GradeChangeRequest # ¡Nuevas importaciones!
from werkzeug.security import generate_password_hash
from datetime import datetime

app = create_app() 

with app.app_context():
    # 1. Eliminar la base de datos existente (si la hay)
    db.drop_all()
    print("Base de datos existente eliminada (si existía).")

    # 2. Crear todas las tablas
    db.create_all()
    print("Tablas de la base de datos creadas.")

    # 3. Insertar datos iniciales
    print("Insertando datos iniciales...")

    # Crear Administrador
    admin_user = User(username='admin', email='admin@school.com', role='Administrador', first_name='Super', last_name='Admin')
    admin_user.set_password('Lazaro@2023')
    db.session.add(admin_user)

    # Crear Profesor
    profesor_juan = User(username='profesor_juan', email='juan@school.com', role='Profesor', first_name='Juan', last_name='Pérez')
    profesor_juan.set_password('profepass')
    db.session.add(profesor_juan)

    # Crear Estudiante
    estudiante_maria = User(username='estudiante_maria', email='maria@school.com', role='Estudiante', first_name='Maria', last_name='González')
    estudiante_maria.set_password('estudiantepass')
    db.session.add(estudiante_maria)

    # Crear un nivel educativo
    cuarto_bach = GradeLevel(name='4to. Bachillerato', description='Grado para estudiantes de 4to año de bachillerato')
    db.session.add(cuarto_bach)

    # Guarda los usuarios y el nivel primero para que tengan IDs
    db.session.commit()
    print("Usuarios y Nivel de Grado de prueba añadidos y confirmados.")


    # Recupera las instancias después del commit si necesitas sus IDs
    admin_user = User.query.filter_by(username='admin').first()
    profesor_juan = User.query.filter_by(username='profesor_juan').first()
    estudiante_maria = User.query.filter_by(username='estudiante_maria').first()
    cuarto_bach = GradeLevel.query.filter_by(name='4to. Bachillerato').first()

    # Asignar una asignatura al profesor y al nivel
    matematicas = None # Inicializar para evitar UnboundLocalError
    if profesor_juan and cuarto_bach:
        matematicas = Subject(
            name='Matemáticas',
            code='MAT101',
            description='Curso de matemáticas para 4to. Bachillerato',
            teacher_obj=profesor_juan
        )
        matematicas.grade_levels.append(cuarto_bach)
        db.session.add(matematicas)
        db.session.commit() # Guarda la asignatura para que tenga ID
        print("Asignatura de Matemáticas añadida para Profesor Juan en 4to. Bachillerato.")
    else:
        print("Advertencia: No se pudo añadir la asignatura. Asegúrate de que el profesor y el nivel existan.")

    # --- NUEVO: Añadir Inscripciones de Prueba ---
    if estudiante_maria and matematicas:
        enrollment_maria_math = Enrollment(student_obj=estudiante_maria, subject_obj=matematicas)
        db.session.add(enrollment_maria_math)
        db.session.commit()
        print(f"Estudiante {estudiante_maria.first_name} inscrito en {matematicas.name}.")
    else:
        print("Advertencia: No se pudo inscribir al estudiante. Asegúrate de que el estudiante y la asignatura existan.")

    # --- NUEVO: Configurar Actividades para Matemáticas (Zona: 60 puntos) ---
    if matematicas:
        print("Configurando actividades para Matemáticas...")
        # Unidad I: 3 Actividades + 1 PM
        act1_u1 = SubjectActivityConfig(subject_obj=matematicas, unit_number='Unidad I', activity_number=1, activity_name='Actividad Inicial 1', max_score=10.0)
        act2_u1 = SubjectActivityConfig(subject_obj=matematicas, unit_number='Unidad I', activity_number=2, activity_name='Actividad Inicial 2', max_score=15.0)
        act3_u1 = SubjectActivityConfig(subject_obj=matematicas, unit_number='Unidad I', activity_number=3, activity_name='Actividad Inicial 3', max_score=15.0)
        pm1_u1 = SubjectActivityConfig(subject_obj=matematicas, unit_number='Unidad I', activity_number=4, activity_name='Proceso Mejoramiento 1', max_score=10.0)
        
        # Una actividad más para la Unidad II
        act1_u2 = SubjectActivityConfig(subject_obj=matematicas, unit_number='Unidad II', activity_number=1, activity_name='Actividad Inicial 4', max_score=10.0)

        db.session.add_all([act1_u1, act2_u1, act3_u1, pm1_u1, act1_u2])
        db.session.commit()
        print("Actividades configuradas para Matemáticas (Unidad I y II).")
    else:
        print("Advertencia: No se pudo configurar actividades porque la asignatura no existe.")

    # Añadir una nota de prueba usando la nueva estructura
    nota_maria = None # Inicializar
    if estudiante_maria and matematicas:
        act_ini_1_config = SubjectActivityConfig.query.filter_by(
            subject_id=matematicas.id,
            unit_number='Unidad I',
            activity_name='Actividad Inicial 1'
        ).first()

        if act_ini_1_config:
            nota_maria = Grade(
                student_id=estudiante_maria.id,
                subject_id=matematicas.id,
                value=8.5, 
                activity_name='Actividad Inicial 1',
                unit_number='Unidad I',
                component_type='Zona'
            )
            db.session.add(nota_maria)
            db.session.commit() # ¡Commit aquí para que la nota tenga ID antes de la solicitud!
            print(f"Nota de {nota_maria.value} añadida para {estudiante_maria.first_name} en {matematicas.name} ({nota_maria.activity_name}).")
        else:
            print("Advertencia: No se encontró la configuración de Actividad Inicial 1 para añadir la nota de prueba.")

    # Añadir notas de prueba para los Parciales
    if estudiante_maria and matematicas:
        parcial1_maria = Grade(
            student_id=estudiante_maria.id,
            subject_id=matematicas.id,
            value=18.0, 
            activity_name='Parcial 1',
            unit_number='Unidad I',
            component_type='Parcial'
        )
        parcial2_maria = Grade(
            student_id=estudiante_maria.id,
            subject_id=matematicas.id,
            value=15.0, 
            activity_name='Parcial 2',
            unit_number='Unidad II',
            component_type='Parcial'
        )
        db.session.add_all([parcial1_maria, parcial2_maria])
        db.session.commit()
        print(f"Notas de parciales añadidas para {estudiante_maria.first_name} en {matematicas.name}.")
    else:
        print("Advertencia: No se pudo añadir notas de parciales de prueba.")

    # --- NUEVO: Añadir una solicitud de cambio de nota de prueba ---
    if nota_maria and profesor_juan:
        print("Añadiendo una solicitud de cambio de nota de prueba...")
        change_request = GradeChangeRequest(
            grade_id=nota_maria.id,
            requested_by_user_id=profesor_juan.id,
            reason='La calificación inicial fue un error de digitación, el estudiante obtuvo 9.5.',
            request_type='edit',
            new_value=9.5,
            status='pending'
        )
        db.session.add(change_request)
        db.session.commit()
        print(f"Solicitud de cambio para la nota {nota_maria.id} creada por {profesor_juan.username}.")
    else:
        print("Advertencia: No se pudo añadir una solicitud de cambio de nota de prueba.")


    # Añadir Anuncios de Prueba
    print("Añadiendo anuncios de prueba...")

    announcement_all = Announcement(
        title='¡Bienvenidos al Nuevo Año Escolar!',
        content='Esperamos que tengan un año lleno de aprendizaje y éxitos. ¡Mucho ánimo a todos!',
        user=admin_user,
        target_role='Todos'
    )
    db.session.add(announcement_all)

    announcement_students = Announcement(
        title='Recordatorio: Fecha Límite para Proyectos de Ciencias',
        content='Estimados estudiantes, recuerden que la fecha límite para entregar sus proyectos de ciencias es el 30 de agosto. ¡No lo dejen para el último minuto!',
        user=profesor_juan,
        target_role='Estudiante'
    )
    db.session.add(announcement_students)

    announcement_teachers = Announcement(
        title='Reunión de Profesores - Agenda',
        content='La reunión semanal de profesores se llevará a cabo el viernes a las 10 AM en la sala de conferencias. Por favor, revisen la agenda adjunta.',
        user=admin_user,
        target_role='Profesor'
    )
    db.session.add(announcement_teachers)

    db.session.commit()
    print("Anuncios de prueba añadidos.")

    print("Datos iniciales insertados exitosamente.")
    print("Base de datos lista para usar.")