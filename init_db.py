# init_db.py

from app import create_app, db
from models import User, GradeLevel, Subject, Grade, Announcement
from werkzeug.security import generate_password_hash
from datetime import datetime

# Asegúrate de que 'app' se inicialice correctamente desde create_app
# Esto es importante si tu app.py usa un create_app() function
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
    admin_user.set_password('Lazaro@2023') # O tu contraseña predefinida
    db.session.add(admin_user)

    # Crear Profesor
    profesor_juan = User(username='profesor_juan', email='juan@school.com', role='Profesor', first_name='Juan', last_name='Pérez')
    profesor_juan.set_password('profepass') # O tu contraseña predefinida
    db.session.add(profesor_juan)

    # Crear Estudiante
    estudiante_maria = User(username='estudiante_maria', email='maria@school.com', role='Estudiante', first_name='Maria', last_name='González')
    estudiante_maria.set_password('estudiantepass') # O tu contraseña predefinida
    db.session.add(estudiante_maria)

    # Crear un nivel educativo
    cuarto_bach = GradeLevel(name='4to. Bachillerato', description='Grado para estudiantes de 4to año de bachillerato')
    db.session.add(cuarto_bach)

    # Guarda los usuarios y el nivel primero para que tengan IDs
    db.session.commit()

    # Recupera las instancias después del commit si necesitas sus IDs
    admin_user = User.query.filter_by(username='admin').first()
    profesor_juan = User.query.filter_by(username='profesor_juan').first()
    estudiante_maria = User.query.filter_by(username='estudiante_maria').first()
    cuarto_bach = GradeLevel.query.filter_by(name='4to. Bachillerato').first()

    # Asignar una asignatura al profesor y al nivel
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

        # Opcional: Añadir una nota de prueba
        # Asumimos que María es estudiante de 4to Bach para esta nota de prueba
        if estudiante_maria and matematicas:
            nota_maria = Grade(
                student_id=estudiante_maria.id,
                subject_id=matematicas.id,
                value=85.0,
                bimestre='Bimestre 1',
                date_recorded=datetime.utcnow() # Usa la hora actual para el registro
            )
            db.session.add(nota_maria)
            db.session.commit()
            print(f"Nota de 85.0 añadida para {estudiante_maria.first_name} en {matematicas.name} (Bimestre 1).")
    else:
        print("No se pudo añadir la asignatura/nota. Asegúrate de que el profesor, estudiante y el nivel existan.")

    # --- NUEVOS: Añadir Anuncios de Prueba ---
    print("Añadiendo anuncios de prueba...")

    # Anuncio para todos
    announcement_all = Announcement(
        title='¡Bienvenidos al Nuevo Año Escolar!',
        content='Esperamos que tengan un año lleno de aprendizaje y éxitos. ¡Mucho ánimo a todos!',
        user=admin_user, # Publicado por el admin
        target_role='Todos'
    )
    db.session.add(announcement_all)

    # Anuncio específico para estudiantes
    announcement_students = Announcement(
        title='Recordatorio: Fecha Límite para Proyectos de Ciencias',
        content='Estimados estudiantes, recuerden que la fecha límite para entregar sus proyectos de ciencias es el 30 de agosto. ¡No lo dejen para el último minuto!',
        user=profesor_juan, # Publicado por el profesor Juan
        target_role='Estudiante'
    )
    db.session.add(announcement_students)

    # Anuncio específico para profesores
    announcement_teachers = Announcement(
        title='Reunión de Profesores - Agenda',
        content='La reunión semanal de profesores se llevará a cabo el viernes a las 10 AM en la sala de conferencias. Por favor, revisen la agenda adjunta.',
        user=admin_user, # Publicado por el admin
        target_role='Profesor'
    )
    db.session.add(announcement_teachers)

    db.session.commit()
    print("Anuncios de prueba añadidos.")

    print("Datos iniciales insertados exitosamente.")
    print("Base de datos lista para usar.")