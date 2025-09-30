from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Ombor Holati"),KeyboardButton(text="➕ Ishlab chiqarish")],
 
            [KeyboardButton(text="🛠️ Materiallar"),KeyboardButton(text="💴 Balans")],
            [KeyboardButton(text="🛠️ Men Chiqardim")],

        ],
        resize_keyboard=True
    )

class PaginationStates(StatesGroup):
    viewing_transactions = State()

class CostPaginationStates(StatesGroup):
    viewing_transactions = State()
    
class ProductionState(StatesGroup):
    choosing_product = State()
    entering_quantity = State()
    confirming = State()
