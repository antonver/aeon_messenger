from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Position, Quality, Interview
from app.schemas.position import Position as PositionSchema
from app.schemas.interview import InterviewCreate, Interview as InterviewSchema, InterviewUpdate
import random

router = APIRouter(prefix="/hr", tags=["hr"])

@router.get("/positions", response_model=List[PositionSchema])
async def get_active_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить активные позиции для интервью"""
    positions = db.query(Position).filter(Position.is_active == True).all()
    return positions

@router.post("/interviews", response_model=InterviewSchema)
async def create_interview(
    interview: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать новое интервью"""
    # Проверяем, что позиция существует и активна
    position = db.query(Position).filter(
        Position.id == interview.position_id,
        Position.is_active == True
    ).first()
    
    if not position:
        raise HTTPException(status_code=404, detail="Позиция не найдена или неактивна")
    
    # Проверяем, нет ли уже активного интервью у пользователя
    existing_interview = db.query(Interview).filter(
        Interview.user_id == current_user.id,
        Interview.status == "in_progress"
    ).first()
    
    if existing_interview:
        raise HTTPException(status_code=400, detail="У вас уже есть активное интервью")
    
    # Генерируем вопросы на основе качеств позиции
    questions = generate_questions_for_position(position, db)
    
    # Создаем интервью
    db_interview = Interview(
        user_id=current_user.id,
        position_id=interview.position_id,
        questions=questions,
        answers={},
        max_score=100
    )
    
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    
    return db_interview

@router.get("/interviews/current", response_model=InterviewSchema)
async def get_current_interview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить текущее активное интервью пользователя"""
    interview = db.query(Interview).filter(
        Interview.user_id == current_user.id,
        Interview.status == "in_progress"
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Активное интервью не найдено")
    
    return interview

@router.put("/interviews/{interview_id}/answer")
async def submit_answer(
    interview_id: int,
    question_index: int,
    answer: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отправить ответ на вопрос интервью"""
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Интервью не найдено")
    
    if interview.status != "in_progress":
        raise HTTPException(status_code=400, detail="Интервью уже завершено")
    
    # Обновляем ответы
    if not interview.answers:
        interview.answers = {}
    
    interview.answers[str(question_index)] = answer
    db.commit()
    
    return {"message": "Ответ сохранен"}

@router.post("/interviews/{interview_id}/complete")
async def complete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Завершить интервью и получить результат"""
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Интервью не найдено")
    
    if interview.status != "in_progress":
        raise HTTPException(status_code=400, detail="Интервью уже завершено")
    
    # Рассчитываем балл
    score = calculate_interview_score(interview)
    interview.score = score
    interview.status = "completed"
    
    db.commit()
    
    return {
        "score": score,
        "max_score": interview.max_score,
        "percentage": round((score / interview.max_score) * 100, 2)
    }

def generate_questions_for_position(position: Position, db: Session) -> List[dict]:
    """Генерирует 10 вопросов на основе качеств позиции"""
    questions = []
    
    # Получаем качества позиции
    position_qualities = db.query(Quality).join(
        PositionQuality, Quality.id == PositionQuality.quality_id
    ).filter(PositionQuality.position_id == position.id).all()
    
    # Базовые вопросы для каждой позиции
    base_questions = [
        "Расскажите о своем опыте работы в данной области",
        "Какие у вас есть сильные стороны?",
        "Как вы справляетесь со стрессовыми ситуациями?",
        "Расскажите о проекте, которым вы гордитесь",
        "Как вы планируете свое время?",
        "Какие у вас есть цели на ближайший год?",
        "Как вы относитесь к командной работе?",
        "Расскажите о ситуации, когда вам пришлось решать сложную задачу",
        "Как вы изучаете новые технологии?",
        "Что для вас важно в работе?"
    ]
    
    # Добавляем специфичные вопросы для качеств
    quality_questions = {
        "Коммуникабельность": [
            "Как вы выстраиваете отношения с коллегами?",
            "Расскажите о конфликтной ситуации, которую вы решили"
        ],
        "Лидерство": [
            "Как вы мотивируете команду?",
            "Расскажите о проекте, где вы были лидером"
        ],
        "Аналитическое мышление": [
            "Как вы подходите к решению сложных задач?",
            "Расскажите о ситуации, где требовался анализ данных"
        ],
        "Креативность": [
            "Как вы генерируете новые идеи?",
            "Расскажите о нестандартном решении проблемы"
        ],
        "Ответственность": [
            "Как вы относитесь к дедлайнам?",
            "Расскажите о ситуации, где вы взяли на себя ответственность"
        ]
    }
    
    # Собираем все вопросы
    all_questions = base_questions.copy()
    
    for quality in position_qualities:
        if quality.name in quality_questions:
            all_questions.extend(quality_questions[quality.name])
    
    # Выбираем 10 случайных вопросов
    selected_questions = random.sample(all_questions, min(10, len(all_questions)))
    
    # Формируем структуру вопросов
    for i, question in enumerate(selected_questions):
        questions.append({
            "id": i,
            "text": question,
            "type": "text",
            "max_length": 500
        })
    
    return questions

def calculate_interview_score(interview: Interview) -> int:
    """Рассчитывает балл за интервью"""
    if not interview.answers:
        return 0
    
    # Простая система оценки на основе количества ответов
    # В реальной системе здесь может быть более сложная логика
    total_questions = len(interview.questions) if interview.questions else 0
    answered_questions = len(interview.answers)
    
    if total_questions == 0:
        return 0
    
    # Базовый балл за каждый ответ
    base_score = (answered_questions / total_questions) * 70
    
    # Дополнительные баллы за качество ответов (упрощенная логика)
    quality_bonus = 0
    for answer in interview.answers.values():
        if isinstance(answer, str) and len(answer.strip()) > 50:
            quality_bonus += 3
    
    total_score = min(100, base_score + quality_bonus)
    return int(total_score) 