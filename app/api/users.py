from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import and_
from app.models.chat_invitation import ChatInvitation
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()

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