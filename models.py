from sqlalchemy import Column, String, Float, Integer, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    subscription_plan = Column(String)
    theoretical_progress = Column(Float, default=0.0)
    weaknesses = Column(JSON)  # DuckDB maneja JSON correctamente

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(String, primary_key=True)
    student_id = Column(String)
    correct_answers = Column(Integer)
    wrong_answers = Column(Integer)
    failed_topics = Column(JSON)

class VideoMetadata(Base):
    __tablename__ = "videos_metadata"

    id = Column(String, primary_key=True)
    title = Column(String)
    ai_metadata = Column(JSON) # {"topics": ["x"], "timestamps": {"01:00":"y"}}

class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(String, primary_key=True)
    name = Column(String)
    vehicle_type = Column(String)

class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(String, primary_key=True)
    instructor_id = Column(String) # FK a instructor
    date = Column(String) # YYYY-MM-DD
    time = Column(String) # "10:00"
    is_booked = Column(Integer, default=0) # 0 libre, 1 reservada

class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id = Column(String, primary_key=True)
    student_id = Column(String)       # FK a students
    video_id = Column(String)         # FK a videos_metadata
    checkpoint_id = Column(String)    # ej: "cp_1"
    selected_option = Column(String)  # ej: "b"
    is_correct = Column(Integer)      # 0 o 1
    attempt_number = Column(Integer)  # Intento nº
    answered_at = Column(String)      # ISO timestamp