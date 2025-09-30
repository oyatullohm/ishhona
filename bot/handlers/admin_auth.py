from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from main.models import CustomUser,BotSettings
from asgiref.sync import sync_to_async
from aiogram.filters import Command
from bot.keyboards import admin_kb
from aiogram import Router, F
router = Router()

class AdminLogin(StatesGroup):
    waiting_for_password = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, user):
    if user and user.is_staff:
        await message.answer("Siz allaqachon adminsiz!", reply_markup=admin_kb.admin_main_menu())
        user.is_worker = False
        user.is_deliverer = False
        await sync_to_async(user.save)()

        return
    
    await message.answer("🔐 Admin parolini kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdminLogin.waiting_for_password)

@router.message(AdminLogin.waiting_for_password)
async def process_admin_password(message: Message, state: FSMContext, user):
    admin = await sync_to_async(BotSettings.objects.last)()
    if message.text == admin.admin_password:
        if user:
            user.is_staff = True
            user.is_worker = False
            user.is_deliverer = False
            await sync_to_async(user.save)()
        else:
            user = await sync_to_async(CustomUser.objects.create)(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                is_staff=True,
                is_active=True
            )
        
        await message.answer("✅ Admin paneliga kirdingiz!", reply_markup=admin_kb.admin_main_menu())
        await state.clear()
    else:
        await message.answer("❌ Noto'g'ri parol. Qayta urinib ko'ring:")