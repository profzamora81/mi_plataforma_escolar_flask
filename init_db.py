# init_db.py

from app import app, db
from models import User, GradeLevel, Subject, Grade, Announcement, Enrollment, SubjectActivityConfig, GradeChangeRequest # ¡Nuevas importaciones!
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    print("Tablas de la base de datos creadas.")
    
    # Asegurarse de que las tablas existan (esto ya lo hiciste con db.create_all() desde la consola)
    # db.create_all() # No es necesario si ya lo ejecutaste desde la consola justo antes de este script

    print("Insertando datos iniciales...")

    # Crear niveles de grado
    grade_level_1 = GradeLevel(name='Primero Básico')
    grade_level_2 = GradeLevel(name='Segundo Básico')
    grade_level_3 = GradeLevel(name='Tercero Básico')
    grade_level_4 = GradeLevel(name='Cuarto Bachillerato')
    grade_level_5 = GradeLevel(name='Quinto Bachillerato')

    db.session.add_all([grade_level_1, grade_level_2, grade_level_3, grade_level_4, grade_level_5])
    db.session.commit()

    # Crear usuarios
    hashed_password_admin = generate_password_hash('adminpass')
    hashed_password_teacher = generate_password_hash('teacherpass')
    hashed_password_student1 = generate_password_hash('student1pass')
    hashed_password_student2 = generate_password_hash('student2pass')

    admin_user = User(username='admin', email='admin@school.com', role='Administrador', first_name='Super', last_name='Admin', password=hashed_password_admin)
    teacher_user = User(username='profesor', email='profesor@school.com', role='Profesor', first_name='Carlos', last_name='Gomez', password=hashed_password_teacher)
    student_user1 = User(username='maria.g', email='maria@school.com', role='Estudiante', first_name='Maria', last_name='Gonzalez', password=hashed_password_student1)
    student_user2 = User(username='juan.p', email='juan@school.com', role='Estudiante', first_name='Juan', last_name='Perez', password=hashed_password_student2)

    db.session.add_all([admin_user, teacher_user, student_user1, student_user2])
    db.session.commit()

    # Crear asignaturas
    subject1 = Subject(name='Matemáticas', code='MAT101', description='Matemáticas básicas', teacher_id=teacher_user.id)
    subject2 = Subject(name='Ciencias', code='CIE101', description='Ciencias naturales', teacher_id=teacher_user.id)
    subject3 = Subject(name='Literatura', code='LIT101', description='Literatura universal', teacher_id=teacher_user.id)

    db.session.add_all([subject1, subject2, subject3])
    db.session.commit()

    # Asociar asignaturas con niveles de grado
    subject1.grade_levels.append(grade_level_1)
    subject1.grade_levels.append(grade_level_2)
    subject2.grade_levels.append(grade_level_1)
    subject3.grade_levels.append(grade_level_3)
    db.session.commit()

    # Añadir inscripciones de estudiantes
    enrollment1 = Enrollment(student_id=student_user1.id, subject_id=subject1.id)
    enrollment2 = Enrollment(student_id=student_user1.id, subject_id=subject2.id)
    enrollment3 = Enrollment(student_id=student_user2.id, subject_id=subject1.id)

    db.session.add_all([enrollment1, enrollment2, enrollment3])
    db.session.commit()

    # Añadir algunas notas para María en Matemáticas
    grade1 = Grade(student_id=student_user1.id, subject_id=subject1.id, value=8.5, description='Examen Parcial Unidad I', activity_name='Examen Parcial', unit_number='Unidad I', component_type='Parcial')
    grade2 = Grade(student_id=student_user1.id, subject_id=subject1.id, value=7.0, description='Tarea 1', activity_name='Tarea 1', unit_number='Unidad I', component_type='Zona')
    grade3 = Grade(student_id=student_user2.id, subject_id=subject1.id, value=9.0, description='Examen Final Unidad I', activity_name='Examen Final', unit_number='Unidad I', component_type='Parcial')

    db.session.add_all([grade1, grade2, grade3])
    db.session.commit()

    # Añadir una solicitud de cambio de nota (ejemplo para la imagen proporcionada)
    # Suponiendo que el profesor Juan Pérez es teacher_user
    change_request1 = GradeChangeRequest(
        grade_id=grade1.id, # Referencia a la nota de María en Matemáticas
        requested_by_user_id=teacher_user.id, # Solicitado por el profesor
        reason='La calificación inicial fue un error de digitación, el estudiante obtuvo 9.5.',
        request_type='edit',
        new_value=9.5,
        status='pending',
        request_date=datetime(2025, 7, 24, 15, 54, 0) # Fecha del ejemplo de la imagen
    )
    db.session.add(change_request1)
    db.session.commit()


    print("Datos iniciales insertados exitosamente.")