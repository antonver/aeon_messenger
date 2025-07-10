from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import and_
from typing import List
from app.models.chat_invitation import ChatInvitation
from app.database import get_db
from app.models.user import User
from app.models.chat import chat_members
from app.schemas.user import UserCreate, UserUpdate, User as UserSchema, UserList, SubordinateBase
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Получение информации о текущем пользователе
    """
    return current_user


@router.get("/admin-status")
async def get_admin_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Проверка статуса администратора и информации о первом входе
    """
    # Проверяем, есть ли администраторы в системе
    admin_count = db.query(User).filter(User.is_admin == True).count()
    total_users = db.query(User).count()
    
    return {
        "is_admin": current_user.is_admin,
        "is_first_user": total_users == 1,
        "admin_count": admin_count,
        "total_users": total_users,
        "message": "Первый пользователь автоматически становится администратором" if total_users == 1 and current_user.is_admin else None
    }


@router.put("/me", response_model=UserSchema)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновление информации о текущем пользователе
    """
    for field, value in user_data.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/", response_model=UserList)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка пользователей с пагинацией
    """
    # Получаем общее количество пользователей
    total = db.query(User).filter(User.is_active == True).count()
    
    # Получаем пользователей с пагинацией
    offset = (page - 1) * per_page
    users = db.query(User).filter(
        User.is_active == True
    ).offset(offset).limit(per_page).all()
    
    return UserList(
        users=users,
        total=total,
        page=page,
        per_page=per_page,
        has_next=offset + per_page < total,
        has_prev=page > 1
    )


@router.get("/subordinates", response_model=List[UserSchema])
async def get_subordinates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка подчиненных текущего пользователя
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут просматривать подчиненных")
    
    return current_user.subordinates


@router.post("/subordinates", response_model=UserSchema)
async def add_subordinate(
    subordinate_data: SubordinateBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Добавление подчиненного для текущего пользователя
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут добавлять подчиненных")
    
    # Проверяем существование пользователя
    subordinate = db.query(User).filter(User.id == subordinate_data.subordinate_id).first()
    if not subordinate:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверяем, не является ли пользователь уже подчиненным
    if subordinate in current_user.subordinates:
        raise HTTPException(status_code=400, detail="Пользователь уже является подчиненным")
    
    # Добавляем подчиненного
    current_user.subordinates.append(subordinate)
    db.commit()
    db.refresh(current_user)
    
    return subordinate


@router.delete("/subordinates/{subordinate_id}", response_model=UserSchema)
async def remove_subordinate(
    subordinate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Удаление подчиненного у текущего пользователя
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут удалять подчиненных")
    
    # Проверяем существование пользователя
    subordinate = db.query(User).filter(User.id == subordinate_id).first()
    if not subordinate:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверяем, является ли пользователь подчиненным
    if subordinate not in current_user.subordinates:
        raise HTTPException(status_code=400, detail="Пользователь не является подчиненным")
    
    # Удаляем подчиненного
    current_user.subordinates.remove(subordinate)
    db.commit()
    db.refresh(current_user)
    
    return subordinate


@router.post("/check-invitations")
async def check_and_accept_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Проверка и активация приглашений для текущего пользователя
    """
    if not current_user.username:
        return {"message": "У пользователя нет username", "accepted": 0}
    
    # Находим активные приглашения для этого username
    invitations = db.query(ChatInvitation).filter(
        and_(
            ChatInvitation.username == current_user.username,
            ChatInvitation.is_active == True
        )
    ).all()
    
    accepted_count = 0
    
    for invitation in invitations:
        # Проверяем, что пользователь еще не является участником чата
        existing_member = db.query(chat_members).filter(
            and_(
                chat_members.c.user_id == current_user.id,
                chat_members.c.chat_id == invitation.chat_id
            )
        ).first()
        
        if not existing_member:
            # Добавляем пользователя в чат
            db.execute(
                chat_members.insert().values(
                    user_id=current_user.id,
                    chat_id=invitation.chat_id,
                    is_admin=False
                )
            )
            accepted_count += 1
        
        # Деактивируем приглашение
        invitation.is_active = False
        invitation.accepted_at = func.now()
    
    db.commit()
    
    return {"message": f"Принято {accepted_count} приглашений", "accepted": accepted_count} 