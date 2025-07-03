from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.chat import chat_members
from app.auth.telegram import validate_telegram_data, extract_user_info
from app.websocket.manager import manager
from sqlalchemy import and_
import json

router = APIRouter()


async def get_websocket_user(websocket: WebSocket, db: Session) -> User:
    """
    Получение пользователя для WebSocket соединения
    """
    # Получаем данные авторизации из query параметров
    query_params = dict(websocket.query_params)
    init_data = query_params.get('init_data')
    
    if not init_data:
        await websocket.close(code=4001, reason="Отсутствуют данные авторизации")
        raise HTTPException(status_code=401, detail="Отсутствуют данные авторизации")
    
    # Валидируем данные от Telegram
    validated_data = validate_telegram_data(init_data)
    if not validated_data:
        await websocket.close(code=4001, reason="Недействительные данные авторизации")
        raise HTTPException(status_code=401, detail="Недействительные данные авторизации")
    
    # Извлекаем информацию о пользователе
    user_info = extract_user_info(validated_data)
    telegram_id = user_info.get('telegram_id')
    
    if not telegram_id:
        await websocket.close(code=4001, reason="Отсутствует ID пользователя")
        raise HTTPException(status_code=401, detail="Отсутствует ID пользователя")
    
    # Ищем пользователя в базе данных
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        await websocket.close(code=4001, reason="Пользователь не найден")
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    return user


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint для реального времени
    """
    try:
        # Получаем пользователя
        user = await get_websocket_user(websocket, db)
        
        # Подключаем пользователя
        await manager.connect(websocket, user)
        
        # Добавляем пользователя во все его чаты
        user_chat_ids = db.query(chat_members.c.chat_id).filter(
            chat_members.c.user_id == user.id
        ).all()
        
        for (chat_id,) in user_chat_ids:
            manager.join_chat(user.id, chat_id)
        
        # Уведомляем о том, что пользователь онлайн
        await manager.broadcast_user_online(user.id, True)
        
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get('type')
                
                if message_type == 'typing':
                    # Обработка уведомления о печати
                    chat_id = message.get('chat_id')
                    is_typing = message.get('is_typing', False)
                    
                    if chat_id:
                        # Проверяем, что пользователь является участником чата
                        is_member = db.query(chat_members).filter(
                            and_(
                                chat_members.c.user_id == user.id,
                                chat_members.c.chat_id == chat_id
                            )
                        ).first()
                        
                        if is_member:
                            await manager.broadcast_typing(chat_id, user.id, is_typing)
                
                elif message_type == 'join_chat':
                    # Подключение к чату
                    chat_id = message.get('chat_id')
                    
                    if chat_id:
                        # Проверяем, что пользователь является участником чата
                        is_member = db.query(chat_members).filter(
                            and_(
                                chat_members.c.user_id == user.id,
                                chat_members.c.chat_id == chat_id
                            )
                        ).first()
                        
                        if is_member:
                            manager.join_chat(user.id, chat_id)
                
                elif message_type == 'leave_chat':
                    # Отключение от чата
                    chat_id = message.get('chat_id')
                    
                    if chat_id:
                        manager.leave_chat(user.id, chat_id)
                
                elif message_type == 'ping':
                    # Пинг для поддержания соединения
                    await manager.send_personal_message({
                        "type": "pong"
                    }, user.id)
                
            except json.JSONDecodeError:
                # Игнорируем некорректные JSON сообщения
                continue
            except Exception as e:
                # Логируем ошибки
                print(f"Ошибка обработки WebSocket сообщения: {e}")
                continue
    
    except WebSocketDisconnect:
        # Обрабатываем отключение
        manager.disconnect(websocket, user.id)
        await manager.broadcast_user_online(user.id, False)
    
    except Exception as e:
        # Обрабатываем другие ошибки
        print(f"Ошибка WebSocket соединения: {e}")
        try:
            manager.disconnect(websocket, user.id)
            await manager.broadcast_user_online(user.id, False)
        except:
            pass 