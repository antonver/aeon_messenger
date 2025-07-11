from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exc
from typing import List
import logging
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Position, Quality, PositionQuality, Interview
from app.schemas.position import PositionCreate, PositionUpdate, Position as PositionSchema, PositionWithQualities
from app.schemas.quality import QualityCreate, Quality as QualitySchema
from app.schemas.interview import Interview as InterviewSchema, InterviewWithUser
from app.schemas.user import User as UserSchema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

def check_admin_permissions(current_user: User = Depends(get_current_user)):
    """Проверяет права администратора"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )
    return current_user

# User management endpoints

@router.get("/users", response_model=List[UserSchema])
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить список всех пользователей"""
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        logger.error(f"Ошибка при получении пользователей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении пользователей")

@router.post("/users/make-admin-by-username")
async def make_user_admin_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Назначить пользователя администратором по username"""
    try:
        # Убираем @ если есть
        username = username.replace('@', '')

        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с username '{username}' не найден"
            )

        user.is_admin = True
        db.commit()

        return {"message": f"Пользователь @{username} успешно назначен администратором"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при назначении администратора: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при назначении администратора")

# Position management endpoints

@router.post("/positions", response_model=PositionSchema)
async def create_position(
    position: PositionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Создать новую позицию"""
    try:
        logger.info(f"Создание позиции: {position.dict()}")
        logger.info(f"Текущий пользователь: {current_user.id} ({current_user.username})")

        # Извлекаем quality_ids из данных позиции
        quality_ids = getattr(position, 'quality_ids', []) or []
        position_data = position.dict(exclude={'quality_ids'})
        
        logger.info(f"Данные позиции: {position_data}")
        logger.info(f"ID качеств: {quality_ids}")
        
        # Создаем позицию
        db_position = Position(**position_data)
        db.add(db_position)
        db.flush()  # Получаем ID без коммита

        logger.info(f"Позиция создана с ID: {db_position.id}")
        
        # Добавляем качества к позиции
        for quality_id in quality_ids:
            logger.info(f"Добавляем качество {quality_id} к позиции {db_position.id}")
            # Проверяем, что качество существует
            quality = db.query(Quality).filter(Quality.id == quality_id).first()
            if quality:
                logger.info(f"Качество {quality_id} найдено: {quality.name}")
                # Проверяем, что связь еще не существует
                existing = db.query(PositionQuality).filter(
                    PositionQuality.position_id == db_position.id,
                    PositionQuality.quality_id == quality_id
                ).first()

                if not existing:
                    position_quality = PositionQuality(
                        position_id=db_position.id,
                        quality_id=quality_id,
                        weight=1
                    )
                    db.add(position_quality)
                    logger.info(f"Связь позиция-качество создана")
                else:
                    logger.info(f"Связь позиция-качество уже существует")
            else:
                logger.warning(f"Качество с ID {quality_id} не найдено")

        db.commit()
        db.refresh(db_position)
        logger.info(f"Позиция успешно создана и сохранена")
        return db_position
        
    except exc.IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка целостности данных при создании позиции: {e}")
        raise HTTPException(status_code=400, detail="Позиция с таким названием уже существует")
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при создании позиции: {e}")
        logger.error(f"Тип ошибки: {type(e)}")
        logger.error(f"Детали ошибки: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании позиции: {str(e)}")

@router.get("/positions", response_model=List[PositionWithQualities])
async def get_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить все позиции с качествами"""
    try:
        # Используем joinedload для загрузки связанных качеств
        positions = db.query(Position).options(
            joinedload(Position.qualities).joinedload(PositionQuality.quality)
        ).all()

        logger.info(f"Found {len(positions)} positions")
        
        result = []
        for position in positions:
            # Извлекаем качества из связанных PositionQuality
            qualities = []
            for pq in position.qualities:
                if pq.quality:
                    qualities.append(pq.quality)
                    logger.info(f"Position {position.id} ({position.title}) has quality: {pq.quality.name}")

            logger.info(f"Position {position.id} ({position.title}) has {len(qualities)} qualities")

            # Создаем объект позиции с качествами
            position_with_qualities = PositionWithQualities(
                id=position.id,
                title=position.title,
                description=position.description,
                is_active=position.is_active,
                created_at=position.created_at,
                updated_at=position.updated_at,
                qualities=qualities
            )
            result.append(position_with_qualities)

        logger.info(f"Returning {len(result)} positions with qualities")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении позиций: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении позиций")

@router.get("/positions/{position_id}", response_model=PositionWithQualities)
async def get_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить позицию по ID с качествами"""
    try:
        position = db.query(Position).options(
            joinedload(Position.qualities).joinedload(PositionQuality.quality)
        ).filter(Position.id == position_id).first()
        
        if not position:
            raise HTTPException(status_code=404, detail="Позиция не найдена")

        # Извлекаем качества из связанных PositionQuality
        qualities = []
        for pq in position.qualities:
            if pq.quality:
                qualities.append(pq.quality)
                logger.info(f"Position {position.id} ({position.title}) has quality: {pq.quality.name}")

        logger.info(f"Position {position.id} ({position.title}) has {len(qualities)} qualities")

        return PositionWithQualities(
            id=position.id,
            title=position.title,
            description=position.description,
            is_active=position.is_active,
            created_at=position.created_at,
            updated_at=position.updated_at,
            qualities=qualities
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении позиции: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении позиции")

@router.put("/positions/{position_id}", response_model=PositionSchema)
async def update_position(
    position_id: int,
    position_update: PositionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Обновить позицию"""
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise HTTPException(status_code=404, detail="Позиция не найдена")

        update_data = position_update.dict(exclude_unset=True, exclude={'quality_ids'})
        for field, value in update_data.items():
            setattr(position, field, value)

        # Обновляем качества если они переданы
        if hasattr(position_update, 'quality_ids') and position_update.quality_ids is not None:
            # Удаляем старые связи
            db.query(PositionQuality).filter(PositionQuality.position_id == position_id).delete()

            # Добавляем новые связи
            for quality_id in position_update.quality_ids:
                quality = db.query(Quality).filter(Quality.id == quality_id).first()
                if quality:
                    position_quality = PositionQuality(
                        position_id=position_id,
                        quality_id=quality_id,
                        weight=1
                    )
                    db.add(position_quality)

        db.commit()
        db.refresh(position)
        return position
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении позиции: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении позиции")

@router.delete("/positions/{position_id}")
async def delete_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Удалить позицию"""
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise HTTPException(status_code=404, detail="Позиция не найдена")

        # Сначала удаляем связи с качествами
        db.query(PositionQuality).filter(PositionQuality.position_id == position_id).delete()

        # Затем удаляем позицию
        db.delete(position)
        db.commit()
        return {"message": "Позиция успешно удалена"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при удалении позиции: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении позиции")

# Quality management endpoints

@router.post("/qualities", response_model=QualitySchema)
async def create_quality(
    quality: QualityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Создать новое качество"""
    try:
        quality_data = quality.dict()
        logger.info(f"Создание качества: {quality_data}")
        logger.info(f"Текущий пользователь: {current_user.id} ({current_user.username})")
        
        db_quality = Quality(**quality_data)
        db.add(db_quality)
        db.commit()
        db.refresh(db_quality)
        
        logger.info(f"Качество создано с ID: {db_quality.id}")
        return db_quality
        
    except exc.IntegrityError as e:
        db.rollback()
        logger.error(f"Ошибка целостности данных при создании качества: {e}")
        raise HTTPException(status_code=400, detail="Качество с таким названием уже существует")
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при создании качества: {e}")
        logger.error(f"Тип ошибки: {type(e)}")
        logger.error(f"Детали ошибки: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании качества: {str(e)}")

@router.get("/qualities", response_model=List[QualitySchema])
async def get_qualities(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить все качества"""
    try:
        qualities = db.query(Quality).all()
        return qualities
    except Exception as e:
        logger.error(f"Ошибка при получении качеств: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении качеств")

@router.get("/qualities/{quality_id}", response_model=QualitySchema)
async def get_quality(
    quality_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить качество по ID"""
    quality = db.query(Quality).filter(Quality.id == quality_id).first()
    if not quality:
        raise HTTPException(status_code=404, detail="Качество не найдено")
    return quality

@router.put("/qualities/{quality_id}", response_model=QualitySchema)
async def update_quality(
    quality_id: int,
    quality_update: QualityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Обновить качество"""
    quality = db.query(Quality).filter(Quality.id == quality_id).first()
    if not quality:
        raise HTTPException(status_code=404, detail="Качество не найдено")
    
    update_data = quality_update.dict()
    for field, value in update_data.items():
        setattr(quality, field, value)
    
    db.commit()
    db.refresh(quality)
    return quality

@router.delete("/qualities/{quality_id}")
async def delete_quality(
    quality_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Удалить качество"""
    quality = db.query(Quality).filter(Quality.id == quality_id).first()
    if not quality:
        raise HTTPException(status_code=404, detail="Качество не найдено")
    
    db.delete(quality)
    db.commit()
    return {"message": "Качество успешно удалено"}

# Position-Quality relationship endpoints

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
    
    # Проверяем, не существует ли уже такая связь
    existing_relation = db.query(PositionQuality).filter(
        PositionQuality.position_id == position_id,
        PositionQuality.quality_id == quality_id
    ).first()
    
    if existing_relation:
        raise HTTPException(status_code=400, detail="Качество уже добавлено к этой позиции")
    
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

# Interview management endpoints

@router.get("/interviews", response_model=List[InterviewSchema])
async def get_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить все интервью"""
    interviews = db.query(Interview).all()
    return interviews

@router.get("/interviews/{interview_id}", response_model=InterviewSchema)
async def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permissions)
):
    """Получить интервью по ID"""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Интервью не найдено")
    return interview
