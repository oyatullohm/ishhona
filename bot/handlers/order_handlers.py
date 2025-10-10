from main.models import Client, Order, OrderItem, Currency, Product ,CustomUser, Kassa,Cource
from aiogram.types import Message, CallbackQuery,InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from bot.keyboards import order_kb
from aiogram import Router, F
router = Router()
        
@router.message(F.text == "📦 Ombor __Holati__")
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
        

@router.message(F.text == "📦 Buyurtmalar_")
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
                f"   ├─ Narxi: {item.unit_price}\n"
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
    
    await state.set_state(order_kb.OrderPaginationStates.viewing_orders)

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



@router.message(F.text == "👥 Clientga Savdo")
async def order_create(message: Message, user, state: FSMContext):  
    if not user:
        await message.answer("❌ Sizda ruxsat yo'q")
        return
    
    clients = await sync_to_async(list)(Client.objects.filter(client_type='customer'))
    if not clients:
        await message.answer("❌ Hozircha mijozlar mavjud emas. Avval mijoz qo'shing.")
    else:
        await message.answer(
            "Mijozni tanlang:",
            reply_markup=order_kb.client_selection_keyboard(clients)
        )
       
    await state.set_state(order_kb.DelivererStates.selecting_client)

# 👤 Mijoz tanlash
@router.callback_query(F.data.startswith("select_cclient_"), order_kb.DelivererStates.selecting_client)
async def select_client(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split("_")[2])
    client = await sync_to_async(Client.objects.get)(id=client_id)
    
    await state.update_data(client_id=client_id)
    
    await callback.message.answer(
        f"✅ Mijoz tanlandi:\n"
        f"👤 {client.name}\n"
        f"📞 {client.phone_number}\n"
        f"📍 {client.address or 'Manzil kiritilmagan'}\n\n"
        f"📝 Valyutani tanlang:",
        reply_markup=order_kb.button_valyuta()
    )


    await state.set_state(order_kb.DelivererStates.selecting_order)
    await callback.answer()

# 📝 Savdo ta'rifini kiritish
@router.callback_query(F.data.in_(["UZS", "USD"]), order_kb.DelivererStates.selecting_order)
async def enter_order_details(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client = await sync_to_async(Client.objects.get)(id=data['client_id'])
    currency_code = callback.data
    user = await sync_to_async(CustomUser.objects.get)(telegram_id=callback.from_user.id)
    currency = await sync_to_async(Currency.objects.get)(code=currency_code)
    order = Order(
        client=client,
        total_amount=0,
        status='pending',            
        base_currency= currency,
        user = user
    )
    await sync_to_async(order.save)()
    
    await state.update_data(order_id=order.id)

    products = await sync_to_async(list)(Product.objects.select_related('product_price').all())
    await callback.message.answer(
        f"✅ Savdo yaratildi! (ID: {order.id})\n\n"
        f"Endi mahsulot tanlang:",
        reply_markup=order_kb.product_selection_keyboard(products)
    )
    await state.set_state(order_kb.DelivererStates.selecting_product)


# 📦 Mahsulot tanlash
@router.callback_query(F.data.startswith("select_pproduct_"), order_kb.DelivererStates.selecting_product)
async def select_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    
    await state.update_data(product_id=product_id)

    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=product_id)
    await callback.message.answer(
        f"📦 Mahsulot tanlandi: {product.product_price.name}\n"
        f"💵 Narxi: {product.product_price.selling_price} so'm\n\n"
        f"❓ Nechta olasiz?"
    )
    await state.set_state(order_kb.DelivererStates.entering_quantity)
    await callback.answer()


# 🔢 Miqdor kiritish
@router.message(order_kb.DelivererStates.entering_quantity)
async def enter_quantity(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)
    except ValueError:
        await message.answer("❌ Faqat son kiriting.")
        return
    
    data = await state.get_data()
    order = await sync_to_async(Order.objects.get)(id=data['order_id'])
    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=data['product_id'])

    order_item = OrderItem(order=order, product=product, quantity=quantity,unit_price=product.product_price.selling_price)
    await sync_to_async(order_item.save)()

    await message.answer(
        f"✅ Qo‘shildi: {product.product_price.name} x {quantity} = {order_item.total_price} so‘m\n\n"
        f"Yana mahsulot tanlang yoki ✅ Yakunlash tugmasini bosing.",
        reply_markup=order_kb.product_selection_keyboard(await sync_to_async(list)(Product.objects.select_related('product_price').all()))
    )
    await state.set_state(order_kb.DelivererStates.selecting_product)


# ✅ Yakunlash
@router.callback_query(F.data == "finish_order_", order_kb.DelivererStates.selecting_product)
async def finish_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order = await sync_to_async(Order.objects.prefetch_related('items').select_related('client','base_currency').get)(id=data['order_id'])
    

    items = await sync_to_async(list)(OrderItem.objects.select_related('product','product__product_price').filter(order=order))
    for i in items:
        p = await sync_to_async(Product.objects.select_related('product_price').get)(id=i.product.id)
        p.quantity -= i.quantity
        await sync_to_async(p.save)()
    total = sum([i.total_price for i in items])
    order.total_amount = total
    await sync_to_async(order.save)()
    summary = "\n".join([f"{i.product.product_price.name} x {i.quantity} = {i.total_price}" for i in items])
    await callback.message.answer(
        f"✅ Buyurtma yakunlandi!\n"
        f"🆔 Order ID: {order.id}\n"
        f" {summary}\n"
        f"💰 Jami: {total} so‘m \n"

    )

    await state.clear()
    await callback.answer()


@router.message(F.text == "💰 Naq Pulga Savdo")
async def order_create_not_client(message: Message, user, state: FSMContext):  
    if not user:
        await message.answer("❌ Sizda ruxsat yo'q")
        return
    
    kassa = await sync_to_async(list)(Kassa.objects.select_related('currency').all())
    if not kassa:
        await message.answer("❌ Hozircha mijozlar mavjud emas. Avval mijoz qo'shing.")
    else:
        await message.answer(
            "kassani tallang :",
            reply_markup=order_kb.kassa_selection_keyboard(kassa)
        )
       
    await state.set_state(order_kb.DelivererStates.kassa)

# 👤 Mijoz tanlash
@router.callback_query(F.data.startswith("select_kassa_"), order_kb.DelivererStates.kassa)
async def select_kassa_not_Client(callback: CallbackQuery, state: FSMContext):
    kassa_id = int(callback.data.split("_")[2])
    kassa = await sync_to_async(Kassa.objects.select_related('currency').get)(id=kassa_id)
    
    await state.update_data(kassa_id=kassa_id)
    
    await callback.message.answer(
        f"✅ kassa tanlandi:\n"
        f"👤 {kassa.name}\n"
        f"💵 {kassa.currency}\n"
    )

    user = await sync_to_async(CustomUser.objects.get)(telegram_id=callback.from_user.id)

    order = Order(
        total_amount=0,
        status='delivered',            
        base_currency= kassa.currency,
        user = user
    )
    await sync_to_async(order.save)()
    
    await state.update_data(order_id=order.id)

    products = await sync_to_async(list)(Product.objects.select_related('product_price').all())
    await callback.message.answer(
        f"✅ Savdo yaratildi! (ID: {order.id})\n\n"
        f"Endi mahsulot tanlang:",
        reply_markup=order_kb.product_selection_keyboard_not_client(products)
    )
    await state.set_state(order_kb.DelivererStates.selecting_product)


# 📦 Mahsulot tanlash
@router.callback_query(F.data.startswith("select_ppproduct_"), order_kb.DelivererStates.selecting_product)
async def select_product_not_client(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    
    await state.update_data(product_id=product_id)

    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=product_id)
    await callback.message.answer(
        f"📦 Mahsulot tanlandi: {product.product_price.name}\n"
        f"💵 Narxi: {product.product_price.selling_price} so'm\n\n"
        f"❓ Nechta olasiz?"
    )
    await state.set_state(order_kb.DelivererStates.entering_quantity_NO_CLIENT)
    await callback.answer()


# 🔢 Miqdor kiritish
@router.message(order_kb.DelivererStates.entering_quantity_NO_CLIENT)
async def enter_quantity_NO_CLIENT(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)
        await state.update_data(quantity=quantity)
    except ValueError:
        await message.answer("❌ Faqat son kiriting.")
        return

    
    data = await state.get_data()
    order = await sync_to_async(Order.objects.get)(id=data['order_id'])
    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=data['product_id'])
    await message.answer(
        f"📦 Mahsulot tanlandi: {product.product_price.name}\n"
        f"💵 Narxi: {product.product_price.selling_price} so'm\n"
        f"❓ Narh Kiritng",
        )
    await state.set_state(order_kb.DelivererStates.entering_amount_NO_CLIENT)


@router.message(order_kb.DelivererStates.entering_amount_NO_CLIENT)
async def enter_amount_NO_CLIENT(message: Message, state: FSMContext):
    amount = message.text
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("❌ Faqat son kiriting.")
        return
    data = await state.get_data()
    order = await sync_to_async(Order.objects.get)(id=data['order_id'])
    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=data['product_id'])
    quantity = data['quantity']
    # product.product_price.selling_price = amount
    order_item = OrderItem(order=order, product=product, quantity=quantity, unit_price=amount)
    await sync_to_async(order_item.save)()
    await message.answer(
        f"✅ Qo‘shildi: {product.product_price.name} x {quantity} = {order_item.total_price} so‘m\n\n"
        f"Yana mahsulot tanlang yoki ✅ Yakunlash tugmasini bosing.",
        reply_markup=order_kb.product_selection_keyboard_not_client(await sync_to_async(list)(Product.objects.select_related('product_price').all()))
    )
    await state.set_state(order_kb.DelivererStates.selecting_product_NO_CLIENT)


# ✅ Yakunlash
@router.callback_query(F.data == "no_client_finish_order", order_kb.DelivererStates.selecting_product_NO_CLIENT)
async def finish_order_no_client(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order = await sync_to_async(Order.objects.prefetch_related('items').select_related('client','base_currency').get)(id=data['order_id'])
    
    kassa = await sync_to_async(Kassa.objects.select_related('currency').get)(id=data['kassa_id'])
    items = await sync_to_async(list)(OrderItem.objects.select_related('product','product__product_price').filter(order=order))
    
    for i in items:
        p = await sync_to_async(Product.objects.select_related('product_price').get)(id=i.product.id)
        p.quantity -= i.quantity
        await sync_to_async(p.save)()
    cource = await sync_to_async(Cource.objects.last)()
    total = sum([i.total_price for i in items])
    if kassa.currency.code == "USD":
        total = total / cource.cource 
    order.total_amount = total
    
    kassa.balance += total
    await sync_to_async(kassa.save)()
    await sync_to_async(order.save)()
    summary = "\n".join([f"{i.product.product_price.name} x {i.quantity} = {i.total_price}" for i in items])
    await callback.message.answer(
        f"✅ Buyurtma yakunlandi!\n"
        f"🆔 Order ID: {order.id}\n"
        f" {summary}\n"
        f"💰 Jami: {total} {kassa.currency.code} \n"

    )
    await state.clear()
    await callback.answer()