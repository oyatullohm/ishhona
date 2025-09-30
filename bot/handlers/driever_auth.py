from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from main.models import CustomUser, BotSettings
from aiogram.fsm.context import FSMContext
from bot.keyboards import deliverer_kb
from asgiref.sync import sync_to_async
from aiogram.filters import Command
from aiogram import Router, F

router = Router()

class DeliverLogin(StatesGroup):
    deliver_for_password = State()

@router.message(Command("drever"))
async def cmd_driever(message: Message, state: FSMContext, user):
    if user and user.is_deliverer:
        await message.answer("Siz allaqachon drever siz !", reply_markup=deliverer_kb.main_menu())
        user.is_staff = False 
        user.is_worker = False 
        user.is_deliverer = True
        await sync_to_async(user.save)()
        return
    
    await message.answer("🔐 driever parolini kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(DeliverLogin.deliver_for_password)

@router.message(DeliverLogin.deliver_for_password)
async def process_driever_password(message: Message, state: FSMContext, user):
    worker = await sync_to_async(BotSettings.objects.last)()
    if message.text == worker.driver_password:
        if user:
            user.is_deliverer = True
            user.is_worker = False 
            user.is_staff = False
            await sync_to_async(user.save)()
        else:
            user = await sync_to_async(CustomUser.objects.create)(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                # is_staff=True,
                is_deliverer = True,
                is_active=True
            )
        
        await message.answer("✅ Driever paneliga kirdingiz!", reply_markup=deliverer_kb.main_menu())

        await state.clear()
    else:
        await message.answer("❌ Noto'g'ri parol. Qayta urinib ko'ring:")