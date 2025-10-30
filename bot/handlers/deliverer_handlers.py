
from main.models import (Order, Client,CustomUser,OrderItem,
                         Product,ClientBalance, Currency)
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards import deliverer_kb
from asgiref.sync import sync_to_async
from aiogram import Router, F
router = Router()

@router.message(F.text == "🚚 Yetkazib Berish")
async def delivery_orders(message: Message, user):  # user parametri
    if not user.is_deliverer:
        await message.answer("Sizda ruxsat yo'q")
        return
    
    # Yetkazib berish uchun tayyor buyurtmalar
    orders = await sync_to_async(list)(
        Order.objects.select_related('client','base_currency').filter(status='pending').order_by('-id')[:10]
    )
    
    if not orders:
        await message.answer("Hozircha yetkazib berish uchun buyurtma yo'q")
        return
    
    # orders_text = "🚚 Yetkazib berish uchun buyurtmalar:\n\n"
    for order in orders:
        text = ''
       
        text += f"🆔 {order.id} - {order.client.name}\n"
        text += f"📞 {order.client.phone_number}\n"
        text += f"🚚 {order.get_status_display()}\n"
        text +=  f"📍 {order.client.address or 'Manzil kiritilmagan'}\n"
        
        # orders_text += f"💵 {order.total_amount} {order.currency.code}\n"
        text +=  f"─" * 20 + "\n"
        await message.answer(text, reply_markup=deliverer_kb.order_edit(order))
    await message.answer(
        '🚚 Yetkazib berish uchun buyurtmalar',
        reply_markup=deliverer_kb.orders_keyboard(orders)
    )
#byurtmani tanlash
@router.callback_query(F.data.startswith("deliver_item_edit_"))
async def select_order_for_edit(callback: CallbackQuery, state: FSMContext): 
    order_id = int(callback.data.split("_")[3])
    # await callback.message.answer(f"Siz tanlagan buyurtma IDsi: {order_id} bo'yicha mahsulotlar ro'yxati:")
    order = await sync_to_async(Order.objects.prefetch_related('items').select_related('client','base_currency').get)(id=order_id)
    for i in  await sync_to_async(list)(order.items.all().select_related('product','product__product_price')):
        await callback.message.answer(
            f"✅ ID Order : {order.id}:\n"
            f"✅ ID Product : {i.id}:\n"
            f"🍕 {i.product.product_price.name}\n"
            f"   ├─ Soni: {i.quantity}\n"
            f"   └─ Narxi: {i.total_price} {order.base_currency.code}\n\n",
            reply_markup=deliverer_kb.order_item_edit_keyboard(i.id)
        )
    await callback.answer()
    
# Buyurtma tanlash
@router.callback_query(F.data.startswith("_item_edit_"))
async def edit_order_item(callback: CallbackQuery, state: FSMContext):  # user parametri

    item_id = int(callback.data.split("_")[3])
    item = await sync_to_async(OrderItem.objects.select_related('order','product','product__product_price').get)(id=item_id)
    
    await state.update_data(item_id=item_id)
    await callback.message.answer(
        f"✅ Mahsulot tanlandi:\n"
        f"🍕 {item.product.product_price.name}\n"
        f"   ├─ Soni: {item.quantity}\n"
        f"   ├─ Narh: {item.unit_price}\n"
        f"   └─ Jami: {item.product.product_price.selling_price}\n"
        f"Qanday o'zgartirish kiritmoqchisiz?",
        reply_markup=deliverer_kb.order_item_action_keyboard(item_id)
    )
    await state.set_state(deliverer_kb.DelivererStates.editing_order_item)
    await callback.answer()


@router.callback_query(F.data.startswith("d_item_edit_price_"))
async def edit_order_item_price(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = data['item_id']
    item = await sync_to_async(OrderItem.objects.select_related('order','product','product__product_price').get)(id=item_id)
    await callback.message.answer(f"✏️ Iltimos, yangi narxni kiriting (Hozirgi narx: {item.product.product_price.selling_price}):")
    await state.set_state(deliverer_kb.DelivererStates.entering_price_edit)
    await callback.answer()

@router.message(deliverer_kb.DelivererStates.entering_price_edit)
async def enter_new_price_(message: Message, state: FSMContext):
    try:
        new_price = int(message.text)
        data = await state.get_data()
        item_id = data['item_id']
        item = await sync_to_async(OrderItem.objects.select_related('order','product','product__product_price').get)(id=item_id)
        item.unit_price = new_price
        await sync_to_async(item.save)()
        await message.answer(
            f"✅ Narx yangilandi: {item.product.product_price.name} yangi narxi {new_price} so‘m\n\n",
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Faqat son kiriting.")
        return

@router.callback_query(F.data.startswith("d_item_edit_quantity_"))
async def edit_order_item_quantity(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = data['item_id']
    item = await sync_to_async(OrderItem.objects.select_related('order','product','product__product_price').get)(id=item_id)
    await callback.message.answer(f"✏️ Iltimos, yangi miqdorni kiriting (Hozirgi miqdor: {item.quantity}):")
    await state.set_state(deliverer_kb.DelivererStates.entering_quantity_edit)
    await callback.answer()

@router.message(deliverer_kb.DelivererStates.entering_quantity_edit)
async def enter_new_quantity_(message: Message, state: FSMContext):
    try:
        new_quantity = int(message.text)
        data = await state.get_data()
        item_id = data['item_id']
        item = await sync_to_async(OrderItem.objects.select_related('order','product','product__product_price').get)(id=item_id)
        quantity = item.quantity
        item.quantity = new_quantity
        
        product = await sync_to_async(Product.objects.select_related('product_price').get)(id=item.product.id)
        product.quantity += quantity
        product.quantity -= new_quantity
        await sync_to_async(product.save)()
        
        await sync_to_async(item.save)()
        await message.answer(
            f"✅ Miqdor yangilandi: {item.product.product_price.name} yangi miqdori {new_quantity} ta\n\n",
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Faqat son kiriting.")
        return

@router.callback_query(F.data.startswith("d_item_product__"))
async def edit_order_item_product(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = data['item_id']
    await callback.message.answer("📦 Iltimos, yangi mahsulotni tanlang:", reply_markup=deliverer_kb.product_selection_keyboard(await sync_to_async(list)(Product.objects.select_related('product_price').all())))
    await state.set_state(deliverer_kb.DelivererStates.selecting_product_edit)
    await callback.answer()
    
@router.callback_query(deliverer_kb.DelivererStates.selecting_product_edit, F.data.startswith("select_product_"))
async def select_product_edit_(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    
    data = await state.get_data()
    item_id = data['item_id']
    item = await sync_to_async(OrderItem.objects.select_related('order','product','product__product_price').get)(id=item_id)
    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=product_id)
    item.product = product
    item.unit_price = product.product_price.selling_price
    await sync_to_async(item.save)()
    await callback.message.answer(
        f"✅ Mahsulot yangilandi: Yangi mahsulot {product.product_price.name}\n\n",
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith("d_item_delete__"))
async def delete_order_item(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = data['item_id']   
    item = await sync_to_async(OrderItem.objects.select_related('order','product','product__product_price').get)(id=item_id)
    quantity = item.quantity
    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=item.product.id)
    product.quantity += quantity
    await sync_to_async(product.save)()
    await sync_to_async(item.delete)()
    order = await sync_to_async(Order.objects.prefetch_related('items').select_related('client','base_currency').get)(id=item.order.id)
    if order.items.count() == 0:
        await sync_to_async(order.delete)()
        await callback.message.answer(
            f"✅ Buyurtma bekor qilindi, chunki unda mahsulot qolmadi.\n\n",
        )
        await state.clear()
        await callback.answer()
        return
    await callback.message.answer(
        f"✅ Mahsulot o'chirildi: {item.product.product_price.name}\n\n",
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("deliver_order_"))
async def select_order_for_delivery(callback: CallbackQuery, state: FSMContext):  # user parametri

    order_id = int(callback.data.split("_")[2])
    order = await sync_to_async(Order.objects.select_related('client','base_currency').get)(id=order_id)
    
    await state.update_data(order_id=order_id)
    item = await sync_to_async(list) (OrderItem.objects.filter(order=order).select_related('order','product','product__product_price'))
    items_text = ""
    for i in item:
        items_text += (
            f"🍕 {i.product.product_price.name}\n"
            f"   ├─ Soni: {i.quantity}\n"
            f"   └─ Narxi: {i.total_price} {order.base_currency.code}\n\n"
        )
    await callback.message.answer(
        f"✅ Buyurtma tanlandi:\n"
        f"🆔 {order.id} - {order.client.name}\n"
        f"📞 {order.client.phone_number}\n"
        f"📍 {order.client.address}\n\n"
        f"🛒 <b>Mahsulotlar:</b>\n\n"
        f"{items_text}"
        f"Yetkazib berishni tasdiqlaysizmi?",
        reply_markup=deliverer_kb.confirm_delivery_keyboard()
    )
    await state.set_state(deliverer_kb.DelivererStates.confirming_delivery)
    await callback.answer()

# Yetkazib berishni tasdiqlash
@router.callback_query(deliverer_kb.DelivererStates.confirming_delivery, F.data == "confirm_delivery")
async def confirm_delivery(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order = await sync_to_async(Order.objects.select_related('client','base_currency').prefetch_related('items').get)(id=data['order_id'])
    # Buyurtma holatini yangilash
    if order.status == 'delivered':
        await callback.message.answer("❌ Bu buyurtma allaqachon yetkazib berilgan.")
        await state.clear()
        await callback.answer()
        return
    order.status = 'delivered'
    await sync_to_async(order.save)()
    
    balance = await sync_to_async(
    lambda: list(ClientBalance.objects.filter(client=order.client,currency=order.base_currency).select_related('client', 'currency'))
            )()
    old_balance = 0
    last_balanse = 0
    if balance:
        
        balance = balance[0]
        old_balance = balance.amount
        balance.amount += order.total_amount
        last_balanse = old_balance + order.total_amount
    
        await sync_to_async(balance.save)()
    item = await sync_to_async(list) (OrderItem.objects.filter(order=order).select_related('order','product','product__product_price'))
    items_text = ""
    for i in item:
        items_text += (
            f"🍕 {i.product.product_price.name}\n"
            f"   ├─ Soni: {i.quantity}\n"
            f"   └─ Narxi: {i.total_price} {order.base_currency.code}\n\n"
        )
    await callback.message.answer(
        f"✅ Buyurtma yetkazib berildi!\n"
        f"🆔 Buyurtma: {order.id}\n"
        f"👤 Mijoz: {order.client.name}\n"
         f"🛒 <b>Mahsulotlar:</b>\n\n"
        f"{items_text}"
        f"📞 Tel: {order.client.phone_number}\n"
        f"Oldin {old_balance} {order.base_currency} edi\n"
        f"kegin {last_balanse} {order.base_currency} boldi\n"
    )
    await state.clear()
    await callback.answer()


@router.message(F.text == "📋 clientga savdo")
async def order_create(message: Message, user, state: FSMContext):  
    if not user.is_deliverer:
        await message.answer("❌ Sizda ruxsat yo'q")
        return
    
    clients = await sync_to_async(list)(Client.objects.filter(client_type='customer'))
    if not clients:
        await message.answer("❌ Hozircha mijozlar mavjud emas. Avval mijoz qo'shing.")
    else:
        await message.answer(
            "Mijozni tanlang:",
            reply_markup=deliverer_kb.client_selection_keyboard(clients)
        )
       
    await state.set_state(deliverer_kb.DelivererStates.selecting_client)

# 👤 Mijoz tanlash
@router.callback_query(F.data.startswith("select_client_"), deliverer_kb.DelivererStates.selecting_client)
async def select_client(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split("_")[2])
    client = await sync_to_async(Client.objects.get)(id=client_id)
    
    await state.update_data(client_id=client_id)
    
    await callback.message.answer(
        f"✅ Mijoz tanlandi:\n"
        f"👤 {client.name}\n"
        f"📞 {client.phone_number}\n"
        f"📍 {client.address or 'Manzil kiritilmagan'}\n\n")

    data = await state.get_data()
    client = await sync_to_async(Client.objects.get)(id=data['client_id'])
    currency_code = callback.data
    user = await sync_to_async(CustomUser.objects.get)(telegram_id=callback.from_user.id)
    currency = await sync_to_async(Currency.objects.get)(code='UZS')
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
        reply_markup=deliverer_kb.product_selection_keyboard(products)
    )
    await state.set_state(deliverer_kb.DelivererStates.selecting_product)


# 📦 Mahsulot tanlash
@router.callback_query(F.data.startswith("select_product_"), deliverer_kb.DelivererStates.selecting_product)
async def select_product_(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    
    await state.update_data(product_id=product_id)

    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=product_id)
    await callback.message.answer(
        f"📦 Mahsulot tanlandi: {product.product_price.name}\n"
        f"💵 Narxi: {product.product_price.selling_price} so'm\n\n"
        f"❓ Nechta olasiz?"
    )
    await state.set_state(deliverer_kb.DelivererStates.entering_quantity)
    await callback.answer()


@router.message(deliverer_kb.DelivererStates.entering_quantity)
async def enter_quantity_(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)
    except ValueError:
        await message.answer("❌ Faqat son kiriting.")
        return
    from bot.keyboards.order_kb import price_choice_keyboard
    await state.update_data(quantity=quantity)
    await message.answer(
        "💰 Narxni tanlang:",
        reply_markup=price_choice_keyboard()
    )
    await state.set_state(deliverer_kb.DelivererStates.choosing_price_type)

@router.callback_query(deliverer_kb.DelivererStates.choosing_price_type)
async def choose_price_type_(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=data['product_id'])

    if callback.data == "price_standard":
        unit_price = product.product_price.selling_price
        quantity = data['quantity']
        order = await sync_to_async(Order.objects.get)(id=data['order_id'])
        order_item = OrderItem(order=order, product=product, quantity=quantity, unit_price=unit_price)
        await sync_to_async(order_item.save)()
        await callback.message.answer(
            f"✅ Qo‘shildi: {product.product_price.name} x {quantity} = {order_item.total_price} so‘m\n\n"
            f"Yana mahsulot tanlang yoki ✅ Yakunlash tugmasini bosing.",
            reply_markup=deliverer_kb.product_selection_keyboard(await sync_to_async(list)(Product.objects.select_related('product_price').all()))
        )
        await state.set_state(deliverer_kb.DelivererStates.selecting_product)
    elif callback.data == "price_custom":
        await callback.message.answer("✏️ Iltimos, narxni kiriting:")
        await state.set_state(deliverer_kb.DelivererStates.entering_price)

    await callback.answer()

# 💵 Qo‘lda narx kiritish
@router.message(deliverer_kb.DelivererStates.entering_price)
async def enter_price_(message: Message, state: FSMContext):
    try:
        unit_price = int(message.text)
        data = await state.get_data()
        product = await sync_to_async(Product.objects.select_related('product_price').get)(id=data['product_id'])
        quantity = data['quantity']
        order = await sync_to_async(Order.objects.get)(id=data['order_id'])
        order_item = OrderItem(order=order, product=product, quantity=quantity, unit_price=unit_price)
        await sync_to_async(order_item.save)()
        await message.answer(
            f"✅ Qo‘shildi: {product.product_price.name} x {quantity} = {order_item.total_price} so‘m\n\n"
            f"Yana mahsulot tanlang yoki ✅ Yakunlash tugmasini bosing.",
            reply_markup=deliverer_kb.product_selection_keyboard(await sync_to_async(list)(Product.objects.select_related('product_price').all()))
        )
        await state.set_state(deliverer_kb.DelivererStates.selecting_product)
    except ValueError:
        await message.answer("❌ Faqat son kiriting.")
        return
# ✅ Yakunlash
@router.callback_query(F.data == "finish_order", deliverer_kb.DelivererStates.selecting_product)
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

@router.message(F.text == "📦 Ombor Holati_")
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