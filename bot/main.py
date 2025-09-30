import os
import django
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from django.conf import settings
from asgiref.sync import sync_to_async
from aiogram.types import  BotCommand
# Django ni sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Admin.settings')
django.setup()
from main.models import CustomUser

from bot.keyboards.admin_kb import PasswordLoginState
# Handlerni import qilish
from bot.handlers import (
    # client_handlers, 
    order_handlers,
    order_auth,
    driever_auth,
    deliverer_handlers,
    worker_auth,
    worker_handlers,
    # common_handlers,
    admin_auth, 
    admin_handlers    
)
from bot.middlewares.django_middleware import DjangoMiddleware
from bot.middlewares.user_check import UserCheckMiddleware
from aiogram import Router, F
router = Router()
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext, user):
    if user:  
        await message.answer("✅ Siz allaqachon ro‘yxatdan o'tgansiz.")
        return
    
    await message.answer("🔑 Botdan foydalanish uchun maxfiy parolni kiriting:")
    await state.set_state(PasswordLoginState.waiting_for_password)


@router.message(PasswordLoginState.waiting_for_password)
async def check_password(message: Message, state: FSMContext):
    password = message.text.strip()
    if password == "bot12345":
        user = await sync_to_async(CustomUser.objects.create)(
            telegram_id=message.from_user.id,
            username=message.from_user.username or f"user_{message.from_user.id}",
        
        )
    

        await message.answer(f"✅ Tabriklaymiz!  ro‘yxatdan o‘tdingiz.")
        await state.clear()
    else:
        await message.answer(f"notogri parol ")


@router.message(Command("cancel"), StateFilter("*"))
async def cancel_text_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.")

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="/start"),
        BotCommand(command="admin", description="/admin"),
        BotCommand(command="worker", description="/worker"),   
        BotCommand(command="order", description="/"),   
        BotCommand(command="drever", description="/drever"),
        BotCommand(command="cancel", description="/cancel"),  ] 
    await bot.set_my_commands(commands)


async def main():

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Dispatcher yaratish
    dp = Dispatcher()
    
    # Middleware qo'shish
    dp.update.middleware(DjangoMiddleware())
    dp.update.middleware(UserCheckMiddleware())
    
    # Handlerni ulash
    # dp.include_router(client_handlers.router)
    dp.include_router(router=router)
    dp.include_router(admin_auth.router)   
    dp.include_router(order_auth.router)   
    dp.include_router(worker_auth.router)
    dp.include_router(driever_auth.router)
    dp.include_router(admin_handlers.router) 
    dp.include_router(order_handlers.router) 
    dp.include_router(worker_handlers.router)
    dp.include_router(deliverer_handlers.router)
    
    
    # dp.include_router(order_handlers.router)
    # dp.include_router(payment_handlers.router)
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())