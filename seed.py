import datetime
import uuid

from database import SessionLocal, engine
from models import Base, Instructor, Student, TestResult, TimeSlot, VideoMetadata

DEFAULT_STUDENT_NAME = "Sergio"
DEFAULT_VIDEO_ID = "Tema_4_Intersecciones"

DEFAULT_VIDEO_METADATA = {
    "topics": ["Prioridad", "Glorietas", "Ceda el paso", "Stop"],
    "timestamps": {
        "01:20": "Prioridad en glorietas para los que circulan por dentro",
        "03:45": "Obligacion de detenerse completamente en un Stop",
    },
    "video_url": "/videos/tema4_intersecciones_final.mp4",
    "audio_url": "/audio/tema4_intersecciones_locucion.mp3",
    "checkpoints": [
        {
            "id": "cp_1",
            "trigger_time": 8,
            "start_concept_time": 0,
            "question": "En una glorieta, quien tiene prioridad?",
            "options": [
                {"id": "a", "text": "El que entra en la glorieta"},
                {"id": "b", "text": "El que circula dentro de la glorieta"},
                {"id": "c", "text": "El vehiculo mas grande"},
                {"id": "d", "text": "El que llega primero"},
            ],
            "correct_option": "b",
            "explanation": (
                "La prioridad siempre es del vehiculo que ya circula dentro de la glorieta. "
                "El que quiere incorporarse debe ceder el paso."
            ),
        },
        {
            "id": "cp_2",
            "trigger_time": 16,
            "start_concept_time": 10,
            "question": "Ante una senal de STOP, cuando debes detenerte?",
            "options": [
                {"id": "a", "text": "Solo si hay vehiculos cruzando"},
                {"id": "b", "text": "Solo si hay peatones"},
                {"id": "c", "text": "Siempre, la detencion debe ser total"},
                {"id": "d", "text": "Puedes pasar lentamente si no hay nadie"},
            ],
            "correct_option": "c",
            "explanation": (
                "En un STOP la detencion debe ser total, aunque no venga ningun vehiculo ni peaton. "
                "Es obligatorio parar completamente."
            ),
        },
        {
            "id": "cp_3",
            "trigger_time": 24,
            "start_concept_time": 18,
            "question": "Que indica una senal de ceda el paso?",
            "options": [
                {"id": "a", "text": "Detenerse obligatoriamente"},
                {"id": "b", "text": "Reducir velocidad y ceder si hay trafico"},
                {"id": "c", "text": "Acelerar para incorporarse"},
                {"id": "d", "text": "Cambiar de carril"},
            ],
            "correct_option": "b",
            "explanation": (
                "La senal de ceda el paso obliga a reducir la velocidad y dejar pasar a los vehiculos "
                "que tienen preferencia, deteniendose si es necesario."
            ),
        },
    ],
}

DEFAULT_INSTRUCTORS = [
    {"id": "juan_123", "name": "Juan", "vehicle_type": "Coche Manual"},
    {"id": "laura_456", "name": "Laura", "vehicle_type": "Coche Automatico"},
]

DEFAULT_SLOT_BLUEPRINTS = [
    {"instructor_id": "juan_123", "time": "09:00", "is_booked": 0},
    {"instructor_id": "juan_123", "time": "09:45", "is_booked": 0},
    {"instructor_id": "juan_123", "time": "10:30", "is_booked": 1},
    {"instructor_id": "laura_456", "time": "11:15", "is_booked": 0},
    {"instructor_id": "laura_456", "time": "12:00", "is_booked": 0},
]


def ensure_student(db):
    student = db.query(Student).filter(Student.name == DEFAULT_STUDENT_NAME).first()

    if not student:
        student = Student(
            id=str(uuid.uuid4()),
            name=DEFAULT_STUDENT_NAME,
            email="sergio@ejemplo.com",
            subscription_plan="Premium",
            theoretical_progress=64.0,
            weaknesses=["Glorietas", "Prioridad de Paso", "Senales de Obligacion"],
        )
        db.add(student)
        db.flush()
        return student

    student.email = student.email or "sergio@ejemplo.com"
    student.subscription_plan = student.subscription_plan or "Premium"
    student.theoretical_progress = student.theoretical_progress or 64.0
    student.weaknesses = student.weaknesses or [
        "Glorietas",
        "Prioridad de Paso",
        "Senales de Obligacion",
    ]
    db.flush()
    return student


def ensure_test_result(db, student_id):
    existing_test = (
        db.query(TestResult)
        .filter(TestResult.student_id == student_id)
        .order_by(TestResult.id.desc())
        .first()
    )

    if existing_test:
        return

    db.add(
        TestResult(
            id=str(uuid.uuid4()),
            student_id=student_id,
            correct_answers=27,
            wrong_answers=3,
            failed_topics=["Glorietas", "Senales"],
        )
    )


def ensure_video_metadata(db):
    video = db.query(VideoMetadata).filter(VideoMetadata.id == DEFAULT_VIDEO_ID).first()

    if not video:
        db.add(
            VideoMetadata(
                id=DEFAULT_VIDEO_ID,
                title="Tema 4: Intersecciones",
                ai_metadata=DEFAULT_VIDEO_METADATA,
            )
        )
        return

    video.title = "Tema 4: Intersecciones"
    video.ai_metadata = DEFAULT_VIDEO_METADATA


def ensure_instructors(db):
    for instructor_data in DEFAULT_INSTRUCTORS:
        instructor = db.query(Instructor).filter(Instructor.id == instructor_data["id"]).first()

        if not instructor:
            db.add(Instructor(**instructor_data))
            continue

        instructor.name = instructor_data["name"]
        instructor.vehicle_type = instructor_data["vehicle_type"]


def ensure_time_slots(db):
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    for slot_data in DEFAULT_SLOT_BLUEPRINTS:
        slot = (
            db.query(TimeSlot)
            .filter(TimeSlot.instructor_id == slot_data["instructor_id"])
            .filter(TimeSlot.date == tomorrow)
            .filter(TimeSlot.time == slot_data["time"])
            .first()
        )

        if slot:
            if slot.is_booked is None:
                slot.is_booked = slot_data["is_booked"]
            continue

        db.add(
            TimeSlot(
                id=str(uuid.uuid4()),
                instructor_id=slot_data["instructor_id"],
                date=tomorrow,
                time=slot_data["time"],
                is_booked=slot_data["is_booked"],
            )
        )


def seed_db():
    print("Creando tablas en DuckDB...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        student = ensure_student(db)
        ensure_test_result(db, student.id)
        ensure_video_metadata(db)
        ensure_instructors(db)
        ensure_time_slots(db)
        db.commit()
        print("Base de datos lista y revisada.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
