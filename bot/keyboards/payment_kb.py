from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def payment_methods_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="💵 Naqt", callback_data="pay_cash")],
        [InlineKeyboardButton(text="💳 Karta", callback_data="pay_card")],
        [InlineKeyboardButton(text="🏦 Bank o'tkazmasi", callback_data="pay_transfer")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)