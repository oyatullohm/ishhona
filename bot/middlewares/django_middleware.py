from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from asgiref.sync import sync_to_async

class DjangoMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Bu yerda Django bilan ishlash uchun kerakli ma'lumotlarni qo'shish mumkin
        return await handler(event, data)