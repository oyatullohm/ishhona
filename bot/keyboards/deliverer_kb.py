from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚚 Yetkazib Berish"),KeyboardButton(text="📦 Ombor Holati_")],
            [KeyboardButton(text="📋 clientga savdo")]

        ],
        resize_keyboard=True
    )

def client_selection_keyboard(clients):
    keyboard = []
    for client in clients:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{client.name} ({client.phone_number})",
                callback_data=f"select_client_{client.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def product_selection_keyboard(products):
    keyboard = []
    row = []
    for i, product in enumerate(products, start=1):
        row.append(InlineKeyboardButton(text=product.product_price.name, callback_data=f"select_product_{product.id}"))
        if i % 2 == 0:  # har 2 tadan qator
            keyboard.append(row)
            row = []
    if row:  # oxirgi qator qolsa
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="✅ Yakunlash", callback_data="finish_order_")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def button_valyuta():
    keyboard = [
        [
            InlineKeyboardButton(text="UZS", callback_data="UZS"),
            # InlineKeyboardButton(text="USD", callback_data="USD"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def orders_keyboard(orders):
    keyboard = []
    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                text=f"Buyurtma #{order.id} - {order.client.name}",
                callback_data=f"deliver_order_{order.id}"
            )
        ])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def confirm_delivery_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_delivery")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_delivery")]
    ])