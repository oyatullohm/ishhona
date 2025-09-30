from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from main.models import Order, Client, CustomUser, OrderItem, Product,ClientBalance, Currency
from bot.keyboards import deliverer_kb
from asgiref.sync import sync_to_async

router = Router()

# Faqat yetkazib beruvchilar uchun
class DelivererStates(StatesGroup):
    selecting_order = State()
    updating_status = State()
    confirming_delivery = State()
    selecting_client = State()      # mijoz tanlash
    selecting_order = State()       # savdo ta'rifi kiritish
    selecting_product = State()     # mahsulot tanlash
    entering_quantity = State()     # miqdor kiritish


# Yetkazib berish uchun buyurtmalar
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
    
    orders_text = "🚚 Yetkazib berish uchun buyurtmalar:\n\n"
    for order in orders:
        orders_text += f"🆔 {order.id} - {order.client.name}\n"
        orders_text += f"📞 {order.client.phone_number}\n"
        orders_text += f"📍 {order.client.address or 'Manzil kiritilmagan'}\n"
        # orders_text += f"💵 {order.total_amount} {order.currency.code}\n"
        orders_text += "─" * 20 + "\n"
    
    await message.answer(
        orders_text,
        reply_markup=deliverer_kb.orders_keyboard(orders)
    )

# Buyurtma tanlash
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
    await state.set_state(DelivererStates.confirming_delivery)
    await callback.answer()

# Yetkazib berishni tasdiqlash
@router.callback_query(DelivererStates.confirming_delivery, F.data == "confirm_delivery")
async def confirm_delivery(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order = await sync_to_async(Order.objects.select_related('client','base_currency').prefetch_related('items').get)(id=data['order_id'])
    # Buyurtma holatini yangilash
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
        balance.amount -= order.total_amount
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
        f"kegin {last_balanse} {order.base_currency} edi\n"
    )
    await state.clear()
    await callback.answer()


@router.message(F.text == "📋 clientga savdo")
async def order_create(message: Message, user, state: FSMContext):  
    if not user.is_deliverer:
        await message.answer("❌ Sizda ruxsat yo'q")
        return
    
    clients = await sync_to_async(list)(Client.objects.all())
    if not clients:
        await message.answer("❌ Hozircha mijozlar mavjud emas. Avval mijoz qo'shing.")
    else:
        await message.answer(
            "Mijozni tanlang:",
            reply_markup=deliverer_kb.client_selection_keyboard(clients)
        )
       
    await state.set_state(DelivererStates.selecting_client)

# 👤 Mijoz tanlash
@router.callback_query(F.data.startswith("select_client_"), DelivererStates.selecting_client)
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
        reply_markup=deliverer_kb.button_valyuta()
    )


    await state.set_state(DelivererStates.selecting_order)
    await callback.answer()

# 📝 Savdo ta'rifini kiritish
@router.callback_query(F.data.in_(["UZS", "USD"]), DelivererStates.selecting_order)
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
        reply_markup=deliverer_kb.product_selection_keyboard(products)
    )
    await state.set_state(DelivererStates.selecting_product)


# 📦 Mahsulot tanlash
@router.callback_query(F.data.startswith("select_product_"), DelivererStates.selecting_product)
async def select_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    
    await state.update_data(product_id=product_id)

    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=product_id)
    await callback.message.answer(
        f"📦 Mahsulot tanlandi: {product.product_price.name}\n"
        f"💵 Narxi: {product.product_price.selling_price} so'm\n\n"
        f"❓ Nechta olasiz?"
    )
    await state.set_state(DelivererStates.entering_quantity)
    await callback.answer()


# 🔢 Miqdor kiritish
@router.message(DelivererStates.entering_quantity)
async def enter_quantity(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)
    except ValueError:
        await message.answer("❌ Faqat son kiriting.")
        return
    
    data = await state.get_data()
    order = await sync_to_async(Order.objects.get)(id=data['order_id'])
    product = await sync_to_async(Product.objects.select_related('product_price').get)(id=data['product_id'])

    order_item = OrderItem(order=order, product=product, quantity=quantity)
    await sync_to_async(order_item.save)()

    await message.answer(
        f"✅ Qo‘shildi: {product.product_price.name} x {quantity} = {order_item.total_price} so‘m\n\n"
        f"Yana mahsulot tanlang yoki ✅ Yakunlash tugmasini bosing.",
        reply_markup=deliverer_kb.product_selection_keyboard(await sync_to_async(list)(Product.objects.select_related('product_price').all()))
    )
    await state.set_state(DelivererStates.selecting_product)


# ✅ Yakunlash
@router.callback_query(F.data == "finish_order", DelivererStates.selecting_product)
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