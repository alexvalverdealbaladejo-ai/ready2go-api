import os
import uuid
import re
from contextlib import asynccontextmanager
from datetime import datetime as dt
from typing import Any
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from database import get_db
from models import Student, TestResult, VideoMetadata, Instructor, TimeSlot, QuizAnswer
from seed import seed_db

from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

def get_allowed_origins():
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_db()
    yield

app = FastAPI(title="Ready2GO MVP API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    student_name: str
    video_id: str
    question: str
    history: list = Field(default_factory=list)
    lesson_context: dict[str, Any] = Field(default_factory=dict)
    session_metrics: dict[str, Any] = Field(default_factory=dict)

class FakeLangchainModel:
    """Mock de LangChain para cumplir el MVP cuando el usuario no provee API Key"""

    def invoke(self, prompt: str):
        prompt_lower = str(prompt).lower()
        active_concept_match = re.search(r"concepto activo[:\s]+([^\n]+)", str(prompt), re.IGNORECASE)
        active_concept = active_concept_match.group(1).strip() if active_concept_match else ""
        if "gracias" in prompt_lower:
            return "🤖 (Simulacion): ¡De nada! Si te surge otra duda sobre el video o los test, dimelo. ¡Tu puedes!"
        if "glorieta" in prompt_lower or "prioridad" in prompt_lower:
            return "🤖 **Tutor Antigravity**:\n\n¡Buena pregunta! En las **glorietas**, la regla de oro es que la prioridad es **SIEMPRE** de los vehiculos que ya estan circulando dentro de la calzada anular.\n\nCuando tu quieras entrar, debes ceder el paso a todos los que ya esten dentro. Ademas, recuerda salir siempre desde el carril exterior. ¿Te gustaria que repasemos como usar los intermitentes en este caso?"
        if "stop" in prompt_lower or "detenerse" in prompt_lower:
            return "🤖 **Tutor Antigravity**:\n\n¡Exacto! El **STOP** es una de las señales mas importantes. La detencion debe ser **total y absoluta** (ruedas paradas), incluso si tienes visibilidad total y no viene nadie. Si no te detienes del todo, se considera una falta grave en el examen practico. ¿Deseas saber donde exactamente debes detener el coche si no hay linea de detencion?"
        if "ceda" in prompt_lower:
            return "🤖 **Tutor Antigravity**:\n\nEl **Ceda el paso** es diferente al STOP. Solo tienes que detenerte si vienen vehiculos a los que puedas obstaculizar. Si tienes visibilidad y la via esta libre, puedes continuar sin parar del todo. ¡Pero mucho ojo con la velocidad al aproximarte!"
        if active_concept:
            return (
                "🤖 **Tutor Antigravity**:\n\n"
                f"Ahora mismo estas en el concepto **{active_concept}**. "
                "Quedate con esta idea:\n\n"
                "1. Identifica quien tiene la prioridad.\n"
                "2. Reduce y observa antes de decidir.\n"
                "3. Si obligas a otro vehiculo a frenar, todavia no era tu turno.\n\n"
                "Si quieres, te pongo ahora un ejemplo corto de examen sobre este punto."
            )

        return "🤖 **Tutor Antigravity**: Hola, estoy analizando tu duda sobre la leccion. Te sugiero prestar atencion a la explicacion que estamos viendo ahora en el video. ¿Hay algun concepto especifico de Intersecciones que no te haya quedado claro?"

def get_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
    return FakeLangchainModel()

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ready2go-api"}

@app.get("/api/student/{name}")
def get_student_dashboard(name: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.name == name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en la DB")

    test = db.query(TestResult).filter(TestResult.student_id == student.id).order_by(TestResult.id.desc()).first()

    return {
        "id": student.id,
        "name": student.name,
        "progress": student.theoretical_progress,
        "weaknesses": student.weaknesses,
        "latest_test": {
            "wrong_answers": test.wrong_answers if test else 0,
            "failed_topics": test.failed_topics if test else [],
        },
    }

@app.post("/api/tutor/ask")
def ask_tutor(query: QueryRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.name == query.student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    video = db.query(VideoMetadata).filter(VideoMetadata.id == query.video_id).first()
    video_context = video.ai_metadata if video else "Contexto general"

    msgs = [
        ("system", "Eres Tutor Antigravity de Ready2GO. El alumno es {student_name} y tiene dudas."),
        ("system", "IMPORTANTE: Sus debilidades actuales registradas en DB son: {weaknesses}."),
        ("system", "Contexto del video actual: {video_context}"),
    ]
    if query.lesson_context:
        lesson_lines = []
        if query.lesson_context.get("beat_title"):
            lesson_lines.append(f"Bloque actual: {query.lesson_context.get('beat_title')}")
        if query.lesson_context.get("active_concept"):
            lesson_lines.append(f"Concepto activo: {query.lesson_context.get('active_concept')}")
        if query.lesson_context.get("subtitle"):
            lesson_lines.append(f"Resumen del bloque: {query.lesson_context.get('subtitle')}")
        if query.lesson_context.get("caption"):
            lesson_lines.append(f"Frase que se esta impartiendo: {query.lesson_context.get('caption')}")
        if query.lesson_context.get("current_time_label"):
            lesson_lines.append(f"Segundo actual: {query.lesson_context.get('current_time_label')}")
        if lesson_lines:
            msgs.append(("system", "Contexto de la clase actual:\n" + "\n".join(lesson_lines)))

    if query.session_metrics:
        metrics_lines = []
        if query.session_metrics.get("watch_seconds") is not None:
            metrics_lines.append(
                f"Tiempo visto en esta sesion: {query.session_metrics.get('watch_seconds')} segundos"
            )
        if query.session_metrics.get("questions_asked") is not None:
            metrics_lines.append(
                f"Preguntas realizadas en esta sesion: {query.session_metrics.get('questions_asked')}"
            )
        if query.session_metrics.get("quiz_correct") is not None and query.session_metrics.get("quiz_incorrect") is not None:
            metrics_lines.append(
                "Resultado de checkpoints en esta sesion: "
                f"{query.session_metrics.get('quiz_correct')} correctos y "
                f"{query.session_metrics.get('quiz_incorrect')} incorrectos"
            )
        if metrics_lines:
            msgs.append(("system", "Señales de progreso de sesion:\n" + "\n".join(metrics_lines)))

    if query.history:
        history_text = "\n".join(
            [f"- {m.get('role', '')}: {m.get('content', '')}" for m in query.history if isinstance(m, dict)]
        )
        msgs.append(("system", "Historial previo:\n" + history_text))
    msgs.append(("user", "{question}"))

    prompt_template = ChatPromptTemplate.from_messages(msgs)

    messages = prompt_template.format_messages(
        student_name=student.name,
        weaknesses=student.weaknesses,
        video_context=video_context,
        question=query.question,
    )

    llm = get_llm()
    try:
        if isinstance(llm, FakeLangchainModel):
            response_content = llm.invoke(str(messages))
        else:
            ai_msg = llm.invoke(messages)
            response_content = ai_msg.content
    except Exception as error:
        response_content = f"⚠️ Error en modelo: Falta API Key valida o conexion ({str(error)})."

    return {
        "success": True,
        "tutor_response": response_content,
    }

@app.get("/api/instructors")
def get_instructors(db: Session = Depends(get_db)):
    instructors = db.query(Instructor).all()
    result = []
    for inst in instructors:
        slots = db.query(TimeSlot).filter(TimeSlot.instructor_id == inst.id).all()
        result.append(
            {
                "id": inst.id,
                "name": inst.name,
                "vehicle_type": inst.vehicle_type,
                "slots": [{"id": s.id, "date": s.date, "time": s.time, "is_booked": s.is_booked} for s in slots],
            }
        )
    return result

class BookRequest(BaseModel):
    slot_id: str
    student_id: str

class TestResultRequest(BaseModel):
    student_name: str
    correct_answers: int
    wrong_answers: int
    failed_topics: list[str] = Field(default_factory=list)

@app.post("/api/book")
def book_class(req: BookRequest, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).filter(TimeSlot.id == req.slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.is_booked == 1:
        raise HTTPException(status_code=400, detail="Slot already booked")

    slot.is_booked = 1
    db.commit()
    return {"success": True, "message": "Clase reservada correctamente"}

@app.post("/api/test-results")
def save_test_result(req: TestResultRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.name == req.student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    test_result = TestResult(
        id=str(uuid.uuid4()),
        student_id=student.id,
        correct_answers=req.correct_answers,
        wrong_answers=req.wrong_answers,
        failed_topics=req.failed_topics,
    )
    db.add(test_result)
    db.commit()

    return {
        "success": True,
        "message": "Resultado de test guardado correctamente",
        "result_id": test_result.id,
    }

@app.get("/api/video/{video_id}/checkpoints")
def get_video_checkpoints(video_id: str, db: Session = Depends(get_db)):
    """Devuelve la metadata del video + array de checkpoints con preguntas."""
    video = db.query(VideoMetadata).filter(VideoMetadata.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    metadata = video.ai_metadata or {}
    return {
        "video_id": video.id,
        "title": video.title,
        "video_url": metadata.get("video_url", ""),
        "checkpoints": metadata.get("checkpoints", []),
    }

class QuizAnswerRequest(BaseModel):
    student_name: str
    video_id: str
    checkpoint_id: str
    selected_option: str
    is_correct: bool

@app.post("/api/quiz/answer")
def submit_quiz_answer(req: QuizAnswerRequest, db: Session = Depends(get_db)):
    """Registra un intento (correcto/incorrecto) del alumno en un checkpoint."""
    student = db.query(Student).filter(Student.name == req.student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    previous_attempts = db.query(QuizAnswer).filter(
        QuizAnswer.student_id == student.id,
        QuizAnswer.video_id == req.video_id,
        QuizAnswer.checkpoint_id == req.checkpoint_id,
    ).count()

    answer = QuizAnswer(
        id=str(uuid.uuid4()),
        student_id=student.id,
        video_id=req.video_id,
        checkpoint_id=req.checkpoint_id,
        selected_option=req.selected_option,
        is_correct=1 if req.is_correct else 0,
        attempt_number=previous_attempts + 1,
        answered_at=dt.utcnow().isoformat(),
    )
    db.add(answer)
    db.commit()

    return {
        "success": True,
        "attempt_number": answer.attempt_number,
        "message": "¡Correcto!" if req.is_correct else "Incorrecto. Repasa la explicacion.",
    }

@app.get("/api/quiz/progress/{student_name}/{video_id}")
def get_quiz_progress(student_name: str, video_id: str, db: Session = Depends(get_db)):
    """Devuelve los checkpoints ya superados por el alumno para un video."""
    student = db.query(Student).filter(Student.name == student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    correct_answers = db.query(QuizAnswer).filter(
        QuizAnswer.student_id == student.id,
        QuizAnswer.video_id == video_id,
        QuizAnswer.is_correct == 1,
    ).all()

    completed_checkpoints = list(set([answer.checkpoint_id for answer in correct_answers]))

    all_answers = db.query(QuizAnswer).filter(
        QuizAnswer.student_id == student.id,
        QuizAnswer.video_id == video_id,
    ).all()

    return {
        "student_name": student_name,
        "video_id": video_id,
        "completed_checkpoints": completed_checkpoints,
        "total_attempts": len(all_answers),
        "total_correct": len(correct_answers),
    }
