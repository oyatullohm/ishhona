from django.db.models.functions import TruncMonth
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from datetime import datetime, timedelta, date
from aiogram.fsm.context import FSMContext
from django.db.models import Q, Sum, Count
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from bot.keyboards.admin_kb import *
from bot.keyboards import admin_kb
from aiogram import Router, F
from decimal import Decimal
from main.models import *

router = Router()
# === ASOSIY MENYU ===
@router.message(F.text == "🏠 Admin Bosh Menyu")
async def admin_menu(message: Message, user, state: FSMContext):
    if not user.is_staff:
        await message.answer("Sizda admin panelga kirish huquqi yo'q")
        return

    # FSM ni tozalash
    await state.clear()

    await message.answer(
        text="Admin bosh menyu:",  # matnni kiritish shart
        reply_markup=admin_kb.admin_main_menu())

@router.message(F.text == "❌ Bekor qilish")
async def manage_users(message: Message,state: FSMContext, ):
    text = ("Admin bosh menyu:")
    await state.clear()
    await message.answer(text, reply_markup=admin_kb.admin_main_menu())
    # await .answer()
    
# === FOYDALANUVCHI BOSHQARISH ===
@router.message(F.text == "👥 Foydalanuvchilar")
async def manage_users(message: Message, user):
    if not user.is_staff:
        await message.answer(
        text="Sizda admin panelga krish hquqi yo'q")
        return
    
    users = await sync_to_async(list)(
    CustomUser.objects.filter(telegram_id__isnull=False)
)
    text = "👥 Foydalanuvchilar :\n\n"
    for u in users:
        balans = 0
        try:
            balans = await sync_to_async(Balans.objects.get)(user=u)
        except:
            pass
        roles = []
        if u.is_staff: roles.append("👑")
        if u.is_deliverer: roles.append("🚚")
        if u.is_worker: roles.append("🔧")
        
        text += f"{' '.join(roles)} {u.username}\n"
        text += f"ID: {u.telegram_id}\n"
        text += f"Status: {'✅' if u.is_active else '❌'}\n"
        text +=  f"Balans : {balans}\n" 
        text += "─" * 25 + "\n"
    
    await message.answer(text, reply_markup=admin_kb.users_management_menu())

@router.message(F.text == "🛠️ Rollarni O'zgartirish")
async def change_user_role(message: Message, state: FSMContext, user):
    if not user.is_staff:
        await message.answer(
        text="Sizda admin panelga krish hquqi yo'q")
        return
    
    await message.answer("Foydalanuvchi ID sini yuboring:")
    await state.set_state(AdminStates.waiting_user_id)


@router.message(AdminStates.waiting_user_id)
async def process_user_id(message: Message, state: FSMContext, user):
    try:
        user_id = int(message.text)
        target_user = await sync_to_async(CustomUser.objects.filter(telegram_id=user_id).first)()
        
        if not target_user:
            await message.answer("❌ Foydalanuvchi topilmadi")
            return
        
        await state.update_data(target_user_id=user_id)
        await message.answer(
            f"Foydalanuvchi: {target_user.username}\n"
            f"Joriy rollari:\n"
            f"• Admin: {'✅' if target_user.is_staff else '❌'}\n"
            f"• Yetkazib beruvchi: {'✅' if target_user.is_deliverer else '❌'}\n"
            f"• Ishchi: {'✅' if target_user.is_worker else '❌'}\n\n"
            f"Yangi rol tanlang:",
            reply_markup=admin_kb.roles_keyboard()
        )
        await state.set_state(AdminStates.waiting_user_role)
        
    except ValueError:
        await message.answer("❌ Iltimos, raqam kiriting")

@router.callback_query(AdminStates.waiting_user_role, F.data.startswith("role_"))
async def process_role_selection(callback: CallbackQuery, state: FSMContext, user):
    role = callback.data.split("_")[1]
    data = await state.get_data()
    target_user = await sync_to_async(CustomUser.objects.get)(telegram_id=data['target_user_id'])
    
    # Rollarni yangilash
    if role == "admin":
        target_user.is_staff = True
        target_user.is_deliverer = False
        target_user.is_worker = False
    elif role == "deliverer":
        target_user.is_staff = False
        target_user.is_deliverer = True
        target_user.is_worker = False
    elif role == "worker":
        target_user.is_staff = False
        target_user.is_deliverer = False
        target_user.is_worker = True
    elif role == "Hechkim":
        target_user.is_staff = False
        target_user.is_deliverer = False
        target_user.is_worker = False
        target_user.is_order = False
        target_user.is_active = False
        
        
    
    
    await sync_to_async(target_user.save)()
    
    role_name = {
        'admin': '👑 Admin', 'deliverer': '🚚 Yetkazib beruvchi',
        'worker': '🔧 Ishchi', 'Hechkim': '❌  Barcha hquqlari mahrum '
    }[role]
    
    await callback.message.answer(f"✅ {target_user.username} {role_name} bo'ldi")
    await state.clear()
    await callback.answer()


# === KASSA BOSHQARISH ===
@router.message(F.text == "➕ ➖  Client Va Taminotchi  Oldi berdi")
async def client_taminotchi_(message: Message, user):
    if not user.is_staff:
        await message.answer(
            text="Sizda admin panelga kirish huquqi yo'q"
        )
        return
    client = await sync_to_async(list)(Client.objects.prefetch_related('balances').all())
    await message.answer(
        "Qaysi hamkorni tanlaysiz?",
        reply_markup=admin_kb.client_all(client)
    )

@router.callback_query(F.data.startswith("client_all-"))
async def client_all_calbak(callback: CallbackQuery, state: FSMContext, user):
    client_id = int(callback.data.split("-")[1])
    client = await sync_to_async(lambda: Client.objects.prefetch_related("balances__currency").get(id=client_id))()

    
    await state.update_data(client_id=client_id)

    await callback.answer()
    await callback.message.answer(f"👤 {client.name} tanlandi.\n ")
    # data = await state.get_data()
    await state.update_data(page=1)
    # client = await sync_to_async(lambda: Client.objects.prefetch_related("balances__currency").get(id=data['client_id']))()
    kassatransaction = await sync_to_async(list)(KassaTransaction.objects.filter(related_client=client).select_related('kassa','related_client', 'currency', 'cource').all().order_by('-id'))
    total_pages = max(1, (len(kassatransaction) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    
    await state.update_data(transactions=kassatransaction, total_pages=total_pages, items_per_page=ITEMS_PER_PAGE)
    
    await show_transactions_page_client_all(callback.message, state)


async def show_transactions_page_client_all(message: Message, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    transactions = data.get('transactions', [])
    total_pages = data.get('total_pages', 1)
    items_per_page = data.get('items_per_page', 10)  # Default 10, lekin 5 bo'lishi mumkin
    
    # Sahifadagi elementlarni hisoblash
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(transactions))
    page_transactions = transactions[start_idx:end_idx]
    # Xabar matnini yaratish
    text = f"📋 Oldi Berdi (Sahifa {page}/{total_pages})\n\n"

    for i, transaction in enumerate(page_transactions, start=start_idx + 1):
        # Sana formatini o'zgaruvchi
        date_str = transaction.date.strftime('%Y-%m-%d %H:%M')
        
        # Null bo‘lsa xatolik bermasligi uchun
        client_name = transaction.related_client
        cource = transaction.cource
        kassa_name = transaction.kassa_name
        kassa_currency = transaction.kassa_currency_code
        client_currency = transaction.client_currency_code
        client_previous_balance =transaction.client_previous_balance
        client_new_balance = transaction.client_new_balance
        description = transaction.description or 'Izoh yo‘q'

        text += (
            f"{i}. 📅 Sana: {date_str}\n"
            f"   🔄 Tranzaksiya turi: {transaction.get_transaction_type_display()}\n"
            f"   👤 Client: {client_name}\n"
            f"   💰 Miqdor (Client valyutasi): {transaction.amount} {client_currency}\n"
            f"   💰 Miqdor (Kassa valyutasi): {transaction.amount_in_kassa_currency} {kassa_currency}\n"
            f"   💵 Pulni holati: {transaction.get_is_convert_display()}\n"
            f"   💱 Kurs: {cource}\n"
            f"   🏦 Kassa: {kassa_name}\n"
            f"   📊 Oldingi balans (Kassa): {transaction.previous_balance} {kassa_currency}\n"
            f"   📊 Yangi balans (Kassa): {transaction.new_balance} {kassa_currency}\n"
            f"   📊 Oldingi balans (Client): {client_previous_balance} {client_currency}\n"
            f"   📊 Yangi balans (client): {client_new_balance} {client_currency}\n"
            f"   📝 Izoh: {description}\n\n"
        )

    keyboard = []
    if total_pages > 1:
        row_buttons = []
        if page > 1:
            row_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"clientallprev_page_{page}"))
        if page < total_pages:
            row_buttons.append(InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"clientallnext_page_{page}"))
        
        if row_buttons:
            keyboard.append(row_buttons)
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(text, reply_markup=reply_markup)
    await state.set_state(PaginationStates.viewing_transactions)

# Callback handler paginatsiya uchun
@router.callback_query(F.data.startswith("clientallprev_page_") | F.data.startswith("clientallnext_page_"))
async def handle_pagination_client(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    
    if data.startswith("prev_page_"):
        current_page = int(data.split("_")[2])
        new_page = current_page - 1
    else:  # next_page_
        current_page = int(data.split("_")[2])
        new_page = current_page + 1
    
    await state.update_data(page=new_page)
    await callback.message.delete()  # Eski xabarni o'chirish
    await show_transactions_page_client_all(callback.message, state)
    await callback.answer()


@router.message(F.text == "💰 Kassa Boshqarish")
async def manage_kassa(message: Message, user):
    if not user.is_staff:
        await message.answer(
            text="Sizda admin panelga kirish huquqi yo'q"
        )
        return
    kassas = await sync_to_async(lambda: list(Kassa.objects.select_related("currency").all()))()
    
    text = "💰 Kassalar:\n\n"
    for kassa in kassas:
        text += f"🏦 {kassa.name}\n"
        text += f"💵 {kassa.balance} {kassa.currency.code}\n"
        text += "─" * 25 + "\n"
    
    await message.answer(text, reply_markup=admin_kb.kassa_management_menu())

@router.message(F.text == "➕ Yangi Kassa")
async def new_kassa(message:Message, state:FSMContext, user):
    if not user.is_staff:
        await message.answer(
        text="Sizda admin panelga krish hquqi yo'q")
        return
    await message.answer( "yangi kassa nomini kiritin masalan plastik humo "  )
    await state.set_state(KassaState.waiting_for_name)

@router.message(KassaState.waiting_for_name)
async def kass_name(message:Message, state:FSMContext):
    name = message.text
    await state.update_data(name=name)
    await message.answer("Boshlang'ich balansni kiriting (masalan: 0):")
    await state.set_state(KassaState.waiting_for_initial_balance)

@router.message(KassaState.waiting_for_initial_balance)
async def kass_balance(message: Message, state: FSMContext):
    try:
        balance = Decimal(message.text)
    except Exception:
        await message.answer("Faqat raqam kiriting ❗")
        return

    await state.update_data(balance=balance)

    keyboard = await admin_kb.currency_selection_keyboard()  # ✅ klaviaturani chaqiramiz

    await message.answer(
        "Kassaning valyutasini tanlang:",
        reply_markup=keyboard
    )
    await state.set_state(KassaState.waiting_for_currency)
    
@router.callback_query(KassaState.waiting_for_currency, F.data.startswith("currency_"))
async def kass_currency(callback:CallbackQuery, state:FSMContext):
    currency_code = callback.data.split("_")[1]
    currency = await sync_to_async(Currency.objects.get)(id=currency_code)  
    
    data = await state.get_data()
    name = data['name']
    balance = data['balance']
    

    kassa = await sync_to_async(Kassa.objects.create)(
        name=name,
        balance=balance,
        currency=currency
    )
    
    await callback.message.answer(f"✅ Yangi kassa yaratildi:\n🏦 Nomi {kassa.name}\n💵 {kassa.balance} {currency.code}")
    await state.clear()
    await callback.answer()

@router.message(F.text == "💵 Kursni O'zgartirish")
async def cource_(message:Message, state:FSMContext, user):
    if not user.is_staff:
        await message.answer(
        text="Sizda admin panelga krish hquqi yo'q")
        return
    cource = await sync_to_async(Cource.objects.last)()
    await message.answer(f"Songi kurs {cource}"  )
    await message.answer( "yangi kurs kirgizin 1 $ miqdori masalan 12500 "  )
    await state.set_state(AdminStates.new_cource)
    
@router.message(AdminStates.new_cource)
async def new_couece(message: Message, state: FSMContext, user):
    try:
        amount = Decimal(message.text)
        cource = await sync_to_async(
        lambda: Cource.objects.create(
           cource =amount
        )
        )()
        await message.answer( f"yangi kurs {cource}"  )
        await state.clear()
    except:
        await message.answer( f"kurs yaratishda hato"  )
        
   
@router.message(F.text == "💵 Balans O'zgartirish")
async def change_kassa_balance(message: Message, state: FSMContext, user):
    if not user.is_staff:
        await message.answer(
        text="Sizda admin panelga krish hquqi yo'q")
        return
    
    kassas = await sync_to_async(lambda: list(Kassa.objects.select_related("currency").all()))()
    
    await message.answer(
        "Qaysi kassani tanlaysiz?",
        reply_markup=admin_kb.kassa_selection_keyboard(kassas)
    )

@router.callback_query(F.data.startswith("kassa_"))
async def select_kassa(callback: CallbackQuery, state: FSMContext, user):
    
    kassa_id = int(callback.data.split("_")[1])
    kassa = await sync_to_async(lambda: Kassa.objects.select_related("currency").get(id=kassa_id))()
    
    await state.update_data(kassa_id=kassa_id)
    await callback.message.answer(
        f"🏦 {kassa.name}\n"
        f"Joriy balans: {kassa.balance} {kassa.currency.code}\n\n"
        f"Yangi miqdorni kiriting:",
    )
    await state.set_state(AdminStates.waiting_kassa_amount)
    await callback.answer()

@router.message(AdminStates.waiting_kassa_amount)
async def process_kassa_amount(message: Message, state: FSMContext, user):
    try:
        amount = Decimal(message.text)
        data = await state.get_data()
        kassa = await sync_to_async(lambda: Kassa.objects.select_related("currency").get(id=data['kassa_id']))()
        kassa.balance = amount
        await sync_to_async(kassa.save)()
        
        await message.answer(
            f"✅ Kassa yangilandi!\n"
            f"🏦 {kassa.name}\n"
            f"💵 Yangi balans: {kassa.balance} {kassa.currency.code}"
        )
        await state.clear()
        
    except (ValueError, Decimal.InvalidOperation):
        await message.answer("❌ Noto'g'ri miqdor")


@router.message(F.text == "➖ Pul Berish")
async def change_kassa_minus(message: Message, state: FSMContext, user):
    if not user.is_staff:
        await message.answer("Sizda admin panelga kirish huquqi yo'q")
        return

    kassas = await sync_to_async(lambda: list(Kassa.objects.select_related("currency").all()))()
    await message.answer(
        "Qaysi kassani tanlaysiz?",
        reply_markup=admin_kb.kassa_minus(kassas)
    )


# --- 2) KASSANI TANLASH ---
@router.callback_query(F.data.startswith("kassa-"))
async def kassaminus(callback: CallbackQuery, state: FSMContext, user):
    kassa_id = int(callback.data.split("-")[1])
    kassa = await sync_to_async(lambda: Kassa.objects.select_related("currency").get(id=kassa_id))()

    await state.update_data(kassa_id=kassa_id)

    clients = await sync_to_async(lambda: list(Client.objects.prefetch_related("balances__currency").filter(client_type='supplier')))()

    # klient tanlash menyusi
    buttons = []
    for cl in clients:
        buttons.append([InlineKeyboardButton(
            text=f"{cl.name} | {cl.get_balance_str()}",
            callback_data=f"client-{cl.id}"
        )])

    await callback.message.answer(
        f"🏦 {kassa.name} ({kassa.currency.code}) kassasi tanlandi.\n\n"
        "Endi klientni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# --- 3) KLIENTNI TANLASH ---
@router.callback_query(F.data.startswith("client-"))
async def select_client(callback: CallbackQuery, state: FSMContext, user):
    client_id = int(callback.data.split("-")[1])
    client = await sync_to_async(lambda: Client.objects.prefetch_related("balances__currency").get(id=client_id))()

    await state.update_data(client_id=client_id)

    # klient kassalari (balans valyutalari)
    buttons = []
    for balance in client.balances.all():
        buttons.append([InlineKeyboardButton(
            text=f"{balance.amount} {balance.currency.code}",
            callback_data=f"clientkassa-{balance.currency.id}"
        )])

    await callback.message.answer(
        f"👤 {client.name} tanlandi.\n"
        "Endi klient kassasini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# --- 4) KLIENT KASSASINI TANLASH ---
@router.callback_query(F.data.startswith("clientkassa-"))
async def select_client_kassa(callback: CallbackQuery, state: FSMContext, user):
    currency_id = int(callback.data.split("-")[1])
    await state.update_data(currency_id=currency_id)

    await callback.message.answer(
        "Yangi miqdorni kiriting:",

    )
    await state.set_state(AdminStates.waiting_kassa_minus)
    await callback.answer()


# --- 5) SUMMA KIRITISH VA TRANSACTION YOZISH ---
@router.message(AdminStates.waiting_kassa_minus)
async def process_kassa_amount(message: Message, state: FSMContext, user):
    try:
        amount = Decimal(message.text)
        data = await state.get_data()

        kassa = await sync_to_async(lambda: Kassa.objects.select_related("currency").get(id=data["kassa_id"]))()
        client = await sync_to_async(lambda: Client.objects.get(id=data["client_id"]))()
        cource = await sync_to_async(Cource.objects.last)()

        client_currency = await sync_to_async(lambda: Currency.objects.get(id=data["currency_id"]))()

        original_amount = amount
        amount_in_kassa_currency = amount

        # 🔄 Konvertatsiya
        if kassa.currency != client_currency:
            if kassa.currency.code == "UZS" and client_currency.code == "USD":
                client_amount = original_amount / cource.cource
                amount_in_kassa_currency = original_amount
                amount = client_amount
            elif kassa.currency.code == "USD" and client_currency.code == "UZS":
                client_amount = original_amount * cource.cource
                amount_in_kassa_currency = original_amount
                amount = client_amount
        else:
            amount_in_kassa_currency = original_amount
            amount = original_amount

        # ✅ ClientBalance ni olish yoki yaratish
        client_balance, created = await sync_to_async(lambda: ClientBalance.objects.get_or_create(
            client=client,
            currency=client_currency,
            defaults={'amount': Decimal(0)}
        ))()

        client_previous_balance = client_balance.amount
        
        # 🔧 ASOSIY MANTIQ: Siz clientga pul berayotganda → client balansi OSHADI
        client_new_balance = client_previous_balance - amount

        # ✅ Transaction yaratish
        is_convert = kassa.currency != client_currency
        transaction = await sync_to_async(KassaTransaction.objects.create)(
            kassa=kassa,
            transaction_type="expense",
            related_client=client,
            amount=amount,
            amount_in_kassa_currency=amount_in_kassa_currency,
            currency=client_currency,
            cource=cource,
            is_convert=is_convert,
            description=f"{client.name} ga pul berildi",
            previous_balance=kassa.balance,
            new_balance=kassa.balance - amount_in_kassa_currency,
            client_previous_balance=client_previous_balance,
            client_new_balance=client_new_balance,
            
        )

        # ✅ Balanslarni yangilash
        kassa.balance = transaction.new_balance
        await sync_to_async(kassa.save)()

        client_balance.amount = client_new_balance
        await sync_to_async(client_balance.save)()

        # 🔧 BALANS HOLATINI TUSHUNTIRISH
        # if client_new_balance  0:
        #     balance_status = f"💰 {client.name} sizdan qarzda: +{client_new_balance} {client_currency.code}"
        if client_new_balance < 0:
            balance_status = f"💳 Siz {client.name} ga qarzdorsiz: {client_new_balance} {client_currency.code}"
        else:
            balance_status = f"✅ Hisob-kitob teng (0)"

        await message.answer(
            f"✅ Pul muvaffaqiyatli berildi!\n"
            f"📦 Berildi: {original_amount} {kassa.currency.code}\n"
            f"👤 Client hisobiga: {amount:.2f} {client_currency.code}\n"
            f"{balance_status}"
        )


        await message.answer(
            text=f"✅ {client.name} ga {amount} {client_currency.code} berildi.\n"
                f"Kassadan chiqdi: {amount_in_kassa_currency} {kassa.currency.code}\n"
                f"Kassa yangi balansi: {kassa.balance} {kassa.currency.code}\n\n"
                f"👤 Client balansi: {client_previous_balance} → {client_new_balance} {client_currency.code}"
        )
        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

# --- 1) PUL OLISH BOSHLASH ---
@router.message(F.text == "➕ Pul olish")
async def change_kassa_plus(message: Message, state: FSMContext, user):
    if not user.is_staff:
        await message.answer("Sizda admin panelga kirish huquqi yo'q")
        return

    kassas = await sync_to_async(lambda: list(Kassa.objects.select_related("currency").all()))()
    await message.answer(
        "Qaysi kassani tanlaysiz?",
        reply_markup=admin_kb.kassa_plus(kassas)  # ➕ tugma uchun maxsus klaviatura
    )


# --- 2) KASSANI TANLASH ---
@router.callback_query(F.data.startswith("_kassa_plus-"))
async def kassa_plus_select(callback: CallbackQuery, state: FSMContext, user):
    kassa_id = int(callback.data.split("-")[1])
    kassa = await sync_to_async(lambda: Kassa.objects.select_related("currency").get(id=kassa_id))()

    await state.update_data(kassa_id=kassa_id)

    clients = await sync_to_async(lambda: list(Client.objects.prefetch_related("balances__currency").filter(client_type='customer')))()

    # klient tanlash menyusi
    buttons = []
    for cl in clients:
        buttons.append([InlineKeyboardButton(
            text=f"{cl.name} | {cl.get_balance_str()}",
            callback_data=f"client_plus-{cl.id}"
        )])

    await callback.message.answer(
        f"🏦 {kassa.name} ({kassa.currency.code}) kassasi tanlandi.\n\n"
        "Endi klientni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# --- 3) KLIENTNI TANLASH ---
@router.callback_query(F.data.startswith("client_plus-"))
async def select_client_plus(callback: CallbackQuery, state: FSMContext, user):
    client_id = int(callback.data.split("-")[1])
    client = await sync_to_async(lambda: Client.objects.prefetch_related("balances__currency").get(id=client_id))()

    await state.update_data(client_id=client_id)

    # klient kassalari (balans valyutalari)
    buttons = []
    for balance in client.balances.all():
        buttons.append([InlineKeyboardButton(
            text=f"{balance.amount} {balance.currency.code}",
            callback_data=f"clientkassa_plus-{balance.currency.id}"
        )])

    await callback.message.answer(
        f"👤 {client.name} tanlandi.\n"
        "Endi klient kassasini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# --- 4) KLIENT KASSASINI TANLASH ---
@router.callback_query(F.data.startswith("clientkassa_plus-"))
async def select_client_kassa_plus(callback: CallbackQuery, state: FSMContext, user):
    currency_id = int(callback.data.split("-")[1])
    await state.update_data(currency_id=currency_id)

    await callback.message.answer(
        "Kassaga qo‘shiladigan miqdorni kiriting:",
    
    )
    await state.set_state(AdminStates.waiting_kassa_plus)
    await callback.answer()


# --- 5) SUMMA KIRITISH VA TRANSACTION YOZISH ---
@router.message(AdminStates.waiting_kassa_plus)
async def process_kassa_plus(message: Message, state: FSMContext, user):
    try:
        amount = Decimal(message.text)
        data = await state.get_data()

        kassa = await sync_to_async(lambda: Kassa.objects.select_related("currency").get(id=data["kassa_id"]))()
        client = await sync_to_async(lambda: Client.objects.get(id=data["client_id"]))()
        cource = await sync_to_async(Cource.objects.last)()
        
        # Client valyutasini olish
        client_currency = await sync_to_async(lambda: Currency.objects.get(id=data["currency_id"]))()
        
        original_amount = amount
        amount_in_kassa_currency = amount

        # Konvertatsiya (agar valyutalar turlicha bo'lsa)
        if kassa.currency != client_currency:
            if kassa.currency.code == "UZS" and client_currency.code == "USD":
                # Client USD beradi, kassaga UZS tushadi
                client_amount = original_amount
                amount_in_kassa_currency = original_amount * cource.cource  # UZS qo'shiladi
                amount = client_amount
            elif kassa.currency.code == "USD" and client_currency.code == "UZS":
                # Client UZS beradi, kassaga USD tushadi
                client_amount = original_amount
                amount_in_kassa_currency = original_amount / cource.cource  # USD qo'shiladi
                amount = client_amount
        else:
            amount_in_kassa_currency = original_amount
            amount = original_amount

        # ✅ ClientBalance ni olish yoki yaratish
        client_balance, created = await sync_to_async(lambda: ClientBalance.objects.get_or_create(
            client=client,
            currency=client_currency,
            defaults={'amount': Decimal(0)}
        ))()

        client_previous_balance = client_balance.amount
        
        # 🔧 ASOSIY TO'G'RILASH: Clientdan pul olayotganda → client balansi KAMAYADI
        client_new_balance = client_previous_balance - amount

        # ✅ Transaction yaratish (income)
        is_convert = kassa.currency != client_currency
        transaction = await sync_to_async(KassaTransaction.objects.create)(
            kassa=kassa,
            transaction_type="income",
            amount=amount,  # client valyutasi
            related_client=client,
            amount_in_kassa_currency=amount_in_kassa_currency,  # kassaga tushadigan valyuta
            currency=client_currency,
            is_convert=is_convert,
            cource=cource,
            description=f"{client.name} dan pul olindi",
            previous_balance=kassa.balance,
            new_balance=kassa.balance + amount_in_kassa_currency,
            client_previous_balance=client_previous_balance,
            client_new_balance=client_new_balance  # ✅ Yangi qator
        )

        # ✅ Kassani yangilash
        kassa.balance = transaction.new_balance
        await sync_to_async(kassa.save)()

        # ✅ Client balansini yangilash
        client_balance.amount = client_new_balance
        await sync_to_async(client_balance.save)()

        # 🔧 BALANS HOLATINI TUSHUNTIRISH
        if client_new_balance > 0:
            balance_status = f"💰 {client.name} sizdan qarzda: +{client_new_balance} {client_currency.code}"
        elif client_new_balance < 0:
            balance_status = f"💳 Siz {client.name} ga qarzdorsiz: {client_new_balance} {client_currency.code}"
        else:
            balance_status = f"✅ Hisob-kitob teng (0)"

        await message.answer(
            f"✅ {client.name} dan pul olindi!\n"
            f"📦 Olingan: {original_amount} {client_currency.code}\n"
            f"💰 Kassaga qo'shildi: {amount_in_kassa_currency:.2f} {kassa.currency.code}\n"
            f"🏦 Kassa yangi balansi: {kassa.balance:.2f} {kassa.currency.code}\n"
            f"{balance_status}"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
# # === CLIENT BOSHQARISH ===pu
@router.message(F.text == "🤝 Mijozlar")
async def manage_clients(message: Message, user):
    if not user.is_staff:
        await message.answer(
        text="Sizda admin panelga krish hquqi yo'q")
        return
    
    clients = await sync_to_async(list)(Client.objects.filter(client_type='customer'))
    
    text = "🤝 Mijozlar :\n\n"
    for client in clients:
        text += f"👤 {client.name}\n"
        text += f"📞 {client.phone_number}\n"
        
        # Balanslarni valyuta bo'yicha ajratib olish
        balances = await sync_to_async(lambda: list(client.balances.select_related('currency').all()))()
        if balances:
            balance_text = ""
            for b in balances:
                balance_text += f"{b.amount} {b.currency.code} "
            text += f"💵 Balans: {balance_text}\n"
        else:
            text += "💵 Balans: 0\n"
        
        text += f"🔰 Turi: {client.get_client_type_display()}\n"
        text += "─" * 35 + "\n"

        
    await message.answer(text, reply_markup=admin_kb.clients_management_menu())

@router.message(F.text == "🤝 Taminotchilar")
async def supplier_all(message: Message, user):
    if not user.is_staff:
        await message.answer(
        text="Sizda admin panelga krish hquqi yo'q")
        return
    
    clients = await sync_to_async(list)(Client.objects.filter(client_type='supplier'))
    
    text = "🤝 Taminotchilar :\n\n"
    for client in clients:
        text += f"👤 {client.name}\n"
        text += f"📞 {client.phone_number}\n"
        
        # Balanslarni valyuta bo'yicha ajratib olish
        balances = await sync_to_async(lambda: list(client.balances.select_related('currency').all()))()
        if balances:
            balance_text = ""
            for b in balances:
                balance_text += f"{b.amount} {b.currency.code} "
            text += f"💵 Balans: {balance_text}\n"
        else:
            text += "💵 Balans: 0\n"
        
        text += f"🔰 Turi: {client.get_client_type_display()}\n"
        text += "─" * 35 + "\n"

        
    await message.answer(text, reply_markup=admin_kb.supplier_management_menu())


# --- 1) Telefon raqam
@router.message(F.text == "➕ Yangi Mijoz")
async def add_new_client(message: Message, state: FSMContext, user):
    if not user.is_staff:
        await message.answer(
        text="Sizda admin panelga krish hquqi yo'q")
        return
    
    await message.answer("📞 Mijozning telefon raqamini kiriting:")
    await state.set_state(AdminStates.waiting_client_phone)


# --- 2) Ism
@router.message(AdminStates.waiting_client_phone)
async def process_client_phone(message: Message, state: FSMContext, user):
    phone = message.text
    await state.update_data(phone=phone)
    await message.answer("👤 Mijozning ismini kiriting:")
    await state.set_state(AdminStates.waiting_client_name)


# --- 3) Manzil
@router.message(AdminStates.waiting_client_name)
async def process_client_name(message: Message, state: FSMContext, user):
    name = message.text
    await state.update_data(name=name)
    await message.answer("🏠 Mijozning manzilini kiriting (bo'sh qoldirsangiz ham bo‘ladi):")
    await state.set_state(AdminStates.waiting_client_address)


# --- 4) Telegram ID
@router.message(AdminStates.waiting_client_address)
async def process_client_address(message: Message, state: FSMContext, user):
    address = message.text
    await state.update_data(address=address)
    await message.answer("📲 Mijozning Telegram ID raqamini kiriting (agar yo‘q bo‘lsa 0 yozing):")
    await state.set_state(AdminStates.waiting_client_telegram)


# --- 5) Client turi
@router.message(AdminStates.waiting_client_telegram)
async def process_client_telegram(message: Message, state: FSMContext, user):
    telegram_id = int(message.text) if message.text.isdigit() else None
    await state.update_data(telegram_id=telegram_id)
    await message.answer(
        "🔰 Mijoz turini tanlang:",
        reply_markup=admin_kb.client_type_keyboard()
    )
    await state.set_state(AdminStates.waiting_client_type)


# --- 6) Boshlang‘ich balans (UZS)
@router.callback_query(AdminStates.waiting_client_type, F.data.startswith("client_type_"))
async def process_client_type(callback: CallbackQuery, state: FSMContext, user):
    client_type = callback.data.split("_")[2]
    await state.update_data(client_type=client_type)
    await callback.message.answer("💵 Boshlang‘ich balansni UZS da kiriting (masalan: 0):")
    await state.set_state(AdminStates.waiting_client_balance_uzs)
    await callback.answer()


# --- 7) Boshlang‘ich balans (USD)
@router.message(AdminStates.waiting_client_balance_uzs)
async def process_client_balance_uzs(message: Message, state: FSMContext, user):
    try:
        balance_uzs = Decimal(message.text)
    except:
        await message.answer("❌ Iltimos faqat son kiriting!")
        return

    await state.update_data(balance_uzs=balance_uzs)
    await message.answer("💵 Boshlang‘ich balansni USD da kiriting (masalan: 0):")
    await state.set_state(AdminStates.waiting_client_balance_usd)


# --- 8) Client va balanslarni yaratish
@router.message(AdminStates.waiting_client_balance_usd)
async def process_client_balance_usd(message: Message, state: FSMContext, user):
    try:
        balance_usd = Decimal(message.text)
    except:
        await message.answer("❌ Iltimos faqat son kiriting!")
        return

    await state.update_data(balance_usd=balance_usd)
    data = await state.get_data()

    # Client yaratish
    client = await sync_to_async(Client.objects.create)(
        telegram_id=data.get("telegram_id"),
        name=data["name"],
        phone_number=data["phone"],
        address=data.get("address"),
        client_type=data["client_type"]
    )

    # Balanslar yaratish
    uzs_currency = await sync_to_async(Currency.objects.get)(code="UZS")
    usd_currency = await sync_to_async(Currency.objects.get)(code="USD")

    await sync_to_async(ClientBalance.objects.create)(
        client=client, currency=uzs_currency, amount=data["balance_uzs"]
    )
    await sync_to_async(ClientBalance.objects.create)(
        client=client, currency=usd_currency, amount=data["balance_usd"]
    )

    await message.answer(
        f"✅ Yangi mijoz qo'shildi:\n\n"
        f"👤 {client.name}\n"
        f"📞 {client.phone_number}\n"
        f"🏠 {client.address or '-'}\n"
        f"📲 Telegram ID: {client.telegram_id or '-'}\n"
        f"🔰 Turi: {client.get_client_type_display()}\n"
        f"💵 Balans: {data['balance_uzs']} UZS | {data['balance_usd']} USD"
    )

    await state.clear()


@router.message(F.text == "📂 Kategoriyalar")
async def manage_categories(message: Message, user):
    if not user.is_staff:
        await message.answer("Sizda admin panelga kirish huquqi yo'q")
        return
    
    categories = await sync_to_async(list)(Category.objects.all())
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    current_month_start = today.replace(day=1)
    five_months_ago = (current_month_start - timedelta(days=150)).replace(day=1)
    
    text = "📊 Xarajatlar statistikasi:\n\n"
    for category in categories:
        today_sum = await sync_to_async(
            lambda: category.costs.filter(date=today).aggregate(Sum("amount"))["amount__sum"] or 0
        )()
        yesterday_sum = await sync_to_async(
            lambda: category.costs.filter(date=yesterday).aggregate(Sum("amount"))["amount__sum"] or 0
        )()
        week_sum = await sync_to_async(
            lambda: category.costs.filter(date__gte=week_ago).aggregate(Sum("amount"))["amount__sum"] or 0
        )()
        month_sum = await sync_to_async(
            lambda: category.costs.filter(date__gte=current_month_start).aggregate(Sum("amount"))["amount__sum"] or 0
        )()

        # So‘nggi 5 oy bo‘yicha alohida summalar
        last_5_months = await sync_to_async(
            lambda: list(
                category.costs.filter(date__gte=five_months_ago)
                    .annotate(month=TruncMonth("date"))
                    .values("month")
                    .annotate(total=Sum("amount"))
                    .order_by("month")
            )
        )()

        text += (
            f"📂 {category.name}\n"
            f"   📅 Bugun: {today_sum}\n"
            f"   📅 Kecha: {yesterday_sum}\n"
            f"   📅 7 kun: {week_sum}\n"
            f"   📅 Joriy oy: {month_sum}\n"
        )
        for row in last_5_months:
            oy = row["month"].strftime("%B %Y") if row["month"] else "Nomaʼlum"
            summa = row["total"] or 0
            text += f"   📅 {oy}: {summa}\n"

        text += f"{'─'*30}\n\n"

    # Juda uzun bo‘lsa bo‘lib yuboramiz (Telegram limit ~4096)
    parts = [text[i:i+3500] for i in range(0, len(text), 3500)]
    for part in parts:
        await message.answer(part)

    await message.answer("✅ Kategoriyalar statistikasi tugadi", reply_markup=admin_kb.categories_management_menu())

# # === CATEGORY BOSHQARISH ===
@router.message(F.text == "➕ Yangi Kategoriya")
async def add_new_category(message: Message, state: FSMContext, user):
    if not user.is_staff:
        await message.answer(
        text="Sizda admin panelga krish hquqi yo'q")
        return
    
    await message.answer("Yangi kategoriya nomini kiriting:")
    await state.set_state(AdminStates.waiting_category_name)

@router.message(AdminStates.waiting_category_name)
async def process_category_name(message: Message, state: FSMContext, user):
    name = message.text
    category = await sync_to_async(Category.objects.create)(name=name)
    await message.answer(f"✅ Yangi kategoriya qo'shildi: {category.name}")
    await state.clear()

# Paginatsiya uchun state


@router.message(F.text == "➖ Berilgan Pul")
async def money_given(message: Message, user, state: FSMContext):
    await state.update_data(page=1)
    
    transactions = await sync_to_async(list)(
        KassaTransaction.objects.select_related('kassa', 'currency', 'cource', 'related_client')
        .filter(transaction_type='expense')
        .order_by('-id')
    )
    # 5 talik paginatsiya uchun
    total_pages = max(1, (len(transactions) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    
    await state.update_data(transactions=transactions, total_pages=total_pages, items_per_page=ITEMS_PER_PAGE)
    
    await show_transactions_page(message, state)


async def show_transactions_page(message: Message, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    transactions = data.get('transactions', [])
    total_pages = data.get('total_pages', 1)
    items_per_page = data.get('items_per_page', 10)  # Default 10, lekin 5 bo'lishi mumkin
    
    # Sahifadagi elementlarni hisoblash
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(transactions))
    page_transactions = transactions[start_idx:end_idx]
    # Xabar matnini yaratish
    text = f"📋 Berilgan Pul Ro'yxati (Sahifa {page}/{total_pages})\n\n"

    for i, transaction in enumerate(page_transactions, start=start_idx + 1):
        # Sana formatini o'zgaruvchi
        date_str = transaction.date.strftime('%Y-%m-%d %H:%M')
        
        # Null bo‘lsa xatolik bermasligi uchun
        client_name = transaction.related_client
        cource = transaction.cource
        kassa_name = transaction.kassa_name
        kassa_currency = transaction.kassa_currency_code
        client_currency = transaction.client_currency_code
        client_previous_balance =transaction.client_previous_balance
        client_new_balance = transaction.client_new_balance
        description = transaction.description or 'Izoh yo‘q'

        text += (
            f"{i}. 📅 Sana: {date_str}\n"
            f"   🔄 Tranzaksiya turi: {transaction.get_transaction_type_display()}\n"
            f"   👤 Client: {client_name}\n"
            f"   💰 Miqdor (Client valyutasi): {transaction.amount} {client_currency}\n"
            f"   💰 Miqdor (Kassa valyutasi): {transaction.amount_in_kassa_currency} {kassa_currency}\n"
            f"   💵 Pulni holati: {transaction.get_is_convert_display()}\n"
            f"   💱 Kurs: {cource}\n"
            f"   🏦 Kassa: {kassa_name}\n"
            f"   📊 Oldingi balans (Kassa): {transaction.previous_balance} {kassa_currency}\n"
            f"   📊 Yangi balans (Kassa): {transaction.new_balance} {kassa_currency}\n"
            f"   📊 Oldingi balans (Client): {client_previous_balance} {client_currency}\n"
            f"   📊 Yangi balans (client): {client_new_balance} {client_currency}\n"
            f"   📝 Izoh: {description}\n\n"
        )

    keyboard = []
    if total_pages > 1:
        row_buttons = []
        if page > 1:
            row_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"prev_page_{page}"))
        if page < total_pages:
            row_buttons.append(InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"next_page_{page}"))
        
        if row_buttons:
            keyboard.append(row_buttons)
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(text, reply_markup=reply_markup)
    await state.set_state(PaginationStates.viewing_transactions)

# Callback handler paginatsiya uchun
@router.callback_query(F.data.startswith("prev_page_") | F.data.startswith("next_page_"))
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    
    if data.startswith("prev_page_"):
        current_page = int(data.split("_")[2])
        new_page = current_page - 1
    else:  # next_page_
        current_page = int(data.split("_")[2])
        new_page = current_page + 1
    
    await state.update_data(page=new_page)
    await callback.message.delete()  # Eski xabarni o'chirish
    await show_transactions_page(callback.message, state)
    await callback.answer()

# Orqaga qaytish handleri
@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()  # Eski xabarni o'chirish
    
    
    await callback.message.answer("Asosiy menyu", reply_markup=admin_kb.admin_main_menu)
    await callback.answer()


# Olingan Pul uchun
@router.message(F.text == "➕ Olingan Pul")
async def money_received(message: Message, user, state: FSMContext):
    await state.update_data(page=1)
    
    # DBdan income yozuvlarini olish
    transactions = await sync_to_async(list)(
        KassaTransaction.objects.select_related('kassa', 'currency', 'cource', 'related_client')
        .filter(transaction_type='income')
        .order_by('-date')
    )
    # 5 talik paginatsiya
    total_pages = max(1, (len(transactions) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    
    await state.update_data(
        transactions=transactions,
        total_pages=total_pages,
        items_per_page=ITEMS_PER_PAGE
    )
    
    await show_transactions_page_received(message, state)


async def show_transactions_page_received(message: Message, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    transactions = data.get('transactions', [])
    total_pages = data.get('total_pages', 1)
    items_per_page = data.get('items_per_page', 10)  # default 10, lekin 5 ham bo‘lishi mumkin
    
    # Sahifadagi elementlarni hisoblash
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(transactions))
    page_transactions = transactions[start_idx:end_idx]
    
    # Xabar matnini yaratish
    text = f"📋 Olingan Pul Ro'yxati (Sahifa {page}/{total_pages})\n\n"

    for i, transaction in enumerate(page_transactions, start=start_idx + 1):
        date_str = transaction.date.strftime('%Y-%m-%d %H:%M')

        client_name = transaction.related_client
        cource = transaction.cource
        kassa_name = transaction.kassa_name
        kassa_currency = transaction.kassa_currency_code
        client_currency = transaction.client_currency_code
        client_previous_balance =transaction.client_previous_balance
        client_new_balance = transaction.client_new_balance
        description = transaction.description or 'Izoh yo‘q'

        text += (
            f"{i}. 📅 Sana: {date_str}\n"
            f"   🔄 Tranzaksiya turi: {transaction.get_transaction_type_display()}\n"
            f"   👤 Client: {client_name}\n"
            f"   💰 Miqdor (Client valyutasi): {transaction.amount} {client_currency}\n"
            f"   💰 Miqdor (Kassa valyutasi): {transaction.amount_in_kassa_currency} {kassa_currency}\n"
            f"   💵 Pulni holati: {transaction.get_is_convert_display()}\n"
            f"   💱 Kurs: {cource}\n"
            f"   🏦 Kassa: {kassa_name}\n"
            f"   📊 Oldingi balans (Kassa): {transaction.previous_balance} {kassa_currency}\n"
            f"   📊 Yangi balans (Kassa): {transaction.new_balance} {kassa_currency}\n"
            f"   📊 Oldingi balans (Client): {client_previous_balance} {client_currency}\n"
            f"   📊 Yangi balans (client): {client_new_balance} {client_currency}\n"
            f"   📝 Izoh: {description}\n\n"
        )

    # Navigatsiya tugmalari
    keyboard = []
    if total_pages > 1:
        row_buttons = []
        if page > 1:
            row_buttons.append(
                InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"prev_page_{page}")
            )
        if page < total_pages:
            row_buttons.append(
                InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"next_page_{page}")
            )
        if row_buttons:
            keyboard.append(row_buttons)
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(text, reply_markup=reply_markup)
    await state.set_state(PaginationStates.viewing_received_transactions)


# Callback handler paginatsiya uchun
@router.callback_query(F.data.startswith("prev_page_") | F.data.startswith("next_page_"))
async def handle_pagination_received(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    
    if data.startswith("prev_page_"):
        current_page = int(data.split("_")[2])
        new_page = current_page - 1
    else:  # next_page_
        current_page = int(data.split("_")[2])
        new_page = current_page + 1
    
    await state.update_data(page=new_page)
    await callback.message.delete()  # eski xabarni o‘chirish
    await show_transactions_page_received(callback.message, state)
    await callback.answer()


# Orqaga qaytish handleri (umumiy)
@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    
    
    await callback.message.answer("Asosiy menyu", reply_markup=admin_kb.admin_main_menu)
    await callback.answer()



@router.message(F.text == "💸 Xarajatlar")
async def manage_expenses(message: Message, user):
    if not user.is_staff:
        await message.answer("❌ Sizda admin panelga kirish huquqi yo'q")
        return

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    # Statistikalar
    daily_expenses = await sync_to_async(
        lambda: Cost.objects.filter(date=today).aggregate(Sum('amount'))['amount__sum'] or 0
    )()
    yesterday_expenses = await sync_to_async(
        lambda: Cost.objects.filter(date=yesterday).aggregate(Sum('amount'))['amount__sum'] or 0
    )()
    weekly_expenses = await sync_to_async(
        lambda: Cost.objects.filter(date__gte=week_ago).aggregate(Sum('amount'))['amount__sum'] or 0
    )()

    five_months_ago = today.replace(day=1) - timedelta(days=150)
    monthly_data = await sync_to_async(list)(
        Cost.objects.filter(date__gte=five_months_ago)
        .values('date__year', 'date__month')
        .annotate(total=Sum('amount'))
        .order_by('-date__year', '-date__month')[:5]
    )

    text = f"""💸 Xarajatlar Statistika

    📅 Bugun: {daily_expenses} UZS
    📅 Kecha: {yesterday_expenses} UZS
    📅 So'nggi 7 kun: {weekly_expenses} UZS

    📅 So'nggi 5 oy:"""

    for m in monthly_data:
        oy = f"{m['date__month']:02d}-{m['date__year']}"
        text += f"\n   • {oy}: {m['total']} UZS"

    text += "\n\n📋 So'nggi 10 ta xarajat:"

    # 1-betni chiqaramiz
    expenses = await sync_to_async(list)(
        Cost.objects.select_related("category", "currency", "kassa",'user')
        .order_by('-id')[:10]
    )

    for expense in expenses:
        category = expense.category.name if expense.category else "❌ Kategoriya yo‘q"
        currency = expense.currency.code if hasattr(expense.currency, "code") else expense.currency
        # user = expense.user if user else "❌ User yo‘q"
        text += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            # f"👤 Ishchi: {user}\n"
            f"💵 Miqdor: {expense.amount} {currency}\n"
            f"📂 Kategoriya: {category}\n"
            f"📅 Sana: {expense.date}\n"
        )
    # Keyingi bet borligini tekshiramiz
    total_count = await sync_to_async(Cost.objects.count)()
    has_next = total_count > 10

    await message.answer(
        text,
        reply_markup=get_pagination_keyboard(page=1, has_next=has_next)
    )

# Callback – pagination
@router.callback_query(F.data.startswith("expenses_page:"))
async def paginate_expenses(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    per_page = 10
    offset = (page - 1) * per_page

    expenses = await sync_to_async(list)(
        Cost.objects.select_related("category", "currency", "kassa",'user')
        .order_by('-date')[offset:offset + per_page]
    )

    text = f"📋 Xarajatlar (bet {page}):"
    for expense in expenses:
        category = expense.category.name if expense.category else "Kategoriya yo'q"
        currency = expense.currency.code if hasattr(expense.currency, "code") else expense.currency
        # user = expense.user if user  else "❌ User yo‘q"
        text += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            # f"👤 Ishchi: {user}\n"
            f"💵 Miqdor: {expense.amount} {currency}\n"
            f"📂 Kategoriya: {category}\n"
            f"📅 Sana: {expense.date}\n"
        )
    total_count = await sync_to_async(Cost.objects.count)()
    has_next = total_count > offset + per_page

    await callback.message.edit_text(
        text,
        reply_markup=get_pagination_keyboard(page, has_next)
    )
    await callback.answer()


@router.message(F.text == "➕ Xarajat Qo'shish")
async def add_expense_start(message: Message, user):
    if not user.is_staff:
        await message.answer("❌ Sizda admin huquqi yo‘q")
        return

    categories = await sync_to_async(list)(Category.objects.all())
    if not categories:
        await message.answer("Kategoriya mavjud emas ❌")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c.name, callback_data=ExpenseCategoryCB(category_id=c.id).pack())]
        for c in categories
    ])

    await message.answer("📂 Kategoriya tanlang:", reply_markup=kb)


@router.callback_query(ExpenseCategoryCB.filter())
async def select_kassa(callback: CallbackQuery, callback_data: ExpenseCategoryCB):
    category_id = callback_data.category_id
    kassalar = await sync_to_async(list)(Kassa.objects.all())

    if not kassalar:
        await callback.message.edit_text("Kassa mavjud emas ❌")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{k.name} ({k.balance})",
            callback_data=ExpenseKassaCB(category_id=category_id, kassa_id=k.id).pack()
        )]
        for k in kassalar
    ])

    await callback.message.edit_text("🏦 Kassani tanlang:", reply_markup=kb)
    await callback.answer()


@router.callback_query(ExpenseKassaCB.filter())
async def ask_amount(callback: CallbackQuery, callback_data: ExpenseKassaCB, state: FSMContext):
    await state.update_data(category_id=callback_data.category_id, kassa_id=callback_data.kassa_id)
    await state.set_state(ExpenseState.waiting_for_amount)

    await callback.message.edit_text("💰 Xarajat miqdorini kiriting (masalan: `150000`):")
    await callback.answer()


@router.message(ExpenseState.waiting_for_amount)
async def save_expense(message: Message, state: FSMContext):
    try:
        amount = Decimal(message.text)
    except:
        await message.answer("❌ Miqdor noto‘g‘ri formatda, son kiriting.")
        return

    data = await state.get_data()
    category_id = data["category_id"]
    kassa_id = data["kassa_id"]

    category = await sync_to_async(Category.objects.get)(id=category_id)
    kassa = await sync_to_async(Kassa.objects.get)(id=kassa_id)
  
    # Cost yaratamiz
    cost = await sync_to_async(
        lambda: Cost.objects.create(
            category=category,
            kassa=kassa,
            amount=amount,
            currency=kassa.currency  # Kassaning valyutasi
        )
    )()

 

    await message.answer(
        f"✅ Xarajat qo‘shildi:\n\n"
        f"📂 Kategoriya: {category.name}\n"
        f"🏦 Kassa: {kassa.name}\n"
        f"💰 Miqdor: {amount} {kassa.currency}\n"
        f"📅 Sana: {cost.date}"
    )


@router.message(F.text == "🏪 Mahsulotlar")
async def product_mnue(message:Message):
    await message.answer("Asosiy menyu", reply_markup=admin_kb.product_menu())
    # await .answer()

@router.message(F.text == "➕ Aralashmagan Mahsulot Qoshish")
async def add_product(message: Message, state: FSMContext):
    await message.answer("📝 Mahsulot nomini kiriting:")
    await state.set_state("add_product_name")


@router.message(StateFilter("add_product_name"))
async def get_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("💰 Narxini kiriting (masalan: 12000.50):")
    await state.set_state("add_product_price")


@router.message(StateFilter("add_product_price"))
async def get_product_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text)
    except:
        await message.answer("❌ Noto‘g‘ri format! Raqam kiriting.")
        return
    await state.update_data(price=price)
    await message.answer("📦 Miqdorini kiriting (masalan: 10 yoki 5.5):")
    await state.set_state("add_product_quantity")


@router.message(StateFilter("add_product_quantity"))
async def get_product_quantity(message: Message, state: FSMContext):
    try:
        quantity = float(message.text)
    except:
        await message.answer("❌ Noto‘g‘ri format! Son kiriting.")
        return
    await state.update_data(quantity=quantity)
    await message.answer("⚖️ O‘lchov birligini tanlang:\n1. kg\n2. g\n3. pcs")
    await state.set_state("add_product_unit")


@router.message(StateFilter("add_product_unit"))
async def get_product_unit(message: Message, state: FSMContext):
    unit_map = {"1": "kg", "2": "g", "3": "pcs"}
    unit = unit_map.get(message.text.strip())
    if not unit:
        await message.answer("❌ Noto‘g‘ri tanlov! 1, 2 yoki 3 ni tanlang.")
        return
    await state.update_data(unit=unit)

    # Valyutani tanlash (masalan, Currency modelidan olish)
    currencies = await sync_to_async(list)(Currency.objects.all())
    text = "💵 Valyutani tanlang:\n"
    for idx, cur in enumerate(currencies, 1):
        text += f"{idx}. {cur.code}\n"
    await state.update_data(currencies=currencies)
    await message.answer(text)
    await state.set_state("add_product_currency")


@router.message(StateFilter("add_product_currency"))
async def get_product_currency(message: Message, state: FSMContext):
    data = await state.get_data()
    currencies = data["currencies"]
    try:
        idx = int(message.text.strip()) - 1
        currency = currencies[idx]
    except:
        await message.answer("❌ Xato! Raqamni to‘g‘ri tanlang.")
        return

    # Malumotlarni olish
    name = data["name"]
    price = data["price"]
    quantity = data["quantity"]
    unit = data["unit"]

    # Bazaga saqlash
    product = await sync_to_async(ProductNotMixed.objects.create)(
        name=name,
        price=price,
        quantity=quantity,
        unit=unit,
        currency=currency
    )

    await message.answer(
        f"✅ Mahsulot qo‘shildi!\n\n"
        f"📌 Nomi: {product.name}\n"
        f"💰 Narxi: {product.price} {currency.code}\n"
        f"📦 Miqdori: {product.quantity} {product.unit}"
    )
    await state.clear()


@router.message(F.text == "📦 Aralashmagan Mahsulot")
async def not_mixsid(message: Message, user):
    # SELECT ni sync threadda bajarib, natijani listga aylantiramiz
    products = await sync_to_async(list)(ProductNotMixed.objects.select_related("currency").all())

    if not products:
        await message.answer("📭 Aralashmagan mahsulotlar yo'q")
        await message.answer(
        text="Menyu" ,
        reply_markup=admin_kb.not_mixid())
        return

    for i, p in enumerate(products, start=1):
        text = (
            f"{i}. Nomi: {p.name}\n"
            f"   📦 Miqdori: {p.quantity} {p.get_unit_display()}\n"
            f"   💰 Narxi: {p.price} {p.currency.code}\n"
        )
        await message.answer(text, reply_markup=product_edit_kb(p.id))
    await message.answer(
        text="Menyu" ,
        reply_markup=admin_kb.not_mixid())
    
    
@router.callback_query(F.data.startswith("edit_product_notmixsid:"))
async def start_edit_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    await state.update_data(product_id=product_id)

    await callback.message.answer("✏️ Yangi narxni kiriting:")
    await state.set_state(EditProductState.waiting_for_price)

@router.message(EditProductState.waiting_for_price)
async def set_new_price(message: Message, state: FSMContext):
    try:
        new_price = float(message.text)
    except ValueError:
        await message.answer("❌ Narx noto‘g‘ri kiritildi. Raqam kiriting!")
        return

    await state.update_data(new_price=new_price)
    await message.answer("📊 Endi yangi miqdorni kiriting:")
    await state.set_state(EditProductState.waiting_for_quantity)

@router.message(EditProductState.waiting_for_quantity)
async def set_new_quantity(message: Message, state: FSMContext):
    try:
        new_quantity = float(message.text)
    except ValueError:
        await message.answer("❌ Miqdor noto‘g‘ri kiritildi. Raqam kiriting!")
        return

    data = await state.get_data()
    product_id = data["product_id"]
    new_price = data["new_price"]

    # DB yangilash
    await sync_to_async(ProductNotMixed.objects.filter(id=product_id).update)(
        price=new_price,
        quantity=new_quantity
    )

    await message.answer(f"✅ Mahsulot yangilandi!\n💰 Narx: {new_price}\n📊 Miqdor: {new_quantity}")
    await state.clear()

# 🔹 Kirim boshlash
# 🔹 Kirim boshlash
@router.message(F.text == "➕ Aralashmagan Mahsulot kirim Qilish")
async def choose_product(message: Message, state: FSMContext):
    products = await sync_to_async(list)(
        ProductNotMixed.objects.select_related("currency").all()
    )
    if not products:
        await message.answer("📭 Hali mahsulotlar mavjud emas")
        return

    text = "📦 Qaysi mahsulot uchun kirim qilamiz?\n➡️ Iltimos, mahsulot *ID* ni kiriting:\n\n"

    await message.answer(text)

    for i, p in enumerate(products, start=1):
        text = (
            f"🔹 <b>{i}-mahsulot</b>\n"
            f"🆔 ID: <b>{p.id}</b>\n"
            f"🏷️ Nomi: <b>{p.name}</b>\n"
            f"📊 Miqdori: <b>{p.quantity}</b> {p.get_unit_display()}\n"
            f"💰 Narxi: <b>{p.price}</b> {p.currency.code}\n"
        )
        await message.answer(text)

    await state.set_state(IncomeState.product)


# 🔹 Mahsulot tanlash
@router.message(IncomeState.product)
async def get_product(message: Message, state: FSMContext):
    try:
        product = await sync_to_async(ProductNotMixed.objects.get)(id=message.text)
    except ProductNotMixed.DoesNotExist:
        await message.answer("❌ Bunday mahsulot topilmadi, qaytadan tanlang")
        return

    await state.update_data(product_id=product.id)
    await message.answer(
        f"✅ {product.name} tanlandi.\n\n💵 To‘lov turini tanlang:",
        reply_markup=payment_type_keyboard()
    )
    await state.set_state(IncomeState.payment_type)

# 🔹 To‘lov turi tanlash (Naq yoki Supplier)
@router.callback_query(F.data.startswith("payment_type"))
async def get_payment_type(callback: CallbackQuery, state: FSMContext):
    payment_type = callback.data.split(":")[1]
    await state.update_data(payment_type=payment_type)

    if payment_type == "naq":
        kassalar = await sync_to_async(list)(Kassa.objects.all())
        if not kassalar:
            await callback.message.answer("❌ Hech qanday kassa mavjud emas")
            return

        await callback.message.answer("🏦 Qaysi kassadan pul to‘lanadi?", reply_markup=cash_keyboard(kassalar))
        await state.set_state(IncomeState.cash)

    elif payment_type == "supplier":
        clients = await sync_to_async(list)(Client.objects.filter(client_type='supplier'))
        if not clients:
            await callback.message.answer("❌ Supplier clientlar mavjud emas")
            return

        await callback.message.answer("👤 Supplier tanlang:")
        for i, c in enumerate(clients, start=1):
            text = f"🔹 <b>{i}-client</b>\n🆔 ID: {c.id}\n👤 Nomi: {c.name}\n"
            await callback.message.answer(text, reply_markup=client_keyboard(c.id))
        await state.set_state(IncomeState.client)


# 🔹 Client tanlash
@router.callback_query(F.data.startswith("choose_client"))
async def choose_client(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split(":")[1])
    client = await sync_to_async(Client.objects.get)(id=client_id)

    await state.update_data(client_id=client.id)
    await callback.message.answer(f"✅ Client tanlandi: {client.name}\nEndi miqdorini kiriting:")
    await state.set_state(IncomeState.quantity)


# 🔹 Kassa tanlash (Naq uchun)
@router.callback_query(F.data.startswith("choose_cash"))
async def choose_cash(callback: CallbackQuery, state: FSMContext):
    cash_id = int(callback.data.split(":")[1])
    kassa = await sync_to_async(Kassa.objects.get)(id=cash_id)
    await state.update_data(cash_id=kassa.id)
    await callback.message.answer(f"✅ {kassa.name} kassasi tanlandi.\nEndi miqdorini kiriting:")
    await state.set_state(IncomeState.quantity)


# 🔹 Miqdor kiritish
@router.message(IncomeState.quantity)
async def get_quantity(message: Message, state: FSMContext):
    try:
        quantity = float(message.text)
    except ValueError:
        await message.answer("❌ Miqdorni faqat raqamda kiriting!")
        return

    await state.update_data(quantity=quantity)
    await message.answer("💰 Endi narxini kiriting:")
    await state.set_state(IncomeState.price)


# 🔹 Narx kiritish va yakuniy saqlash
@router.message(IncomeState.price)
async def save_income(message: Message, state: FSMContext, user: CustomUser):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("❌ Narxni faqat raqamda kiriting!")
        return

    data = await state.get_data()
    product = await sync_to_async(ProductNotMixed.objects.get)(id=data["product_id"])
    payment_type = data.get("payment_type")
    currency_id = product.currency_id
    currency = await sync_to_async(Currency.objects.get)(id=currency_id)

    client = None
    if payment_type == "supplier":
        client = await sync_to_async(Client.objects.get)(id=data["client_id"])

    income = await sync_to_async(Income.objects.create)(
        component=product,
        quantity=data["quantity"],
        price=Decimal(price),
        currency_id=currency_id,
        user=user,
        client=client,
    )

    # 🔹 Product narxini yangilaymiz
    product.price = Decimal(price)
    await sync_to_async(product.save)()

    # 🔹 Agar naq bo‘lsa, kassadan pulni ayiramiz
    if payment_type == "naq":
        kassa = await sync_to_async(Kassa.objects.get)(id=data["cash_id"])
        minus_summ = Decimal(price) * Decimal(data["quantity"])
        kassa.balance -= minus_summ
        await sync_to_async(kassa.save)()
        await message.answer(f"🏦 {kassa.name} kassasidan {minus_summ} so‘m ayirildi 💸")

    await message.answer(
        f"✅ Income qo‘shildi!\n\n"
        f"📦 Mahsulot: {product.name}\n"
        f"🔢 Miqdor: {income.quantity} {product.get_unit_display()}\n"
        f"💰 Narx: {income.price} {currency}\n"
        f"📊 Jami: {income.total_sum} {currency}\n"
        f"👤 Client: {client if client else 'Naq (kassa orqali)'}\n"
        f"🏦 Kim kiritdi: {income.user}"
    )
    await state.clear()


@router.message(F.text == "📥 Aralashmagan Mahsulot Tarihi")
async def money_received(message: Message, user, state: FSMContext):
    await state.update_data(page=1)
    
    # DBdan income yozuvlarini olish
    income = await sync_to_async(list)(
        Income.objects.select_related('component', 'currency', 'user', 'client')
        .all().order_by('-date')
    )
    # 5 talik paginatsiya
    total_pages = max(1, (len(income) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    
    await state.update_data(
        income=income,
        total_pages=total_pages,
        items_per_page=ITEMS_PER_PAGE
    )
    
    await show_income_page_received(message, state)


async def show_income_page_received(message: Message, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    income = data.get('income', [])
    total_pages = data.get('total_pages', 1)
    items_per_page = data.get('items_per_page', 10)  # default 10, lekin 5 ham bo‘lishi mumkin
    
    # Sahifadagi elementlarni hisoblash
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(income))
    page_income = income[start_idx:end_idx]
    
    # Xabar matnini yaratish
    text = f"📋 Mahsulot (Sahifa {page}/{total_pages})\n\n"

    for i, income in enumerate(page_income, start=start_idx + 1):
        date_str = income.date.strftime('%Y-%m-%d')

        product = income.component.name
        moqdor = f"{income.quantity} {income.component.get_unit_display()}"
        price = f"{income.price} {income.currency.code}"
        user  = income.user.username if income.user else "Noma'lum"

        text += (
            f"{i}. 📅 Sana: {date_str}\n"
            f"   📦 Mahsulot: {product}\n"
            f"   🔢  Miqdor: {moqdor}\n"
            f"   💵 Narxi: {price}\n"
            f"   👤 Taminotchi: {income.client}\n"
            f"   💵 Kurs: {income.cource}\n"
            f"   🏦 User: {user}\n\n"
        )

    # Navigatsiya tugmalari
    keyboard = []
    if total_pages > 1:
        row_buttons = []
        if page > 1:
            row_buttons.append(
                InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"incomeprev_page_{page}")
            )
        if page < total_pages:
            row_buttons.append(
                InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"incomenext_page_{page}")
            )
        if row_buttons:
            keyboard.append(row_buttons)
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(text, reply_markup=reply_markup)
    await state.set_state(PaginationStates.viewing_received_income)


# Callback handler paginatsiya uchun
@router.callback_query(F.data.startswith("incomeprev_page_") | F.data.startswith("incomenext_page_"))
async def handle_pagination_incom(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    
    if data.startswith("incomeprev_page_"):
        current_page = int(data.split("_")[2])
        new_page = current_page - 1
    else:  # next_page_
        current_page = int(data.split("_")[2])
        new_page = current_page + 1
    
    await state.update_data(page=new_page)
    await callback.message.delete()  # eski xabarni o‘chirish
    await show_income_page_received(callback.message, state)
    await callback.answer()


# ➕ ProductPrice yaratishni boshlash
@router.message(F.text == "➕ Yangi Tayyor Product Qoshish")
async def start_product_price(message: Message, state: FSMContext):
    await message.answer("📝 Yangi  Product nomini kiriting:")
    await state.set_state(ProductPriceState.name)


# 🔹 Narx nomi kiritish
@router.message(ProductPriceState.name)
async def set_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text, components=[])
    products = await sync_to_async(list)(ProductNotMixed.objects.all().select_related('currency'))
    if not products:
        await message.answer("❌ Hali mahsulotlar mavjud emas.")
        await state.clear()
        return
    
    text = "📦 Qaysi komponentni qo‘shamiz? ID raqamini yuboring:\n\n"
    await message.answer(text)
    for p in products:
        text = f"🆔 {p.id} \n {p.name} \n{p.price} \n{p.currency}\n"
        await message.answer(text)
    await state.set_state(ProductPriceState.components)


@router.message(ProductPriceState.components)
async def add_component(message: Message, state: FSMContext):
    # ✅ Saqlash tugmasi bo‘lsa
    if message.text == "Saqlash":
        await save_product_price(message, state)
        return

    # ✅ ID kiritilgan bo‘lsa
    try:
        product = await sync_to_async(ProductNotMixed.objects.get)(id=int(message.text))
    except (ProductNotMixed.DoesNotExist, ValueError):
        await message.answer("❌ Noto‘g‘ri ID! Qaytadan to‘g‘ri ID kiriting:")
        return

    # ✅ Agar product topilgan bo‘lsa
    await state.update_data(current_product=product.id)
    await message.answer(f"🔢 {product.name} uchun miqdorni kiriting:")
    await state.set_state(ProductPriceState.done)


# 🔹 Miqdor kiritish
@router.message(ProductPriceState.done)
async def set_quantity(message: Message, state: FSMContext):
    try:
        quantity = float(message.text)
    except ValueError:
        await message.answer("❌ Miqdorni faqat raqamda kiriting.")
        return

    data = await state.get_data()
    components = data.get("components", [])
    product_id = data.get("current_product")

    components.append({"id": product_id, "quantity": quantity})
    await state.update_data(components=components, current_product=None)

    # Yana qo‘shishni so‘raymiz
    await message.answer(
        "✅ Qo‘shildi!\n\n"
        "👉 Yana komponent qo‘shish uchun ID yuboring.\n"
        "✅ Tugatish uchun 'Saqlash' deb yozing."
    )

    # ❗ Muhim: qaytadan components state ga qaytaramiz
    await state.set_state(ProductPriceState.components)

# 🔹 Tugatish va saqlash
@router.message(F.text == "Saqlash")
async def save_product_price(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    components = data.get("components")

    product_price = await sync_to_async(ProductPrice.objects.create)(
        name=name,
        components=components,
        selling_price=Decimal(0)  # Hozircha 0, save() ichida hisoblanadi
    )

    # save() da avtomatik hisoblanadi
    await sync_to_async(product_price.save)()

    await message.answer(
        f"✅ Yangi narx qo‘shildi!\n\n"
        f"📌 Nomi: {product_price.name}\n"
        f"💵 Narx UZS: {product_price.total_cost_uzs}\n"
        f"💵 Narx USD: {product_price.total_cost_usd}\n"
    )
    await state.clear()

@router.message(F.text == "🏪 Tayyor Mahsulot")
async def product_menu(message: Message, user):
    await message.answer(
        text="Tayyor Mahsulotlar Ro'yhati ", 
        reply_markup=product_())
    products = await sync_to_async(list)(Product.objects.all().select_related(
        'product_price'
    ))
    
    for p in products:
        text = (
            f"📦 Mahsulot: {p.product_price.name}\n\n"
            f"🆔 ID: {p.product_price.id}\n"
            f"💰 Sotilish narxi: {p.product_price.selling_price:,} so‘m\n"
            f"👷 Ishlab chiqarish xarajati (ish haqi): {p.product_price.salary:,} so‘m\n"
            f"💵 Dollardagi narh: {p.product_price.total_cost_usd:,} $\n"
            f"🇺🇿 So‘mdagi narh: {p.product_price.total_cost_uzs:,} so‘m\n\n"
            f"📊 Miqdor: {p.quantity}\n"
            f"🧾 Jami summa: {p.total_cost:,} so‘m\n"
            
        )
        await message.answer(text,reply_markup=product_price_inline_buttons(p.product_price.id)
)

@router.callback_query(F.data.startswith("edit_price"))
async def edit_price_(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    await state.update_data(product=product_id)
    await callback.message.delete()  # eski xabarni o‘chiramiz
    await callback.message.answer("✅ Product tanlandi.\n\n💰 Endi sotish narhini kiriting:")
    await state.set_state(ProductPriceState.selling_price)


# 📌 Sotilish narxi kiritish
@router.message(ProductPriceState.selling_price)
async def product_selling_price(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        selling_price = Decimal(message.text)
    except ValueError:
        await message.answer("❌ Narxni faqat raqamda kiriting!")
        return

    p = await sync_to_async(ProductPrice.objects.get)(id=data['product'])
    p.selling_price = selling_price
    await sync_to_async(p.save)()

    # Chiroyli chiqarish
    text = (
        f"📦 Mahsulot: {p.name}\n\n"
        f"🆔 ID: {p.id}\n"
        f"💰 Sotilish narxi: {int(p.selling_price):,} so‘m\n"
        f"👷 Ishlab chiqarish xarajati (ish haqi): {int(p.salary):,} so‘m\n"
        f"💵 Dollardagi narh: {p.total_cost_usd:,.2f} $\n"
        f"🇺🇿 So‘mdagi narh: {p.total_cost_uzs:,.2f} so‘m\n"
    )

    await message.answer(
        text,
        reply_markup=product_price_inline_buttons(p.id) 
    )
    
        

@router.callback_query(F.data.startswith("edit_salary"))
async def edit_salary_(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    await state.update_data(product=product_id)
    await callback.message.delete()  # eski xabarni o‘chiramiz
    await callback.message.answer("✅ Product tanlandi.\n\n💰 Endi ishchi narhini kiriting:")
    await state.set_state(ProductPriceState.salary)


# 📌 Sotilish narxi kiritish
@router.message(ProductPriceState.salary)
async def product_salary(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        salary = Decimal(message.text)
    except ValueError:
        await message.answer("❌ Narxni faqat raqamda kiriting!")
        return

    p = await sync_to_async(ProductPrice.objects.get)(id=data['product'])
    p.salary = salary
    await sync_to_async(p.save)()

    # Chiroyli chiqarish
    text = (
        f"📦 Mahsulot: {p.name}\n\n"
        f"🆔 ID: {p.id}\n"
        f"💰 Sotilish narxi: {int(p.selling_price):,} so‘m\n"
        f"👷 Ishlab chiqarish xarajati (ish haqi): {int(p.salary):,} so‘m\n"
        f"💵 Dollardagi narh: {p.total_cost_usd:,.2f} $\n"
        f"🇺🇿 So‘mdagi narh: {p.total_cost_uzs:,.2f} so‘m\n"
    )

    await message.answer(
        text,
        reply_markup=product_price_inline_buttons(p.id) 
    )

@router.message(F.text == "🪖 Parollarni O'zhartirish")
async def password(message: Message, user, state: FSMContext):
    if not user.is_staff :
        await message.answer("❌ Sizda bu bo‘limga kirish huquqi yo‘q")
        return

    await message.answer(
        "🔐 Parollarni o'zgartirish uchun quyidagi buyruqlarni ishlating:\n\n"
        "Masalan:\n"
        "admin parolni o'zgartirish:\n"
        "admin_password new_password\n"
        "worker parolni o'zgartirish:\n"
        "worker_password new_password\n"
        "driver parolni o'zgartirish:\n"
        "driver_password new_password\n"
        "start parolni o'zgartirish: \n"
        "start_password new_password\n"
        "savdo parolni o'zgartirish: \n"
        "savdo_password new_password\n"
        
        "Eslatma: Parolni o'zgartirish uchun yuqoridagi formatda yozing."
        
    )
    await state.set_state(PasswordState.password)
    
@router.message(PasswordState.password)
async def change_password(message: Message, state: FSMContext):
    text = message.text.split()

    if len(text) != 2:
        await message.answer("❌ Format noto‘g‘ri!\nMasalan: `admin_password 1234`")
        return

    name, password = text
    passv = await sync_to_async(BotSettings.objects.last)()

    if not passv:
        await message.answer("⚠️ Sozlamalar topilmadi.")
        return

    if name == 'admin_password':
        passv.admin_password = password  # yoki make_password(password)
    elif name == "worker_password":
        passv.worker_password = password
    elif name == "driver_password":
        passv.driver_password = password
    elif name == "start_password":
        passv.start_password = password
    elif name == "savdo_password":
        passv.order_password = password
    else:
        await message.answer("❌ Noto‘g‘ri buyruq!")
        return

    await sync_to_async(passv.save)()
    await message.answer(f"✅ {name} muvaffaqiyatli yangilandi!")
    await state.clear()


# 1. Admin worker tanlaydi
@router.message(F.text == "Ishchiga pull berish")
async def give_money_to_workers(message: Message, user, state: FSMContext):
    if not user.is_staff:
        await message.answer("❌ Sizda bu bo‘limga kirish huquqi yo‘q")
        return

    users = await sync_to_async(list)(
        CustomUser.objects.filter(balans__isnull=False).prefetch_related("balans")
    )
    if not users:
        await message.answer("❌ Hali ishchilar mavjud emas.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{u.username} ({u.balans.balans})",
                callback_data=f"__user__{u.id}"
            )]
            for u in users
        ]
    )
    await message.answer("Ishchini tanlang 👇", reply_markup=keyboard)


# 2. Worker tanlanganida
@router.callback_query(F.data.startswith("__user__"))
async def cost_user_id__(callback: CallbackQuery, state: FSMContext):
    worker_id = int(callback.data.split("_")[4])
    await state.update_data(user_id=worker_id)

    categories = await sync_to_async(list)(Category.objects.all())
    if not categories:
        await callback.message.answer("Kategoriya mavjud emas ❌")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c.name, callback_data=ExpenseCategoryCB__(category_id=c.id).pack())]
        for c in categories
    ])
    await callback.message.answer("📂 Kategoriya tanlanggg:", reply_markup=kb)
    await callback.answer()


# 3. Kategoriya tanlanganda
@router.callback_query(ExpenseCategoryCB__.filter())
async def select_kassa__(callback: CallbackQuery, callback_data: ExpenseCategoryCB__, state: FSMContext):
    category_id = callback_data.category_id
    await state.update_data(category_id=category_id)

    kassalar = await sync_to_async(list)(Kassa.objects.all())
    if not kassalar:
        await callback.message.edit_text("Kassa mavjud emas ❌")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{k.name} ({k.balance})",
            callback_data=ExpenseKassaCB_(category_id=category_id, kassa_id=k.id).pack()
        )]
        for k in kassalar
    ])

    await callback.message.edit_text("🏦 Kassani tanlanggg:", reply_markup=kb)
    await callback.answer()


# 4. Kassa tanlanganda
@router.callback_query(ExpenseKassaCB_.filter())
async def ask_amount__(callback: CallbackQuery, callback_data: ExpenseKassaCB_, state: FSMContext):
    await state.update_data(category_id=callback_data.category_id, kassa_id=callback_data.kassa_id)
    await state.set_state(WorkerMoneyState.amount)

    await callback.message.edit_text("💰 Xarajat miqdorini kiriting (masalan: `140000`):")
    await callback.answer()


# 5. Miqdorni yozganda
@router.message(WorkerMoneyState.amount)
async def save_expense__(message: Message, state: FSMContext):
    try:
        amount = Decimal(message.text)
    except:
        await message.answer("❌ Miqdor noto‘g‘ri formatda, son kiriting.")
        return

    data = await state.get_data()
    category_id = data["category_id"]
    kassa_id = data["kassa_id"]
    user_id = data['user_id']

    user = await sync_to_async(CustomUser.objects.get)(id=user_id)
    balans = await sync_to_async(Balans.objects.select_related('user').get)(user_id=user_id)
    category = await sync_to_async(Category.objects.get)(id=category_id)
    kassa = await sync_to_async(Kassa.objects.get)(id=kassa_id)

    # Cost yaratamiz
    cost = await sync_to_async(
        lambda: Cost.objects.create(
            category=category,
            kassa=kassa,
            amount=amount,
            currency=kassa.currency,
            user = user
        )
    )()

    # Ishchi balansidan ayiramiz
    balans.balans -= cost.amount
    await sync_to_async(balans.save)()
    await message.answer(
        f"✅ Xarajat qo‘shildi:\n\n"
        f"👷 Ishchi: {balans.user}\n"
        f"📂 Kategoriya: {category.name}\n"
        f"🏦 Kassa: {kassa.name}\n"
        f"💰 Miqdor: {amount} {kassa.currency}\n"
        f"📅 Sana: {cost.date}"
    )
    await state.clear()



@router.message(F.text == "📦 Ombor _Holati_")
async def product_all(message:Message, user):
    if not user:
        await message.answer("Sizda panelga kirish huquqi yo'q")
        return
    product = await sync_to_async(list)(Product.objects.select_related('product_price').all())
    for p in product:
        text = (
            f"📦 Nomi {p.product_price}\n"
            f"📊 Miqdori {p.quantity}"
        )
        await message.answer(text)



@router.message(F.text == "📦 Buyurtmalar")
async def order_all(message: Message, user, state: FSMContext):
    if not user:
        await message.answer("Sizda panelga kirish huquqi yo'q")
        return
    
    # Buyurtmalarni olish
    orders = await sync_to_async(list)(
        Order.objects.prefetch_related('items')
        .select_related('client','user', 'base_currency')
        .all()
        .order_by('-id')
    )
    
    if not orders:
        await message.answer("Hali buyurtmalar mavjud emas")
        return
    
    # Sahifalar sonini hisoblash (20 talik paginatsiya)
    total_pages = max(1, (len(orders) + 9) // 10)
    
    await state.update_data(orders=orders, total_pages=total_pages, page=1)
    await show_orders_page(message, state)

async def show_orders_page(message: Message, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    orders = data.get('orders', [])
    total_pages = data.get('total_pages', 1)
    
    # Sahifadagi elementlarni hisoblash (20 talik)
    start_idx = (page - 1) * 10
    end_idx = min(start_idx + 10, len(orders))
    page_orders = orders[start_idx:end_idx]
    
    # Navigatsiya tugmalari
    keyboard = []
    if total_pages > 1:
        row_buttons = []
        if page > 1:
            row_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"__prev_page_orders_{page}"))
        if page < total_pages:
            row_buttons.append(InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"__next_page_orders_{page}"))
        
        if row_buttons:
            keyboard.append(row_buttons)
    

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    # Sahifa sarlavhasi
    
    # Har bir buyurtmani alohida xabar qilish
    for order in page_orders:
        # Buyurtma itemlarini olish
        items = await sync_to_async(list)(
            OrderItem.objects.filter(order=order)
            .select_related('order', 'product', 'product__product_price')
        )
        
        items_text = ""
        for item in items:
            items_text += (
                f"🍕 {item.product.product_price.name}\n"
                f"   ├─ Soni: {item.quantity}\n"
                f"   ├─ Narxi: {item.product.product_price.selling_price}\n"
                f"   └─ Jami: {item.total_price} {order.base_currency.code}\n\n"
            )
        
        text = (
            f"🆔 Buyurtma ID: {order.id}\n"
            f"👤 Client: {order.client}\n"
            f"👤 kim sotdi: {order.user}\n"
            f"📅 Sana: {order.date.strftime('%d-%m-%Y')}\n"
            f"🚚 {order.get_status_display()}\n"
            f"📋 Buyurtma tarkibi:\n{items_text}"
            f"💵 Valyuta: {order.base_currency.code}\n"
            f"💰 Summa: {order.total_sum}\n"
            f"{'='*25}\n"
        )
        
        await message.answer(text)
    await message.answer(f"📦 Buyurtmalar Ro'yxati (Sahifa {page}/{total_pages})", reply_markup=reply_markup)
    
    await state.set_state(OrderPaginationStates.viewing_orders)

# TO'G'RI HANDLER - bu eng muhimi!
@router.callback_query(F.data.startswith("__prev_page_orders_") | F.data.startswith("__next_page_orders_"))
async def handle_orders_pagination(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    
    # TO'G'RI USUL: oxirgi elementni olish
    current_page = int(data.split("_")[-1])  # "prev_page_orders_2" -> ["prev", "page", "orders", "2"] -> 2
    
    if data.startswith("prev_page_orders_"):
        new_page = current_page - 1
    else:  # next_page_orders_
        new_page = current_page + 1
    
    await state.update_data(page=new_page)
    await callback.message.delete()  # Eski xabarni o'chirish
    await show_orders_page(callback.message, state)
    await callback.answer()



@router.message(F.text == "💵⏩💴 kassadan kassaga")
async def transfer_money(message: Message, user, state: FSMContext):
    if not user.is_staff:
        await message.answer("❌ Sizda bu bo‘limga kirish huquqi yo‘q")
        return

    kassalar = await sync_to_async(list)(Kassa.objects.select_related('currency').all())
    if len(kassalar) < 2:
        await message.answer("❌ Kamida 2 ta kassa bo‘lishi kerak.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{k.name} {k.currency} : {k.balance}" , callback_data=f'____kassa_transfer_from_{k.id}')]
        for k in kassalar
    ])
    await message.answer("💸 Qaysi kassadan pul o'tkazamiz? Tanlang:", reply_markup=kb)
    await state.set_state(TransferMoneyState.from_kassa)

# 2. Kassa tanlanganda
@router.callback_query(F.data.startswith("____kassa_transfer_from_"))
async def select_from_kassa__(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    from_kassa_id = int(data.split("_")[-1])
    await state.update_data(from_kassa_id=from_kassa_id)

    kassalar = await sync_to_async(list)(Kassa.objects.select_related('currency').exclude(id=from_kassa_id))
    if not kassalar:
        await callback.message.edit_text("❌ Boshqa kassa mavjud emas.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{k.name} {k.currency} : {k.balance}" , callback_data=f"__to_kassa__{k.id}")]
        for k in kassalar
    ])
    await callback.message.edit_text("💸 Qaysi kassaga pul o'tkazamiz? Tanlang:", reply_markup=kb)
    await state.set_state(TransferMoneyState.to_kassa)  
# 3. To kassa tanlanganda
@router.callback_query(F.data.startswith("__to_kassa__"))
async def select_to_kassa(callback: CallbackQuery, state: FSMContext):
    to_kassa_id = int(callback.data.split("_")[-1])
    await state.update_data(to_kassa_id=to_kassa_id)
    if to_kassa_id == (await state.get_data())['from_kassa_id']:
        await callback.answer("❌ Boshqa kassa tanlang!", show_alert=True)
        return

    await callback.message.edit_text("💰 Qancha pul o'tkazamiz? Miqdorni kiriting (masalan: `150000`):")
    await state.set_state(TransferMoneyState.amount)

# 4. Miqdorni yozganda
@router.message(TransferMoneyState.amount)
async def enter_amount(message: Message,user, state: FSMContext):
    try:
        amount = Decimal(message.text)
        if amount <= 0:
            raise ValueError("Miqdor musbat bo'lishi kerak.")
    except:
        await message.answer("❌ Miqdor noto‘g‘ri formatda, musbat son kiriting.")
        return

    data = await state.get_data()
    from_kassa = await sync_to_async(Kassa.objects.select_related('currency').get)(id=data["from_kassa_id"])
    to_kassa = await sync_to_async(Kassa.objects.select_related('currency').get)(id=data["to_kassa_id"])

    if from_kassa.currency.id != to_kassa.currency.id:
        await message.answer("❌ Kassa valyutalari mos emas.")
        return
    
        
    if from_kassa.balance < amount:
        await message.answer(f"❌ {from_kassa.name} kassasida yetarli mablag' yo'q.")
        return

    # Pul o'tkazish
    from_kassa.balance -= amount
    to_kassa.balance += amount
    await sync_to_async(from_kassa.save)()
    await sync_to_async(to_kassa.save)()
    
    await sync_to_async(Transfer.objects.create)(
        from_kassa=from_kassa,
        to_kassa=to_kassa,
        amount=amount,
        currency=from_kassa.currency,
        user=user)
        
    await message.answer(
        f"✅ Muvaffaqiyatli o'tkazildi!\n\n"
        f"🏦 {from_kassa.name} kassasidan \n"
        f"{to_kassa.name} kassasiga {amount} {from_kassa.currency.code} o'tkazildi.\n"
        f"📊 Yangi balans:\n"
        f"{from_kassa.name}: {from_kassa.balance} {from_kassa.currency.code}\n"
        f"{to_kassa.name}: {to_kassa.balance} {to_kassa.currency.code}"
    )
    await state.clear()
    
    
@router.message(F.text == "💵 ⏩ Kassa")
async def transfer_history(message: Message, user, state: FSMContext):
    if not user.is_staff:
        await message.answer("❌ Sizda bu bo‘limga kirish huquqi yo‘q")
        return

    transfers = await sync_to_async(list)(
        Transfer.objects.select_related('from_kassa', 'to_kassa', 'currency', 'user')
        .all().order_by('-id')[ :20 ]  # So'nggi 20 ta transferni olish
    )
    if not transfers:
        await message.answer("❌ Hali transferlar mavjud emas.")
        return

    text = "📋 Transferlar tarixi:\n\n"
    for t in transfers:
        text = (
            f"📅 Sana: {t.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"🏦 From: {t.from_kassa.name}\n"
            f"🏦 To: {t.to_kassa.name}\n"
            f"💰 Miqdor: {t.amount} {t.currency.code}\n"
            f"👤 Kim o'tkazdi: {t.user}\n"
            f"{'-'*35}\n"
        )

        await message.answer(text)

