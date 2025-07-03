from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.chat import Chat, chat_members
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageUpdate, Message as MessageSchema, MessageList
from app.auth.dependencies import get_current_user
from sqlalchemy import and_, desc, asc
import os
import uuid
from app.config import settings

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/chat/{chat_id}", response_model=MessageList)
async def get_chat_messages(
    chat_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение сообщений из чата с пагинацией
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
    
    # Получаем общее количество сообщений
    total = db.query(Message).filter(
        and_(
            Message.chat_id == chat_id,
            Message.is_deleted == False
        )
    ).count()
    
    # Получаем сообщения с пагинацией (сначала новые)
    offset = (page - 1) * per_page
    messages = db.query(Message).filter(
        and_(
            Message.chat_id == chat_id,
            Message.is_deleted == False
        )
    ).order_by(desc(Message.created_at)).offset(offset).limit(per_page).all()
    
    # Обратный порядок для отображения (старые сначала)
    messages.reverse()
    
    return MessageList(
        messages=messages,
        total=total,
        page=page,
        per_page=per_page,
        has_next=offset + per_page < total,
        has_prev=page > 1
    )


@router.post("/", response_model=MessageSchema)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Отправка сообщения в чат
    """
    # Проверяем, что пользователь является участником чата
    is_member = db.query(chat_members).filter(
        and_(
            chat_members.c.user_id == current_user.id,
            chat_members.c.chat_id == message_data.chat_id
        )
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    # Проверяем, что чат существует и активен
    chat = db.query(Chat).filter(
        and_(
            Chat.id == message_data.chat_id,
            Chat.is_active == True
        )
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    # Создаем сообщение
    new_message = Message(
        chat_id=message_data.chat_id,
        sender_id=current_user.id,
        text=message_data.text,
        message_type=message_data.message_type,
        reply_to_message_id=message_data.reply_to_message_id
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Обновляем время последнего обновления чата
    chat.updated_at = new_message.created_at
    db.commit()
    
    return new_message


@router.put("/{message_id}", response_model=MessageSchema)
async def edit_message(
    message_id: int,
    message_data: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Редактирование сообщения
    """
    message = db.query(Message).filter(
        and_(
            Message.id == message_id,
            Message.sender_id == current_user.id,
            Message.is_deleted == False
        )
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    # Обновляем текст сообщения
    if message_data.text is not None:
        message.text = message_data.text
        message.is_edited = True
    
    db.commit()
    db.refresh(message)
    
    return message


@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Удаление сообщения
    """
    message = db.query(Message).filter(
        and_(
            Message.id == message_id,
            Message.sender_id == current_user.id,
            Message.is_deleted == False
        )
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    # Помечаем сообщение как удаленное
    message.is_deleted = True
    message.text = None  # Очищаем текст
    
    db.commit()
    
    return {"message": "Сообщение успешно удалено"}


@router.post("/{message_id}/read")
async def mark_message_as_read(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Отметка сообщения как прочитанного
    """
    message = db.query(Message).filter(
        and_(
            Message.id == message_id,
            Message.is_deleted == False
        )
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    # Проверяем, что пользователь является участником чата
    is_member = db.query(chat_members).filter(
        and_(
            chat_members.c.user_id == current_user.id,
            chat_members.c.chat_id == message.chat_id
        )
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    # Добавляем пользователя в список прочитавших
    if current_user.id not in message.read_by:
        message.read_by = message.read_by + [current_user.id]
        db.commit()
    
    return {"message": "Сообщение отмечено как прочитанное"}


@router.post("/chat/{chat_id}/read-all")
async def mark_all_messages_as_read(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Отметка всех сообщений в чате как прочитанных
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
    
    # Получаем все непрочитанные сообщения
    unread_messages = db.query(Message).filter(
        and_(
            Message.chat_id == chat_id,
            Message.is_deleted == False,
            ~Message.read_by.contains([current_user.id])
        )
    ).all()
    
    # Отмечаем все как прочитанные
    for message in unread_messages:
        message.read_by = message.read_by + [current_user.id]
    
    db.commit()
    
    return {"message": f"Отмечено как прочитанное {len(unread_messages)} сообщений"}


@router.post("/upload-media")
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Загрузка медиа файла
    """
    # Проверяем размер файла
    if file.size > settings.max_file_size:
        raise HTTPException(status_code=413, detail="Файл слишком большой")
    
    # Создаем директорию для загрузок если её нет
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    
    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Сохраняем файл
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при сохранении файла")
    
    # Определяем тип медиа
    media_type = "document"
    if file.content_type:
        if file.content_type.startswith("image/"):
            media_type = "photo"
        elif file.content_type.startswith("video/"):
            media_type = "video"
        elif file.content_type.startswith("audio/"):
            media_type = "audio"
    
    return {
        "media_url": f"/media/{unique_filename}",
        "media_type": file.content_type,
        "media_size": file.size,
        "message_type": media_type,
        "filename": file.filename
    }


@router.post("/forward")
async def forward_message(
    message_id: int,
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Пересылка сообщения в другой чат
    """
    # Проверяем, что исходное сообщение существует
    original_message = db.query(Message).filter(
        and_(
            Message.id == message_id,
            Message.is_deleted == False
        )
    ).first()
    
    if not original_message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    # Проверяем доступ к исходному чату
    is_member_source = db.query(chat_members).filter(
        and_(
            chat_members.c.user_id == current_user.id,
            chat_members.c.chat_id == original_message.chat_id
        )
    ).first()
    
    if not is_member_source:
        raise HTTPException(status_code=403, detail="Нет доступа к исходному сообщению")
    
    # Проверяем доступ к целевому чату
    is_member_target = db.query(chat_members).filter(
        and_(
            chat_members.c.user_id == current_user.id,
            chat_members.c.chat_id == chat_id
        )
    ).first()
    
    if not is_member_target:
        raise HTTPException(status_code=403, detail="Нет доступа к целевому чату")
    
    # Создаем пересланное сообщение
    forwarded_message = Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        text=original_message.text,
        message_type=original_message.message_type,
        media_url=original_message.media_url,
        media_type=original_message.media_type,
        media_size=original_message.media_size,
        media_duration=original_message.media_duration,
        forward_from_user_id=original_message.sender_id,
        forward_from_chat_id=original_message.chat_id
    )
    
    db.add(forwarded_message)
    db.commit()
    db.refresh(forwarded_message)
    
    return forwarded_message 