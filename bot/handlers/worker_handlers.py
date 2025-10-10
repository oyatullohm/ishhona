from main.models import Product, Production, CustomUser, ProductNotMixed , Balans , Cost, ProductPrice #g modellaringiz
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from bot.keyboards.worker_kb import *
from aiogram import Router, F
router = Router()

@router.message(F.text == "💴 Balans")
async def user_balans(message:Message, user):
    if not user.is_worker:
        await message.answer("Sizda worker panelga kirish huquqi yo'q")
        return
    try:
        balans = await sync_to_async(Balans.objects.select_related('user').get)(user=user)
        text = (    
            f"💵 {balans.balans} so'm\n"
            f"👤{balans.user.username}"
            )
        await message.answer(text)
    except:
        await message.answer("sibzda balans yoq ")

ITEMS_PER_PAGE = 5  # har safar 5 ta chiqaramiz

@router.message(F.text == "🛠️ Men Chiqardim")
async def product_not_mixsid_user(message: Message, user, state: FSMContext):
    if not user.is_worker:
        await message.answer("Sizda worker panelga kirish huquqi yo'q")
        return
    await state.update_data(page=1)

    products = await sync_to_async(list)(
        Production.objects.select_related(
            'product', 'product__product_price', 'user'
        ).filter(user=user).order_by('-id')
    )

    total_pages = max(1, (len(products) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    await state.update_data(
        products=products,
        total_pages=total_pages,
        items_per_page=ITEMS_PER_PAGE
    )

    await show_products_page(message, state)

async def show_products_page(message: Message, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    products = data.get('products', [])
    total_pages = data.get('total_pages', 1)
    items_per_page = data.get('items_per_page', 5)

    # qaysi mahsulotlar chiqishi kerak
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(products))
    page_products = products[start_idx:end_idx]

    text = f"📋 Siz chiqargan mahsulotlar (Sahifa {page}/{total_pages})\n\n"
    for i, p in enumerate(page_products, start=start_idx + 1):
        text += (
            f"{i}. 📦 Nomi: {p.product.product_price}\n"
            f"   📊 Miqdori: {p.quantity}\n"
            f"   💵 Summa: {p.summa}\n"
            f"  📆 Date: {p.date}\n\n"
        )

    # Paginatsiya tugmalari
    keyboard = []
    row_buttons = []
    if page > 1:
        row_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"prod_prev_{page}"))
    if page < total_pages:
        row_buttons.append(InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"prod_next_{page}"))
    if row_buttons:
        keyboard.append(row_buttons)

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(text, reply_markup=reply_markup)
    await state.set_state(PaginationStates.viewing_transactions)

# Callback handler mahsulotlar uchun paginatsiya
@router.callback_query(F.data.startswith("prod_prev_") | F.data.startswith("prod_next_"))
async def handle_products_pagination(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    if data.startswith("prod_prev_"):
        current_page = int(data.split("_")[2])
        new_page = current_page - 1
    else:  # prod_next_
        current_page = int(data.split("_")[2])
        new_page = current_page + 1

    await state.update_data(page=new_page)
    await callback.message.delete()
    await show_products_page(callback.message, state)
    await callback.answer()


@router.message(F.text == "🛠️ Materiallar")
async def product_not_mixsid(message:Message, user):
    if not user.is_worker:
        await message.answer("Sizda worker panelga kirish huquqi yo'q")
        return
    product = await sync_to_async(list)(ProductNotMixed.objects.select_related('currency').all())
    for p in product:
        text = (
            f"📦 Nomi {p.name}\n"
            f"📊 Miqdori {p.quantity}\n"
            f"⚖️ unit {p.unit}\n"
        )
        await message.answer(text)

@router.message(F.text == "📦 Ombor Holati")
async def product_all(message:Message, user):
    if not user.is_deliverer:
        await message.answer("Sizda worker panelga kirish huquqi yo'q")
        return
    product = await sync_to_async(list)(Product.objects.select_related('product_price').all())
    for p in product:
        text = (
            f"📦 Nomi {p.product_price}\n"
            f"📊 Miqdori {p.quantity}"
        )
        await message.answer(text)
    

@router.message(F.text == "➕ Ishlab chiqarish")
async def start_production(message: Message, user, state: FSMContext):
    if not user.is_worker:
        await message.answer("Sizda worker panelga kirish huquqi yo'q")
        return
    products = await sync_to_async (list)(ProductPrice.objects.all())
    keyboard = [
        [InlineKeyboardButton(text=p.name, callback_data=f"prod:{p.id}")]
        for p in products
    ]
    await message.answer("Mahsulotni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await state.set_state(ProductionState.choosing_product)

# 2) Product tanlanganidan keyin
@router.callback_query(F.data.startswith("prod:"))
async def choose_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    product = await sync_to_async (Product.objects.select_related('product_price').get)(id=product_id)

    await state.update_data(product_id=product.id)
    await callback.message.answer(f"Siz tanladingiz: <b>{product.product_price.name}</b>\n\nMiqdorini kiriting:")
    await state.set_state(ProductionState.entering_quantity)

# 3) Miqdor kiritish
@router.message(ProductionState.entering_quantity)
async def enter_quantity(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)
    except ValueError:
        await message.answer("❌ Raqam kiriting!")
        return

    data = await state.get_data()
    product = await sync_to_async ( Product.objects.select_related('product_price').get)(id=data["product_id"])

    await state.update_data(quantity=quantity)

    text = (
        f"<b>Mahsulot:</b> {product.product_price.name}\n"
        f"<b>Miqdor:</b> {quantity} dona\n\n"
        f"Tasdiqlaysizmi?"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha", callback_data="confirm_yes"),InlineKeyboardButton(text="❌ Yo‘q", callback_data="confirm_no")],
        
    ])

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(ProductionState.confirming)

# 4) Ha bosilsa - create
@router.callback_query(F.data == "confirm_yes")
async def confirm_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product = await sync_to_async ( Product.objects.select_related('product_price').get)(id=data["product_id"])
    quantity = data["quantity"]

    # User olish (agar telegram_id orqali bog‘langan bo‘lsa)
    user =  await sync_to_async( CustomUser.objects.get)(telegram_id=callback.from_user.id)

    production = await sync_to_async( Production.objects.create)(
        product=product,
        quantity=quantity,
        user=user
    )

    await callback.message.answer(f"✅ Ishlab chiqarish qo‘shildi:\n{product.product_price.name} - {quantity} dona")
    await state.clear()

# 5) Yo‘q bosilsa - state clear
@router.callback_query(F.data == "confirm_no")
async def confirm_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Bekor qilindi.")
    await state.clear()


@router.message(F.text == "💵 Olgan Pullarim")
async def mone_ya(message: Message, user, state: FSMContext):
    if not user.is_worker:
        await message.answer("Sizda worker panelga kirish huquqi yo'q")
        return
    await state.update_data(page=1)

    productions = await sync_to_async(list)(
        Cost.objects.select_related(
            'category', 'currency',"kassa",  'user'
        ).filter(user=user).order_by('-id')
    )

    total_pages = max(1, (len(productions) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    await state.update_data(
        productions=productions,
        total_pages=total_pages,
        items_per_page=ITEMS_PER_PAGE
    )

    await show_productions_page(message, state)


async def show_productions_page(message: Message, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    productions = data.get('productions', [])
    total_pages = data.get('total_pages', 1)
    items_per_page = data.get('items_per_page', 5)

    # qaysi mahsulotlar chiqishi kerak
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(productions))
    page_productions = productions[start_idx:end_idx]

    text = f"📋 Siz olgan pullar (Sahifa {page}/{total_pages})\n\n"
    for i, p in enumerate(page_productions, start=start_idx + 1):
        text += (
            f"{i}. 📦 Nomi: {p.category}\n"
            f" 👥 Kim {p.user}\n"
            f"   💵 Summa: {p.amount}\n"
            f"  📆 Date: {p.date}\n\n"
        )

    # Paginatsiya tugmalari
    keyboard = []
    row_buttons = []
    if page > 1:
        row_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"cost_prev_{page}"))
    if page < total_pages:
        row_buttons.append(InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"cost_next_{page}"))
    if row_buttons:
        keyboard.append(row_buttons)

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(text, reply_markup=reply_markup)
    await state.set_state(CostPaginationStates.viewing_transactions)

# Callback handler mahsulotlar uchun paginatsiya
@router.callback_query(F.data.startswith("cost_prev_") | F.data.startswith("cost_next_"))
async def handle_productions_pagination(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    if data.startswith("cost_prev_"):
        current_page = int(data.split("_")[2])
        new_page = current_page - 1
    else:  # cost_next_
        current_page = int(data.split("_")[2])
        new_page = current_page + 1

    await state.update_data(page=new_page)
    await callback.message.delete()
    await show_productions_page(callback.message, state)
    await callback.answer() 

