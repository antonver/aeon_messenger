from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import exc
from typing import List
import logging
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Position, Quality, PositionQuality, Interview
from app.schemas.position import Position as PositionSchema
from app.schemas.interview import InterviewCreate, Interview as InterviewSchema, InterviewUpdate
import random

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hr", tags=["hr"])

@router.get("/positions", response_model=List[PositionSchema])
async def get_active_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить активные позиции для интервью"""
    try:
        positions = db.query(Position).filter(Position.is_active == True).all()
        logger.info(f"Получено {len(positions)} активных позиций")
        return positions
    except Exception as e:
        logger.error(f"Ошибка при получении позиций: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении позиций")

@router.get("/interviews", response_model=List[InterviewSchema])
async def get_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить все интервью пользователя"""
    try:
        interviews = db.query(Interview).filter(Interview.user_id == current_user.id).all()
        logger.info(f"Получено {len(interviews)} интервью для пользователя {current_user.id}")
        return interviews
    except Exception as e:
        logger.error(f"Ошибка при получении интервью: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении интервью")

@router.post("/interviews", response_model=InterviewSchema)
async def create_interview(
    interview: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать новое интервью"""
    try:
        logger.info(f"Создание интервью для позиции {interview.position_id} пользователем {current_user.id}")

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
            max_score=100,
            status="in_progress"
        )

        db.add(db_interview)
        db.commit()
        db.refresh(db_interview)

        logger.info(f"Интервью создано с ID: {db_interview.id}")
        return db_interview

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при создании интервью: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании интервью: {str(e)}")

@router.get("/interviews/current", response_model=InterviewSchema)
async def get_current_interview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить текущее активное интервью пользователя"""
    try:
        interview = db.query(Interview).filter(
            Interview.user_id == current_user.id,
            Interview.status == "in_progress"
        ).first()

        if not interview:
            raise HTTPException(status_code=404, detail="Активное интервью не найдено")

        return interview
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении текущего интервью: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении интервью")

@router.put("/interviews/{interview_id}/answer")
async def submit_answer(
    interview_id: int,
    question_index: int,
    answer: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отправить ответ на вопрос интервью"""
    try:
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

        logger.info(f"Ответ сохранен для интервью {interview_id}, вопрос {question_index}")
        return {"message": "Ответ сохранен"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при сохранении ответа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении ответа")

@router.post("/interviews/{interview_id}/complete")
async def complete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Завершить интервью и получить результат"""
    try:
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

        logger.info(f"Интервью {interview_id} завершено с баллом {score}")
        return {
            "score": score,
            "max_score": interview.max_score,
            "percentage": round((score / interview.max_score) * 100, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при завершении интервью: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при завершении интервью")

def generate_questions_for_position(position: Position, db: Session) -> List[dict]:
    """Генерирует 10 вопросов на основе качеств позиции"""
    try:
        questions = []

        # Получаем качества позиции
        position_qualities = db.query(Quality).join(
            PositionQuality, Quality.id == PositionQuality.quality_id
        ).filter(PositionQuality.position_id == position.id).all()

        # Базовые вопросы для каждой позиции
        base_questions = [
            {
                "id": 1,
                "text": f"Почему вы заинтересованы в позиции {position.title}?",
                "type": "text",
                "category": "motivation"
            },
            {
                "id": 2,
                "text": "Расскажите о своем профессиональном опыте",
                "type": "text",
                "category": "experience"
            },
            {
                "id": 3,
                "text": "Какие ваши сильные стороны?",
                "type": "text",
                "category": "strengths"
            },
            {
                "id": 4,
                "text": "Как вы работаете в команде?",
                "type": "text",
                "category": "teamwork"
            },
            {
                "id": 5,
                "text": "Опишите сложную рабочую ситуацию и как вы ее решили",
                "type": "text",
                "category": "problem_solving"
            }
        ]

        questions.extend(base_questions)

        # Добавляем вопросы на основе качеств позиции
        quality_questions = []
        for quality in position_qualities:
            quality_questions.append({
                "id": len(questions) + 1,
                "text": f"Как вы оцениваете свои навыки в области: {quality.name}?",
                "type": "scale",
                "category": quality.name.lower(),
                "scale": {"min": 1, "max": 10}
            })

        # Добавляем вопросы по качествам (максимум 5)
        if quality_questions:
            questions.extend(quality_questions[:5])

        # Дополняем до 10 вопросов если нужно
        additional_questions = [
            {
                "id": len(questions) + 1,
                "text": "Какие у вас планы профессионального развития?",
                "type": "text",
                "category": "career_goals"
            },
            {
                "id": len(questions) + 1,
                "text": "Что вы знаете о нашей компании?",
                "type": "text",
                "category": "company_knowledge"
            }
        ]

        while len(questions) < 10 and additional_questions:
            questions.append(additional_questions.pop(0))

        return questions[:10]  # Ограничиваем 10 вопросами

    except Exception as e:
        logger.error(f"Ошибка при генерации вопросов: {e}")
        # Возвращаем базовые вопросы в случае ошибки
        return [
            {
                "id": 1,
                "text": f"Почему вы заинтересованы в позиции {position.title}?",
                "type": "text",
                "category": "motivation"
            },
            {
                "id": 2,
                "text": "Расскажите о своем опыте работы",
                "type": "text",
                "category": "experience"
            }
        ]

def calculate_interview_score(interview: Interview) -> int:
    """Рассчитывает балл за интервью"""
    try:
        if not interview.answers:
            return 0

        total_questions = len(interview.questions)
        answered_questions = len(interview.answers)

        # Базовый балл за количество отвеченных вопросов
        completion_score = (answered_questions / total_questions) * 50

        # Дополнительные баллы за качество ответов (упрощенная логика)
        quality_score = 0
        for answer in interview.answers.values():
            if isinstance(answer, str) and len(answer.strip()) > 10:
                quality_score += 5
            elif isinstance(answer, (int, float)):
                quality_score += answer

        total_score = min(int(completion_score + quality_score), interview.max_score)
        return total_score

    except Exception as e:
        logger.error(f"Ошибка при расчете балла интервью: {e}")
        return 0
