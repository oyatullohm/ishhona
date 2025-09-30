from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from main.models import CustomUser, BotSettings
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from aiogram.filters import Command
from bot.keyboards import worker_kb
from aiogram import Router, F

router = Router()

class WorkerLogin(StatesGroup):
    waiting_for_password = State()

@router.message(Command("worker"))
async def cmd_worker(message: Message, state: FSMContext, user):
    if user and user.is_worker:
        await message.answer("Siz allaqachon workersiz!", reply_markup=worker_kb.main_menu())
        user.is_staff = False
        user.is_deliverer = False
        await sync_to_async(user.save)()
        return
    
    await message.answer("🔐 worker parolini kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(WorkerLogin.waiting_for_password)

@router.message(WorkerLogin.waiting_for_password)
async def process_worker_password(message: Message, state: FSMContext, user):
    worker = await sync_to_async(BotSettings.objects.last)()
    if message.text == worker.worker_password:
        if user:
            user.is_worker = True
            user.is_staff = False
            await sync_to_async(user.save)()
        else:
            user = await sync_to_async(CustomUser.objects.create)(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                # is_staff=True,
                is_worker = True,
                is_active=True
            )
        
        await message.answer("✅ Ishci paneliga kirdingiz!", reply_markup=worker_kb.main_menu())

        await state.clear()
    else:
        await message.answer("❌ Noto'g'ri parol. Qayta urinib ko'ring:")