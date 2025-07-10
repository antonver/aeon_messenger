from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Position, Quality, PositionQuality, Interview
from app.schemas.position import PositionCreate, PositionUpdate, Position as PositionSchema, PositionWithQualities
from app.schemas.quality import QualityCreate, Quality as QualitySchema
from app.schemas.interview import Interview as InterviewSchema, InterviewWithUser
from app.schemas.user import User as UserSchema

router = APIRouter(prefix="/admin", tags=["admin"])

def check_admin_permissions(current_user: User = Depends(get_current_user)):
    """Проверяет права администратора"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )
    return current_user

@router.get("/users", response_model=List[UserSchema])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить всех пользователей (только для админов)"""
    users = db.query(User).all()
    return users

@router.post("/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Назначить пользователя администратором"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.is_admin = True
    db.commit()
    return {"message": f"Пользователь {user.first_name} назначен администратором"}

@router.post("/users/{user_id}/remove-admin")
async def remove_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Убрать права администратора у пользователя"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя убрать права у самого себя")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.is_admin = False
    db.commit()
    return {"message": f"Права администратора убраны у пользователя {user.first_name}"}

@router.post("/users/make-admin-by-username")
async def make_user_admin_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Назначить пользователя администратором по username"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь с таким username не найден")
    
    user.is_admin = True
    db.commit()
    return {"message": f"Пользователь @{username} назначен администратором"}

# HR System endpoints

@router.post("/positions", response_model=PositionSchema)
async def create_position(
    position: PositionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Создать новую позицию"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Извлекаем quality_ids из данных позиции
        quality_ids = position.quality_ids or []
        position_data = position.dict(exclude={'quality_ids'})
        
        logger.info(f"Создание позиции: {position_data}")
        
        # Создаем позицию
        db_position = Position(**position_data)
        db.add(db_position)
        db.commit()
        db.refresh(db_position)
        
        logger.info(f"Позиция создана с ID: {db_position.id}")
        
        # Временно отключаем добавление качеств из-за ошибки в модели
        # TODO: Исправить модель PositionQuality
        # for quality_id in quality_ids:
        #     quality = db.query(Quality).filter(Quality.id == quality_id).first()
        #     if quality:
        #         position_quality = PositionQuality(
        #             position_id=db_position.id,
        #             quality_id=quality_id,
        #             weight=1
        #         )
        #         db.add(position_quality)
        # 
        # db.commit()
        return db_position
        
    except Exception as e:
        logger.error(f"Ошибка при создании позиции: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании позиции: {str(e)}")

@router.get("/positions", response_model=List[PositionWithQualities])
async def get_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить все позиции с качествами"""
    positions = db.query(Position).all()
    return positions

@router.put("/positions/{position_id}", response_model=PositionSchema)
async def update_position(
    position_id: int,
    position_update: PositionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Обновить позицию"""
    db_position = db.query(Position).filter(Position.id == position_id).first()
    if not db_position:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    
    for field, value in position_update.dict(exclude_unset=True).items():
        setattr(db_position, field, value)
    
    db.commit()
    db.refresh(db_position)
    return db_position

@router.delete("/positions/{position_id}")
async def delete_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Удалить позицию"""
    db_position = db.query(Position).filter(Position.id == position_id).first()
    if not db_position:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    
    db.delete(db_position)
    db.commit()
    return {"message": "Позиция удалена"}

@router.post("/qualities", response_model=QualitySchema)
async def create_quality(
    quality: QualityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Создать новое качество"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        quality_data = quality.dict()
        logger.info(f"Создание качества: {quality_data}")
        
        db_quality = Quality(**quality_data)
        db.add(db_quality)
        db.commit()
        db.refresh(db_quality)
        
        logger.info(f"Качество создано с ID: {db_quality.id}")
        return db_quality
        
    except Exception as e:
        logger.error(f"Ошибка при создании качества: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании качества: {str(e)}")

@router.get("/qualities", response_model=List[QualitySchema])
async def get_qualities(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить все качества"""
    qualities = db.query(Quality).all()
    return qualities

@router.post("/positions/{position_id}/qualities/{quality_id}")
async def add_quality_to_position(
    position_id: int,
    quality_id: int,
    weight: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Добавить качество к позиции"""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    
    quality = db.query(Quality).filter(Quality.id == quality_id).first()
    if not quality:
        raise HTTPException(status_code=404, detail="Качество не найдено")
    
    position_quality = PositionQuality(
        position_id=position_id,
        quality_id=quality_id,
        weight=weight
    )
    db.add(position_quality)
    db.commit()
    return {"message": f"Качество '{quality.name}' добавлено к позиции '{position.title}'"}

@router.delete("/positions/{position_id}/qualities/{quality_id}")
async def remove_quality_from_position(
    position_id: int,
    quality_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Удалить качество из позиции"""
    position_quality = db.query(PositionQuality).filter(
        PositionQuality.position_id == position_id,
        PositionQuality.quality_id == quality_id
    ).first()
    
    if not position_quality:
        raise HTTPException(status_code=404, detail="Связь позиция-качество не найдена")
    
    db.delete(position_quality)
    db.commit()
    return {"message": "Качество удалено из позиции"}

@router.get("/interviews", response_model=List[InterviewWithUser])
async def get_all_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить все интервью (только для админов)"""
    interviews = db.query(Interview).all()
    return interviews

@router.get("/interviews/stats")
async def get_interview_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить статистику интервью"""
    total_interviews = db.query(Interview).count()
    completed_interviews = db.query(Interview).filter(Interview.status == "completed").count()
    in_progress_interviews = db.query(Interview).filter(Interview.status == "in_progress").count()
    
    # Средний балл
    avg_score = db.query(Interview.score).filter(
        Interview.status == "completed",
        Interview.score.isnot(None)
    ).all()
    avg_score = sum([score[0] for score in avg_score]) / len(avg_score) if avg_score else 0
    
    return {
        "total_interviews": total_interviews,
        "completed_interviews": completed_interviews,
        "in_progress_interviews": in_progress_interviews,
        "average_score": round(avg_score, 2)
    } 