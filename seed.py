import uuid
import json
import datetime
from database import engine, SessionLocal
from models import Base, Student, TestResult, VideoMetadata, Instructor, TimeSlot, QuizAnswer

def seed_db():
    # 1. Crear las tablas físicas en DuckDB (se crea el archivo local si no existe)
    print("Creando tablas en DuckDB...")
    Base.metadata.create_all(bind=engine)

    # 2. Inyectar datos
    db = SessionLocal()

    # Si ya existe nuestro usuario Sergio, limpiamos o evitamos duplicados
    existing_user = db.query(Student).filter(Student.name == "Sergio").first()
    if existing_user:
        print("La base de datos ya está inicializada.")
        db.close()
        return

    print("Inyectando Mocks en Base de Datos Real...")
    student_id = str(uuid.uuid4())
    
    # Perfil del Alumno
    sergio = Student(
        id=student_id,
        name="Sergio",
        email="sergio@ejemplo.com",
        subscription_plan="Premium",
        theoretical_progress=64.0,
        weaknesses=["Glorietas", "Prioridad de Paso", "Señales de Obligación"]
    )
    db.add(sergio)

    # Resultados de Tests recientes
    test1 = TestResult(
        id=str(uuid.uuid4()),
        student_id=student_id,
        correct_answers=27,
        wrong_answers=3,
        failed_topics=["Glorietas", "Señales"]
    )
    db.add(test1)



    # Metadatos del video con checkpoints interactivos para el quiz overlay
    video_tema_4 = VideoMetadata(
        id="Tema_4_Intersecciones",
        title="Tema 4: Intersecciones",
        ai_metadata={
            "topics": ["Prioridad", "Glorietas", "Ceda el paso", "Stop"],
            "timestamps": {
                "01:20": "Prioridad en glorietas para los que circulan por dentro",
                "03:45": "Obligación de detenerse completamente en un Stop"
            },
            "video_url": "/videos/tema4_intersecciones_final.mp4",
            "checkpoints": [
                {
                    "id": "cp_1",
                    "trigger_time": 8,
                    "start_concept_time": 0,
                    "question": "En una glorieta, ¿quién tiene prioridad?",
                    "options": [
                        {"id": "a", "text": "El que entra en la glorieta"},
                        {"id": "b", "text": "El que circula dentro de la glorieta"},
                        {"id": "c", "text": "El vehículo más grande"},
                        {"id": "d", "text": "El que llega primero"}
                    ],
                    "correct_option": "b",
                    "explanation": "La prioridad SIEMPRE es del vehículo que ya circula dentro de la glorieta. El que quiere incorporarse debe ceder el paso."
                },
                {
                    "id": "cp_2",
                    "trigger_time": 16,
                    "start_concept_time": 10,
                    "question": "Ante una señal de STOP, ¿cuándo debes detenerte?",
                    "options": [
                        {"id": "a", "text": "Solo si hay vehículos cruzando"},
                        {"id": "b", "text": "Solo si hay peatones"},
                        {"id": "c", "text": "Siempre, la detención debe ser total"},
                        {"id": "d", "text": "Puedes pasar lentamente si no hay nadie"}
                    ],
                    "correct_option": "c",
                    "explanation": "En un STOP la detención debe ser TOTAL, aunque no venga ningún vehículo ni peatón. Es obligatorio parar completamente."
                },
                {
                    "id": "cp_3",
                    "trigger_time": 24,
                    "start_concept_time": 18,
                    "question": "¿Qué indica una señal de 'Ceda el paso'?",
                    "options": [
                        {"id": "a", "text": "Detenerse obligatoriamente"},
                        {"id": "b", "text": "Reducir velocidad y ceder si hay tráfico"},
                        {"id": "c", "text": "Acelerar para incorporarse"},
                        {"id": "d", "text": "Cambiar de carril"}
                    ],
                    "correct_option": "b",
                    "explanation": "La señal de 'Ceda el paso' obliga a reducir la velocidad y dejar pasar a los vehículos que tienen preferencia, deteniéndose si es necesario."
                }
            ]
        }
    )
    db.add(video_tema_4)

    # Inyección de Profesores
    prof1 = Instructor(id="juan_123", name="Juan", vehicle_type="Coche Manual")
    prof2 = Instructor(id="laura_456", name="Laura", vehicle_type="Coche Automático")
    db.add(prof1)
    db.add(prof2)

    # Inyección de Slots (Bloques de 45 min) para mañana
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    slots = [
        TimeSlot(id=str(uuid.uuid4()), instructor_id="juan_123", date=tomorrow, time="09:00", is_booked=0),
        TimeSlot(id=str(uuid.uuid4()), instructor_id="juan_123", date=tomorrow, time="09:45", is_booked=0),
        TimeSlot(id=str(uuid.uuid4()), instructor_id="juan_123", date=tomorrow, time="10:30", is_booked=1),
        TimeSlot(id=str(uuid.uuid4()), instructor_id="laura_456", date=tomorrow, time="11:15", is_booked=0),
        TimeSlot(id=str(uuid.uuid4()), instructor_id="laura_456", date=tomorrow, time="12:00", is_booked=0),
    ]
    for s in slots:
        db.add(s)

    db.commit()
    db.close()
    print("¡Base de Datos lista! Archivo local creado: ready2go.duckdb")

if __name__ == "__main__":
    seed_db()

