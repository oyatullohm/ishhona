from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from decimal import Decimal, ROUND_HALF_UP
from django.dispatch import receiver
from django.db import models
from datetime import date
class Benefit(models.Model):
    percentage = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date = models.DateField(default=date.today)
    def __str__(self):
        return f"{self.percentage} %"
    class Meta:
        verbose_name = "Foyda"
        verbose_name_plural = "Foydalar"
    
class BotSettings(models.Model):
    admin_password = models.CharField(max_length=255, default="admin123")
    worker_password = models.CharField(max_length=255, default="012345")
    driver_password = models.CharField(max_length=255, default="012345")
    trade_password = models.CharField(max_length=255, default="012345")
    start_password = models.CharField(max_length=255, default="012345")
    order_password = models.CharField(max_length=255, default="012345")

    class Meta:
        verbose_name = "Bot sozlamasi"
        verbose_name_plural = "Bot sozlamalari"

    def save(self, *args, **kwargs):
        # Faqat bitta yozuvga ruxsat
        if not self.pk and BotSettings.objects.exists():
            raise Exception("Faqat bitta BotSettings yozuvi bo‘lishi mumkin!")
        return super().save(*args, **kwargs)

    def __str__(self):
        return "Bot parollari sozlamalari"


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)  # USD, UZS, EUR

    def __str__(self):
        return f"{self.code}"
    class Meta:
        verbose_name = "Valyuta"
        verbose_name_plural = "Valyutalar"

# Valyuta kursi modeli
class Cource(models.Model):
    cource = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"{self.cource}"
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        product = ProductPrice.objects.all()
        for i in product:
            i.save()
    class Meta:
        verbose_name = "Valyuta kursi"
        verbose_name_plural = "Valyuta kurslari"      


class CustomUser(AbstractUser):
    telegram_id = models.PositiveBigIntegerField(blank=True, null=True, unique=True)
    is_worker = models.BooleanField(default=False)
    is_deliverer = models.BooleanField(default=False)
    is_order = models.BooleanField(default=True)
    
    class Meta: 
        verbose_name = "Foydalanuchi"
        verbose_name_plural = "Foydalanichilar"
    def __str__(self):
        return f"{self.username}"
# Kassa modeli


class Balans(models.Model):
    balans = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True )

    def __str__(self):
        return f"{self.balans}"
    class Meta:
        verbose_name = "Balans"
        verbose_name_plural = "Balanslar"
        

class Kassa(models.Model):
    name = models.CharField(max_length=55)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1)
    
    def __str__(self):
        return f"{self.name} : {self.balance} : {self.currency.code}"

    class Meta:
        verbose_name = "Kassa"
        verbose_name_plural = "Kassalar"
    
# Kassa harakatlari uchun model
class KassaTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Kirim'),
        ('expense', 'Chiqim'),
    )
    kassa = models.ForeignKey(Kassa, on_delete=models.SET_NULL, null=True, blank=True , related_name='kassa_transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Client valyutasi bo‘yicha
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)  # Client valyutasi
    cource = models.ForeignKey(Cource, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    amount_in_kassa_currency = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # kassadan chiqadigan miqdor
    related_client = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True)

    previous_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Kassa oldingi balans
    new_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)       # Kassa yangi balans

    # 🔹 Client balansi ham yozamiz
    client_previous_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    client_new_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    client_currency_code = models.CharField(max_length=5, blank=True, null=True)
    kassa_currency_code = models.CharField(max_length=5, blank=True, null=True)

    is_convert = models.BooleanField(
        default=False,
        choices=[
            (True, "pulni holati ozgargan"),
            (False, "pulni holati ozgarmagan"),
        ]
    )
    @property
    def kassa_name(self):
        return self.kassa.name
    
    def save(self, *args, **kwargs):
        # ✅ Kassa valyutasi
        if self.kassa and self.kassa.currency:
            self.kassa_currency_code = self.kassa.currency.code

        # ✅ Client valyutasi
        if self.currency:
            self.client_currency_code = self.currency.code

        # ✅ Client balansi olish (shu valyutada)
        if self.related_client and self.currency:
            client_balance = self.related_client.balances.filter(currency=self.currency).first()
            if client_balance:
                self.client_previous_balance = client_balance.amount
                # if self.transaction_type == "expense":
                    # self.client_new_balance = client_balance.amount - self.amount
                # if self.transaction_type == "income" :
                    # self.client_new_balance = client_balance.amount - self.amount
        super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Kassa o'tkazmasi"
        verbose_name_plural = "Kassa o'tkazmalari"

# Mijoz modeli
class Client(models.Model):
    CLIENT_TYPES = (
        ("supplier", "taminotchi"),
        ("customer", "mijoz"),
    )
    
    telegram_id = models.PositiveBigIntegerField( blank=True, null=True)
    name = models.CharField(max_length=55)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=13)
    client_type = models.CharField(max_length=15, choices=CLIENT_TYPES, default="customer")
    
    def __str__(self):
        return self.name

    def get_balance_str(self):
        balances = self.balances.all()
        balance_text = ""
        for balance in balances:
            balance_text += f"{balance.amount} {balance.currency.code}\n"
        return balance_text.strip()
    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"
    
# Mijoz balansi modeli
class ClientBalance(models.Model):
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True , related_name='balances')
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['client', 'currency']
        verbose_name = "Mijoz balansi"
        verbose_name_plural = "Mijoz balanslari"
    
    def __str__(self):
        return f"{self.client.name} - {self.amount} {self.currency.code}"


class Category(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Harajat Kategoriya"
        verbose_name_plural = "Harajat Kategoriyalar"

# Xarajatlar modeli
class Cost(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,related_name='costs')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    date = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    kassa = models.ForeignKey(Kassa, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')  # related_name qo'shildi
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='cost_user')  # related_name qo'shildi
    
    def save(self, *args, **kwargs):
        if self.kassa:
            self.kassa.balance -= self.amount
            self.kassa.save()
        super().save(*args, **kwargs)


# Mahsulot aralashmagan 
class ProductNotMixed(models.Model):
    MEASUREMENT_UNITS = (
        ('kg', 'Kilogramm'),
        ('g', 'Gramm'),
        ('pcs', 'Dona'),
    )
    
    name = models.CharField(max_length=55)
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0) 
    unit = models.CharField(max_length=10, choices=MEASUREMENT_UNITS, default='pcs')
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.name} : {self.quantity} :{self.unit}"
    class Meta:
        verbose_name = "Aralashmagan mahsulot"
        verbose_name_plural = "Aralashmagan mahsulotlar"
        
    
class Income(models.Model):
    component = models.ForeignKey(ProductNotMixed, on_delete=models.SET_NULL, null=True, blank=True , related_name="incomes")
    quantity = models.FloatField(default=0)   # qancha kirim qilingan
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # bir dona yoki kg narxi
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)  # qaysi valyutada
    date = models.DateTimeField(auto_now_add=True)  # kirim sanasi
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True )  # kim kirim qildi
    client = models.ForeignKey(Client , on_delete=models.SET_NULL, null=True, blank=True)
    cource = models.CharField(max_length=15,default=0)
    def __str__(self):
        return f"{self.component.name} - {self.quantity} {self.component.unit} kirim qilindi"

    @property
    def currency_(self):
        return f"{self.currency.code}"
    
    @property
    def total_sum(self):
        """Jami qiymat"""
        return Decimal(self.quantity )*Decimal (self.price)

    def save(self, *args, **kwargs):
        if self.pk is None:

            self.component.quantity += Decimal(self.quantity)
            self.component.save()
            self.cource = Cource.objects.last().cource
            if self.client:
                balance, created = ClientBalance.objects.get_or_create(
                    client=self.client,
                    currency=self.currency,
                    # defaults={"amount": 0}
                )
                # Agar cource kurs sifatida ishlatilsa, summani konvertatsiya qilib qo‘shish mumkin
                # if self.cource and str(self.cource).isdigit():
                #     balance.amount += self.total_sum * float(self.cource)
                # else:
                if balance.amount >= 0:
                    balance.amount += self.total_sum
                else:
                    balance.amount -= self.total_sum
            
                balance.save()

        super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Mahsulot Kirim"
        verbose_name_plural = "Mahsulot Kirimlar"
    

class ProductPrice(models.Model):
    name = models.CharField(max_length=55)
    components = models.JSONField(default=list)  # [{"id": 1, "quantity": 2}, {"id": 3, "quantity": 0.5}]
    benefit = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Foyda foizi
    selling_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    salary = models.DecimalField(max_digits=15, decimal_places=2, default=0)    
    total_cost_usd = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost_uzs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def calculate_total_cost(self):
        total_uzs = Decimal(0)
        total_usd = Decimal(0)
        rate = Cource.objects.last()  
        kurs = Decimal(rate.cource)

        for comp in self.components:
            try:
                product = ProductNotMixed.objects.get(id=comp["id"])
                quantity = Decimal(str(comp["quantity"]))

                if product.unit == "kg":
                    real_qty = quantity
                elif product.unit == "g":
                    real_qty = quantity / Decimal("1000")
                else:
                    real_qty = quantity  

                price = product.price * real_qty

                if product.currency.code == "USD":
                    total_usd += price
                    total_uzs += price * kurs
                else:  # UZS
                    total_uzs += price
                    total_usd += price / kurs

            except ProductNotMixed.DoesNotExist:
                continue

        # 💰 endi salary ham qo‘shamiz
        total_uzs += self.salary
        total_usd += self.salary / kurs

        self.total_cost_usd = total_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.total_cost_uzs = total_uzs.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return self.total_cost_usd, self.total_cost_uzs
    
    def save(self, *args, **kwargs):
        self.calculate_total_cost()
        
        super().save(*args, **kwargs)
        Product.objects.get_or_create(
            product_price=self,
            defaults={"quantity": 0}
        )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Mahsulot Narxi"
        verbose_name_plural = "Mahsulot Narxlari"


@receiver(post_save, sender=ProductNotMixed)
def update_product_price_on_product_change(sender, instance, **kwargs):
    product_prices = []
    for pp in ProductPrice.objects.all():
        for comp in pp.components:
            if comp.get("id") == instance.id:   
                product_prices.append(pp)
                break
    for pp in product_prices:
        pp.save()


class Product(models.Model):
    product_price = models.ForeignKey(ProductPrice, on_delete=models.SET_NULL, null=True, blank=True , related_name='component_items')
    quantity = models.FloatField(default=0)
    
    @property
    def total_cost(self):
        return Decimal(self.product_price.selling_price )* Decimal( self.quantity)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

# Mahsulotlar  Ishlab chiqarish 
class Production(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True , related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    summa = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True )
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.summa = Decimal(self.quantity) * Decimal(self.product.product_price.salary)
            self.product.quantity += self.quantity
            self.product.save()
            balans, created = Balans.objects.get_or_create(user=self.user)
            balans.balans += Decimal(self.quantity) * Decimal(self.product.product_price.salary)
            balans.save()
            
            for comp in self.product.product_price.components:  # [{"id": 1, "quantity": 2}, ...]
                try:
                    product = ProductNotMixed.objects.get(id=comp["id"])
                    required_qty = Decimal(str(comp["quantity"])) * Decimal(self.quantity)
                    product.quantity -= required_qty
                    product.save()
                except ProductNotMixed.DoesNotExist:
                    continue
        super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Mahsulot Ishlab chiqarish"
        verbose_name_plural = "Mahsulotlar Ishlab chiqarish"
    
    
# Buyurtma modeli
class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'Kutilmoqda'),
        ('shipped', 'Yuborilgan'),
        ('delivered', 'Yetkazib berilgan'),
        ('cancelled', 'Bekor qilingan'),
    )
    
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True , related_name='orders')
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=ORDER_STATUS, default='delivered')
    description = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    base_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='base_orders')
    base_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    @property
    def total_sum(self):
        summa = self.items.all()
        total = sum(item.total_price for item in summa)
        return total

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
    
    
    
# Buyurtma elementlari
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True , related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True )
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price

    class Meta:
        verbose_name = "Buyurtma elementi"
        verbose_name_plural = "Buyurtma elementlari"
    def save(self, *args, **kwargs):
        from datetime import date
        today =  date.today()
        first_day_of_month = today.replace(day=1)
        benefit, created = Benefit.objects.get_or_create(date=first_day_of_month)
        benefit_value = Decimal(self.unit_price) - Decimal(self.product.product_price.benefit) 
        benefit.percentage += Decimal(self.quantity) * benefit_value
        benefit.save()
        super().save(*args, **kwargs)

class Transfer(models.Model):
    from_kassa = models.ForeignKey(Kassa, on_delete=models.SET_NULL, null=True, blank=True , related_name='transfers_out')
    to_kassa = models.ForeignKey(Kassa, on_delete=models.SET_NULL, null=True, blank=True
    , related_name='transfers_in')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    # cource = models.ForeignKey(Cource, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True )

    class  Meta:
        verbose_name = "Kassa o'tkazmasi"
        verbose_name_plural = "Kassa o'tkazmalari"