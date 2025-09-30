from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from django.conf import settings
from main.models import CustomUser,BotSettings
from bot.keyboards import order_kb
from asgiref.sync import sync_to_async


router = Router()

class OrderLogin(StatesGroup):
    waiting_for_password = State()

@router.message(Command("order"))
async def cmd_order(message: Message, state: FSMContext, user):
    if user and user.is_order:
        await message.answer("Siz allaqachon sotuchisiz!", reply_markup=order_kb.main_menu())
        # user.is_worker = False
        # user.is_deliverer = False
        await sync_to_async(user.save)()

        return
    
    await message.answer("🔐 order parolini kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OrderLogin.waiting_for_password)

@router.message(OrderLogin.waiting_for_password)
async def process_admin_password(message: Message, state: FSMContext, user):
    admin = await sync_to_async(BotSettings.objects.last)()
    if message.text == admin.order_password:
        if user:
            pass
        else:
            user = await sync_to_async(CustomUser.objects.create)(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                is_staff=True,
                is_active=True
            )
        
        await message.answer("✅ Savdo paneliga kirdingiz!", reply_markup=order_kb.main_menu())
        await state.clear()
    else:
        await message.answer("❌ Noto'g'ri parol. Qayta urinib ko'ring:")
