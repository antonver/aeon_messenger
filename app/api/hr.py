from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import exc
from typing import List
import logging
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.position import Position
from app.models.quality import Quality
from app.models.position_quality import PositionQuality
from app.models.interview import Interview
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

@router.get("/positions/public", response_model=List[PositionSchema])
async def get_active_positions_public(
    db: Session = Depends(get_db)
):
    """Получить активные позиции для интервью (публичный доступ)"""
    try:
        positions = db.query(Position).filter(Position.is_active == True).all()
        logger.info(f"Получено {len(positions)} активных позиций (публичный доступ)")
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
        score = calculate_interview_score(interview, db)
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
    """Генерирует 10 вопросов на основе качеств позиции с помощью OpenAI"""
    try:
        import os
        import openai
        from typing import List

        # Получаем качества позиции
        position_qualities = db.query(Quality).join(
            PositionQuality, Quality.id == PositionQuality.quality_id
        ).filter(PositionQuality.position_id == position.id).all()

        # Проверяем наличие OpenAI API ключа
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY не найден, используем базовые вопросы")
            return generate_basic_questions(position)

        # Настраиваем OpenAI клиент
        openai.api_key = openai_api_key

        # Формируем промпт для генерации вопросов
        qualities_text = ", ".join([q.name for q in position_qualities]) if position_qualities else "общие профессиональные навыки"
        
        prompt = f"""
        Создай ровно 10 профессиональных вопросов для интервью на позицию "{position.title}".
        
        Ключевые качества для оценки: {qualities_text}
        
        Требования к вопросам:
        1. Вопросы должны быть направлены на оценку указанных качеств
        2. Вопросы должны быть открытыми и требовать развернутых ответов
        3. Вопросы должны быть профессиональными и уместными для данной позиции
        4. Вопросы должны быть разнообразными по типам (поведенческие, ситуационные, технические)
        5. Вопросы должны быть на русском языке
        6. Вопросы должны быть конкретными и практическими
        7. Избегай общих вопросов типа "Расскажите о себе"
        
        Примеры хороших вопросов:
        - "Опишите проект, где вы использовали [конкретная технология/навык]"
        - "Как бы вы решали конфликт в команде при работе над срочным проектом?"
        - "Расскажите о случае, когда вам пришлось быстро адаптироваться к изменениям"
        
        Формат ответа - только список из ровно 10 вопросов, каждый с новой строки, без нумерации.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты HR-специалист, который создает профессиональные вопросы для интервью."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            # Получаем сгенерированные вопросы
            generated_questions_text = response.choices[0].message.content.strip()
            questions_list = [q.strip() for q in generated_questions_text.split('\n') if q.strip()]

            # Формируем структурированные вопросы
            questions = []
            for i, question_text in enumerate(questions_list[:10], 1):
                questions.append({
                    "id": i,
                    "text": question_text,
                    "type": "text",
                    "category": "ai_generated"
                })

            # Если получили меньше 10 вопросов, дополняем базовыми
            if len(questions) < 10:
                basic_questions = generate_basic_questions(position)
                for basic_q in basic_questions:
                    if len(questions) >= 10:
                        break
                    questions.append({
                        "id": len(questions) + 1,
                        "text": basic_q["text"],
                        "type": basic_q["type"],
                        "category": basic_q["category"]
                    })

            logger.info(f"Сгенерировано {len(questions)} вопросов для позиции {position.title}")
            return questions

        except Exception as openai_error:
            logger.error(f"Ошибка при обращении к OpenAI: {openai_error}")
            return generate_basic_questions(position)

    except Exception as e:
        logger.error(f"Ошибка при генерации вопросов: {e}")
        return generate_basic_questions(position)

def generate_basic_questions(position: Position) -> List[dict]:
    """Генерирует базовые вопросы для позиции"""
    return [
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
        },
        {
            "id": 6,
            "text": "Какие у вас планы профессионального развития?",
            "type": "text",
            "category": "career_goals"
        },
        {
            "id": 7,
            "text": "Что вы знаете о нашей компании?",
            "type": "text",
            "category": "company_knowledge"
        },
        {
            "id": 8,
            "text": "Как вы справляетесь со стрессовыми ситуациями?",
            "type": "text",
            "category": "stress_management"
        },
        {
            "id": 9,
            "text": "Расскажите о проекте, которым вы гордитесь",
            "type": "text",
            "category": "achievements"
        },
        {
            "id": 10,
            "text": "Как вы планируете свое время и приоритеты?",
            "type": "text",
            "category": "time_management"
        }
    ]

def calculate_interview_score(interview: Interview, db: Session) -> int:
    """Рассчитывает балл за интервью с помощью OpenAI анализа"""
    try:
        if not interview.answers:
            return 0

        import os
        import openai

        # Проверяем наличие OpenAI API ключа
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY не найден, используем базовый расчет")
            return calculate_basic_score(interview)

        # Настраиваем OpenAI клиент
        openai.api_key = openai_api_key

        # Получаем позицию для контекста
        position = db.query(Position).filter(Position.id == interview.position_id).first()
        position_title = position.title if position else "неизвестная позиция"

        # Формируем промпт для анализа
        answers_text = "\n".join([f"Вопрос {i+1}: {interview.questions[i]['text']}\nОтвет: {answer}" 
                                 for i, answer in enumerate(interview.answers.values())])

        prompt = f"""
        Проанализируй ответы кандидата на интервью для позиции "{position_title}".
        
        Ответы кандидата:
        {answers_text}
        
        Оцени ответы по следующим критериям:
        1. Глубина и детализация ответов (0-10 баллов)
        2. Соответствие требованиям позиции (0-10 баллов)
        3. Практический опыт и примеры (0-10 баллов)
        4. Профессиональные знания (0-10 баллов)
        5. Коммуникативные навыки (0-10 баллов)
        
        Общий балл должен быть от 0 до 100.
        
        Верни только число - общий балл от 0 до 100.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты HR-специалист, который оценивает кандидатов на основе их ответов на интервью."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )

            # Получаем оценку
            score_text = response.choices[0].message.content.strip()
            try:
                score = int(score_text)
                # Ограничиваем балл от 0 до 100
                score = max(0, min(100, score))
                logger.info(f"AI оценка для интервью {interview.id}: {score}")
                return score
            except ValueError:
                logger.warning(f"Не удалось распарсить AI оценку: {score_text}, используем базовый расчет")
                return calculate_basic_score(interview)

        except Exception as openai_error:
            logger.error(f"Ошибка при обращении к OpenAI: {openai_error}")
            return calculate_basic_score(interview)

    except Exception as e:
        logger.error(f"Ошибка при расчете балла интервью: {e}")
        return calculate_basic_score(interview)

def calculate_basic_score(interview: Interview) -> int:
    """Базовый расчет балла за интервью"""
    try:
        if not interview.answers:
            return 0

        total_questions = len(interview.questions)
        answered_questions = len(interview.answers)

        # Базовый балл за количество отвеченных вопросов
        completion_score = (answered_questions / total_questions) * 50

        # Дополнительные баллы за качество ответов
        quality_score = 0
        for answer in interview.answers.values():
            if isinstance(answer, str) and len(answer.strip()) > 10:
                quality_score += 5
            elif isinstance(answer, (int, float)):
                quality_score += answer

        total_score = min(int(completion_score + quality_score), interview.max_score)
        return total_score

    except Exception as e:
        logger.error(f"Ошибка при базовом расчете балла: {e}")
        return 0
