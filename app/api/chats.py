from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.chat import Chat, chat_members
from app.models.message import Message
from app.schemas.chat import ChatCreate, ChatUpdate, Chat as ChatSchema, ChatList, UserInChat
from app.auth.dependencies import get_current_user
from sqlalchemy import and_, desc

router = APIRouter(prefix="/chats", tags=["chats"])


def get_chat_with_members(db: Session, chat_id: int) -> Optional[ChatSchema]:
    """
    Вспомогательная функция для получения чата с правильной информацией о членах
    """
    # Получаем основную информацию о чате
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        return None
    
    # Получаем информацию о членах чата с данными из промежуточной таблицы
    members_query = db.query(
        User.id,
        User.telegram_id,
        User.username,
        User.first_name,
        User.last_name,
        User.profile_photo_url,
        chat_members.c.is_admin,
        chat_members.c.joined_at
    ).join(
        chat_members, User.id == chat_members.c.user_id
    ).filter(
        chat_members.c.chat_id == chat_id
    ).all()
    
    # Формируем список членов чата
    members = []
    for member_data in members_query:
        member = UserInChat(
            id=member_data.id,
            telegram_id=member_data.telegram_id,
            username=member_data.username,
            first_name=member_data.first_name,
            last_name=member_data.last_name,
            profile_photo_url=member_data.profile_photo_url,
            is_admin=member_data.is_admin,
            joined_at=member_data.joined_at
        )
        members.append(member)
    
    # Формируем объект чата
    chat_schema = ChatSchema(
        id=chat.id,
        title=chat.title,
        chat_type=chat.chat_type,
        description=chat.description,
        photo_url=chat.photo_url,
        created_by=chat.created_by,
        is_active=chat.is_active,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        members=members
    )
    
    return chat_schema


@router.get("/", response_model=List[ChatList])
async def get_user_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка чатов пользователя
    """
    # Получаем чаты пользователя через промежуточную таблицу
    chats_query = db.query(Chat).join(
        chat_members, Chat.id == chat_members.c.chat_id
    ).filter(
        and_(
            chat_members.c.user_id == current_user.id,
            Chat.is_active == True
        )
    ).order_by(desc(Chat.updated_at))
    
    chats = chats_query.all()
    
    # Формируем список чатов с дополнительной информацией
    chat_list = []
    for chat in chats:
        # Получаем последнее сообщение
        last_message = db.query(Message).filter(
            and_(
                Message.chat_id == chat.id,
                Message.is_deleted == False
            )
        ).order_by(desc(Message.created_at)).first()
        
        # Подсчитываем непрочитанные сообщения (временно отключено)
        unread_count = 0  # TODO: Исправить запрос для JSON поля
        
        chat_data = ChatList(
            id=chat.id,
            title=chat.title,
            chat_type=chat.chat_type,
            photo_url=chat.photo_url,
            last_message=last_message.text if last_message else None,
            last_message_time=last_message.created_at if last_message else None,
            unread_count=unread_count
        )
        chat_list.append(chat_data)
    
    return chat_list


@router.post("/", response_model=ChatSchema)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Создание нового чата
    """
    # Создаем чат
    new_chat = Chat(
        title=chat_data.title,
        chat_type=chat_data.chat_type,
        description=chat_data.description,
        photo_url=chat_data.photo_url,
        created_by=current_user.id
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    
    # Добавляем создателя в чат как администратора
    db.execute(
        chat_members.insert().values(
            user_id=current_user.id,
            chat_id=new_chat.id,
            is_admin=True
        )
    )
    
    # Добавляем других участников
    for member_id in chat_data.member_ids:
        if member_id != current_user.id:
            # Проверяем, что пользователь существует
            member = db.query(User).filter(User.id == member_id).first()
            if member:
                db.execute(
                    chat_members.insert().values(
                        user_id=member_id,
                        chat_id=new_chat.id,
                        is_admin=False
                    )
                )
    
    db.commit()
    
    # Возвращаем созданный чат с участниками
    return get_chat_with_members(db, new_chat.id)


@router.get("/{chat_id}", response_model=ChatSchema)
async def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение информации о чате
    """
    # Проверяем, что пользователь является участником чата
    is_member = db.query(chat_members).filter(
        and_(
            chat_members.c.user_id == current_user.id,
            chat_members.c.chat_id == chat_id
        )
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    chat = get_chat_with_members(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    return chat


@router.put("/{chat_id}", response_model=ChatSchema)
async def update_chat(
    chat_id: int,
    chat_data: ChatUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновление информации о чате
    """
    # Проверяем, что пользователь является администратором чата
    is_admin = db.query(chat_members).filter(
        and_(
            chat_members.c.user_id == current_user.id,
            chat_members.c.chat_id == chat_id,
            chat_members.c.is_admin == True
        )
    ).first()
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    # Обновляем данные чата
    if chat_data.title is not None:
        chat.title = chat_data.title
    if chat_data.description is not None:
        chat.description = chat_data.description
    if chat_data.photo_url is not None:
        chat.photo_url = chat_data.photo_url
    
    db.commit()
    db.refresh(chat)
    
    return get_chat_with_members(db, chat_id)


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Удаление чата (только для создателя)
    """
    chat = db.query(Chat).filter(
        and_(
            Chat.id == chat_id,
            Chat.created_by == current_user.id
        )
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден или недостаточно прав")
    
    # Помечаем чат как неактивный
    chat.is_active = False
    db.commit()
    
    return {"message": "Чат успешно удален"}


@router.post("/{chat_id}/members/{user_id}")
async def add_member_to_chat(
    chat_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Добавление участника в чат
    """
    # Проверяем, что пользователь является администратором чата
    is_admin = db.query(chat_members).filter(
        and_(
            chat_members.c.user_id == current_user.id,
            chat_members.c.chat_id == chat_id,
            chat_members.c.is_admin == True
        )
    ).first()
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    # Проверяем, что пользователь существует
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверяем, что пользователь еще не является участником
    existing_member = db.query(chat_members).filter(
        and_(
            chat_members.c.user_id == user_id,
            chat_members.c.chat_id == chat_id
        )
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="Пользователь уже является участником чата")
    
    # Добавляем пользователя в чат
    db.execute(
        chat_members.insert().values(
            user_id=user_id,
            chat_id=chat_id,
            is_admin=False
        )
    )
    db.commit()
    
    return {"message": "Участник успешно добавлен"}


@router.delete("/{chat_id}/members/{user_id}")
async def remove_member_from_chat(
    chat_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Удаление участника из чата
    """
    # Проверяем, что пользователь является администратором чата или удаляет себя
    is_admin = db.query(chat_members).filter(
        and_(
            chat_members.c.user_id == current_user.id,
            chat_members.c.chat_id == chat_id,
            chat_members.c.is_admin == True
        )
    ).first()
    
    if not is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    # Удаляем участника из чата
    result = db.execute(
        chat_members.delete().where(
            and_(
                chat_members.c.user_id == user_id,
                chat_members.c.chat_id == chat_id
            )
        )
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Участник не найден в чате")
    
    db.commit()
    
    return {"message": "Участник успешно удален"} 