from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from app.models.user import User


class ConnectionManager:
    def __init__(self):
        # Словарь: user_id -> список WebSocket соединений
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Словарь: chat_id -> set пользователей в чате
        self.chat_users: Dict[int, Set[int]] = {}
        # Словарь: user_id -> set чатов пользователя
        self.user_chats: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user: User):
        """
        Подключение пользователя к WebSocket
        """
        await websocket.accept()
        
        if user.id not in self.active_connections:
            self.active_connections[user.id] = []
        
        self.active_connections[user.id].append(websocket)
        
        # Отправляем подтверждение подключения
        await self.send_personal_message({
            "type": "connection_established",
            "user_id": user.id,
            "message": "Соединение установлено"
        }, user.id)

    def disconnect(self, websocket: WebSocket, user_id: int):
        """
        Отключение пользователя от WebSocket
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Если у пользователя нет активных соединений, удаляем его
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Удаляем пользователя из всех чатов
                if user_id in self.user_chats:
                    for chat_id in self.user_chats[user_id]:
                        if chat_id in self.chat_users:
                            self.chat_users[chat_id].discard(user_id)
                            if not self.chat_users[chat_id]:
                                del self.chat_users[chat_id]
                    del self.user_chats[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        """
        Отправка личного сообщения пользователю
        """
        if user_id in self.active_connections:
            message_json = json.dumps(message, ensure_ascii=False, default=str)
            
            # Отправляем сообщение всем активным соединениям пользователя
            disconnected_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_json)
                except Exception:
                    disconnected_connections.append(connection)
            
            # Удаляем неактивные соединения
            for connection in disconnected_connections:
                self.active_connections[user_id].remove(connection)

    async def send_to_chat(self, message: dict, chat_id: int, exclude_user_id: int = None):
        """
        Отправка сообщения всем участникам чата
        """
        if chat_id in self.chat_users:
            for user_id in self.chat_users[chat_id]:
                if exclude_user_id is None or user_id != exclude_user_id:
                    await self.send_personal_message(message, user_id)

    def join_chat(self, user_id: int, chat_id: int):
        """
        Добавление пользователя в чат для WebSocket уведомлений
        """
        if chat_id not in self.chat_users:
            self.chat_users[chat_id] = set()
        
        self.chat_users[chat_id].add(user_id)
        
        if user_id not in self.user_chats:
            self.user_chats[user_id] = set()
        
        self.user_chats[user_id].add(chat_id)

    def leave_chat(self, user_id: int, chat_id: int):
        """
        Удаление пользователя из чата для WebSocket уведомлений
        """
        if chat_id in self.chat_users:
            self.chat_users[chat_id].discard(user_id)
            if not self.chat_users[chat_id]:
                del self.chat_users[chat_id]
        
        if user_id in self.user_chats:
            self.user_chats[user_id].discard(chat_id)
            if not self.user_chats[user_id]:
                del self.user_chats[user_id]

    async def broadcast_typing(self, chat_id: int, user_id: int, is_typing: bool):
        """
        Уведомление о том, что пользователь печатает
        """
        message = {
            "type": "typing",
            "chat_id": chat_id,
            "user_id": user_id,
            "is_typing": is_typing
        }
        
        await self.send_to_chat(message, chat_id, exclude_user_id=user_id)

    async def broadcast_message(self, message_data: dict, chat_id: int):
        """
        Рассылка нового сообщения участникам чата
        """
        message = {
            "type": "new_message",
            "chat_id": chat_id,
            "message": message_data
        }
        
        await self.send_to_chat(message, chat_id)

    async def broadcast_message_read(self, message_id: int, chat_id: int, user_id: int):
        """
        Уведомление о прочтении сообщения
        """
        message = {
            "type": "message_read",
            "message_id": message_id,
            "chat_id": chat_id,
            "user_id": user_id
        }
        
        await self.send_to_chat(message, chat_id, exclude_user_id=user_id)

    async def broadcast_user_online(self, user_id: int, is_online: bool):
        """
        Уведомление об изменении статуса пользователя
        """
        message = {
            "type": "user_status",
            "user_id": user_id,
            "is_online": is_online
        }
        
        # Отправляем всем чатам, где есть этот пользователь
        if user_id in self.user_chats:
            for chat_id in self.user_chats[user_id]:
                await self.send_to_chat(message, chat_id, exclude_user_id=user_id)


# Глобальный менеджер соединений
manager = ConnectionManager() 