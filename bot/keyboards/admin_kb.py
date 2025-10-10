from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from asgiref.sync import sync_to_async
from main.models import Currency
def admin_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Admin Bosh Menyu")],
            [KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="💰 Kassa Boshqarish")],
            [KeyboardButton(text="🤝 Mijozlar"), KeyboardButton(text="🤝 Taminotchilar")],
            [KeyboardButton(text="💸 Xarajatlar"), KeyboardButton(text="🏪 Mahsulotlar")],
            [ KeyboardButton(text="📂 Kategoriyalar"),KeyboardButton(text="📦 Buyurtmalar")],
            [ KeyboardButton(text="📦 Ombor _Holati_")]
        ],
        resize_keyboard=True
    )

def  product_menu():
     return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Aralashmagan Mahsulot"), KeyboardButton(text="🏪 Tayyor Mahsulot")],
            # [KeyboardButton(text="💸 Mahsulot Narhi"),KeyboardButton(text="🛒 Savdo")],
            [ KeyboardButton(text="🏠 Admin Bosh Menyu")],


        ],
        resize_keyboard=True
    )
def  product_():
     return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏪 Mahsulot"),KeyboardButton(text="➕ Yangi Tayyor Product Qoshish")],
            [ KeyboardButton(text="🏠 Admin Bosh Menyu")],
        ],
        resize_keyboard=True
    )

def product_price_inline_buttons(product_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💰 Sotilish narxini o‘zgartirish",
                callback_data=f"edit_price:{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="👷 Ish haqi (xarajat)ni o‘zgartirish",
                callback_data=f"edit_salary:{product_id}"
            )
        ]
    ])
    return keyboard

def not_mixid():
    return ReplyKeyboardMarkup(
        keyboard=[
             [KeyboardButton(text="🏠 Admin Bosh Menyu")],
            [KeyboardButton(text="➕ Aralashmagan Mahsulot kirim Qilish")],
            [KeyboardButton(text="➕ Aralashmagan Mahsulot Qoshish")],
            [KeyboardButton(text="📥 Aralashmagan Mahsulot Tarihi")],
           

          ],
        resize_keyboard=True
    )
def users_management_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛠️ Rollarni O'zgartirish"),KeyboardButton(text="🪖 Parollarni O'zhartirish")],
            # [KeyboardButton(text="✅ Faollashtirish"), KeyboardButton(text="❌ Bloklash")],
            [KeyboardButton(text="🏠 Admin Bosh Menyu")]
        ],
        resize_keyboard=True
    )

def roles_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👑 Admin", callback_data="role_admin"),
            InlineKeyboardButton(text="🚚 Yetkazib beruvchi", callback_data="role_deliverer")
        ],
        [
            InlineKeyboardButton(text="🔧 Ishchi", callback_data="role_worker"),
            InlineKeyboardButton(text="❌ Hechkim", callback_data="role_delete")
        ],
    ])

def kassa_management_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💵 Balans O'zgartirish"),KeyboardButton(text="💵 Kursni O'zgartirish")],
            [KeyboardButton(text="➖ Pul Berish"), KeyboardButton(text="➕ Pul olish")],
            [KeyboardButton(text="➖ Berilgan Pul"), KeyboardButton(text="➕ Olingan Pul")],
            [ KeyboardButton(text="💵⏩💴 kassadan kassaga"),KeyboardButton(text="💵 ⏩ Kassa")],
            [ KeyboardButton(text="➕ Yangi Kassa"),KeyboardButton(text="🏠 Admin Bosh Menyu")],
            [ KeyboardButton(text="➕ ➖  Client Va Taminotchi  Oldi berdi")],

        
        ],
        resize_keyboard=True
    )

def kassa_selection_keyboard(kassas):
    buttons = []
    for kassa in kassas:
        buttons.append([InlineKeyboardButton(
            text=f"{kassa.name} : {kassa.balance} {kassa.currency.code}",
            callback_data=f"kassa_{kassa.id}"
        )])
    # buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def client_menu(clients):
    buttons = []
    for cl in clients:
        buttons.append([
            InlineKeyboardButton(
                text=f"{cl.name} {cl.get_balance_str()}",
                callback_data=f"client-{cl.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def client_kassa_menu(client):
    buttons = []
    # Har bir balansini chiqaramiz
    for balance in client.balances.all():
        buttons.append([
            InlineKeyboardButton(
                text=f"{balance.amount} {balance.currency.code}",
                callback_data=f"clientkassa-{client.id}-{balance.currency.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def kassa_minus(kassas):
    buttons = []
    for kassa in kassas:
        buttons.append([InlineKeyboardButton(
            text=f"{kassa.name} : {kassa.balance} {kassa.currency.code}",
            callback_data=f"kassa-{kassa.id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def kassa_plus(kassas):
    buttons = []
    for kassa in kassas:
        buttons.append([InlineKeyboardButton(
            text=f"{kassa.name} : {kassa.balance} {kassa.currency.code}",
            callback_data=f"_kassa_plus-{kassa.id}"
        )])
    # buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def client_all(clients):
    buttons = []
    for client in clients:
        buttons.append([InlineKeyboardButton(
            text=f"{client.name} ",
            callback_data=f"client_all-{client.id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)



def clients_management_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Yangi Mijoz")],
            # [KeyboardButton(text="📊 Balanslar"), KeyboardButton(text="📈 Statistika")],
            [KeyboardButton(text="🏠 Admin Bosh Menyu")]
        ],
        resize_keyboard=True
    )
def supplier_management_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Yangi Mijoz")],
            # [KeyboardButton(text="📊 Balanslar"), KeyboardButton(text="📈 Statistika")],
            [KeyboardButton(text="🏠 Admin Bosh Menyu")]
        ],
        resize_keyboard=True
    )


def client_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤝 Mijoz", callback_data="client_type_customer"),
            InlineKeyboardButton(text="📦 Taminotchi", callback_data="client_type_supplier")
        ],
        # [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
    ])

def categories_management_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Yangi Kategoriya"),KeyboardButton(text="➕ Xarajat Qo'shish")],
            [KeyboardButton(text="Ishchiga pull berish"),KeyboardButton(text="🏠 Admin Bosh Menyu")]
        ],
        resize_keyboard=True
    )

def expenses_management_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Yangi Xarajat")],
            # [KeyboardButton(text="📅 Kunlik"), KeyboardButton(text="📆 Haftalik")],
            [KeyboardButton(text="🏠 Admin Bosh Menyu")]
        ],
        resize_keyboard=True
    )


    
def get_pagination_keyboard(page: int, has_next: bool):
    buttons = []
    if page > 1:
        buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"expenses_page:{page-1}")
        )
    if has_next:
        buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"expenses_page:{page+1}")
        )

    return InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None


async def currency_selection_keyboard():
    currencies = await sync_to_async(list)(Currency.objects.all())
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(currency), callback_data=f"currency_{currency.id}")]
            for currency in currencies
        ]
    )


def product_edit_kb(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✏️ Tahrirlash",
            callback_data=f"edit_product_notmixsid:{product_id}"
        )
    ]])
    return kb

def client_keyboard(client_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tanlash", callback_data=f"choose_client:{client_id}")]
    ])
    return kb

from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData

class ExpenseCategoryCB(CallbackData, prefix="exp_cat"):
    category_id: int
class ExpenseCategoryCB__(CallbackData, prefix="exp_cat__"):
    category_id: int

class ExpenseKassaCB(CallbackData, prefix="exp_kassa"):
    category_id: int
    kassa_id: int
class ExpenseKassaCB_(CallbackData, prefix="exp_kassa__"):
    category_id: int
    kassa_id: int
    

class AdminStates(StatesGroup):
    # Foydalanuvchi boshqarish
    waiting_user_id = State()
    waiting_user_role = State()
    client_taminotchi = State()
    
    
    new_cource = State()
    
    # Kassa boshqarish
    waiting_kassa_amount = State()
    waiting_kassa_minus = State()
    waiting_kassa_plus = State()

    waiting_kassa_currency = State()
    waiting_kassa_description = State()
    
    # Client boshqarish
    waiting_client = State()
    waiting_client_phone = State()
    waiting_client_name = State()
    waiting_client_type = State()
    waiting_client_address = State()
    waiting_client_telegram = State()
    waiting_client_balance_usd = State()
    waiting_client_balance_uzs = State()
    
    # Category boshqarish
    waiting_category_name = State()
    
    # Expense boshqarish
    waiting_expense_amount = State()
    waiting_expense_category = State()
    waiting_expense_description = State()
    
    # Product boshqarish
    waiting_product_name = State()
    waiting_component_quantity = State()
    
    # Order boshqarish
    waiting_order_client = State()
    waiting_order_products = State()

class PasswordState(StatesGroup):
    password = State()

class PasswordLoginState(StatesGroup):
    waiting_for_password = State()


class TransferMoneyState(StatesGroup):
    from_kassa = State()
    to_kassa = State()
    amount = State()

class ExpenseState(StatesGroup):
    waiting_for_amount = State()
    
class PaginationStates(StatesGroup):
    viewing_transactions = State()
    viewing_received_transactions = State() 
    viewing_received_income = State()

class KassaState(StatesGroup):
    waiting_for_name = State()
    waiting_for_initial_balance = State()
    waiting_for_currency = State()

class EditProductState(StatesGroup):
    waiting_for_price = State()
    waiting_for_quantity = State()

class IncomeState(StatesGroup):
    product = State()
    quantity = State()
    price = State()
    client= State()

class WorkerMoneyState(StatesGroup):
    worker_id = State()
    kassa = State()
    amount = State()
class ProductPriceState(StatesGroup):
    name = State()
    components = State()
    done = State()
    selling_price = State()
    salary = State()

class OrderPaginationStates(StatesGroup):
    viewing_orders = State()    

ITEMS_PER_PAGE = 5
