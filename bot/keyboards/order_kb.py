from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Clientga Savdo"), KeyboardButton(text="💰 Naq Pulga Savdo")],

            [ KeyboardButton(text="📦 Buyurtmalar_"), KeyboardButton(text="📦 Ombor__Holati__")],
            [ ]
        ],
        resize_keyboard=True
    )
def button_valyuta():
    keyboard = [
        [
            InlineKeyboardButton(text="UZS", callback_data="UZS"),
            # InlineKeyboardButton(text="USD", callback_data="USD"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def product_selection_keyboard(products):
    keyboard = []
    row = []
    for i, product in enumerate(products, start=1):
        row.append(InlineKeyboardButton(text=product.product_price.name, callback_data=f"select_pproduct_{product.id}"))
        if i % 2 == 0:  # har 2 tadan qator
            keyboard.append(row)
            row = []
    if row:  # oxirgi qator qolsa
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="✅ Yakunlash", callback_data="finish_order_")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def product_selection_keyboard_not_client(products):
    keyboard = []
    row = []
    for i, product in enumerate(products, start=1):
        row.append(InlineKeyboardButton(text=product.product_price.name, callback_data=f"select_ppproduct_{product.id}"))
        if i % 2 == 0:  # har 2 tadan qator
            keyboard.append(row)
            row = []
    if row:  # oxirgi qator qolsa
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="✅ Yakunlash_", callback_data="no_client_finish_order")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def client_selection_keyboard(clients):
    keyboard = []
    for client in clients:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{client.name} ({client.phone_number})",
                callback_data=f"select_cclient_{client.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def kassa_selection_keyboard(kassas):
    keyboard = []
    for kassa in kassas:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{kassa.name} {kassa.currency} ",
                callback_data=f"select_kassa_{kassa.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def products_keyboard(products):
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.product.name} - {product.product.selling_price} UZS",
                callback_data=f"product_{product.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def confirm_order_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order")],
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

class OrderPaginationStates(StatesGroup):
    viewing_orders = State()   
    

class OrderLogin(StatesGroup):
    waiting_for_password = State()

class DelivererStates(StatesGroup):
    selecting_order = State()
    updating_status = State()
    confirming_delivery = State()
    selecting_client = State()      # mijoz tanlash
    selecting_order = State()       # savdo ta'rifi kiritish
    selecting_product = State()     # mahsulot tanlash
    entering_quantity = State()  
    entering_quantity_NO_CLIENT = State()  
    selecting_product_NO_CLIENT = State()  
    entering_amount_NO_CLIENT = State()  
    entering_payment_NO_CLIENT = State()  
    kassa = State()  