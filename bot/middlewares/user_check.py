from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from asgiref.sync import sync_to_async
from main.models import CustomUser

class UserCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
        elif hasattr(event, 'message') and event.message and event.message.from_user:
            user_id = event.message.from_user.id
        else:
            data['user'] = None
            return await handler(event, data)

        try:
            user = await sync_to_async(CustomUser.objects.get)(telegram_id=user_id)
        except CustomUser.DoesNotExist:
            # ❗ User topilmasa — hech narsa qilmaymiz
            data['user'] = None
            return await handler(event, data)

        # faqat active bo'lsa ishlaydi
        if not user.is_active:
            if hasattr(event, "message"):
                await event.message.answer("❌ Sizning akkauntingiz bloklangan.")
            return  

        data['user'] = user
        return await handler(event, data)
