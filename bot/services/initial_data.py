import os
import django
from asgiref.sync import sync_to_async

# Django ni sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Admin.settings')
django.setup()

from main.models import Currency, Kassa


# @sync_to_async
# def create_initial_data():
    # Currency ma'lumotlarini yaratish
currencies = [
        {'code': 'UZS', 'name': 'Oʻzbek soʻmi', 'symbol': 'soʻm'},
        {'code': 'USD', 'name': 'AQSH dollari', 'symbol': '$'},
        {'code': 'EUR', 'name': 'Yevro', 'symbol': '€'},
        {'code': 'RUB', 'name': 'Rus rubli', 'symbol': '₽'},
    ]
    
for currency_data in currencies:
        currency, created = Currency.objects.get_or_create(
            code=currency_data['code']
        )
        if created:
            print(f"Yangi valyuta yaratildi: {currency.code}")
    
    # Asosiy kassa yaratish
uzs_currency = Currency.objects.get(code='UZS')
kassa, created = Kassa.objects.get_or_create(
    name='Asosiy Kassa',
    defaults={
        'balance': 0,
        'currency': uzs_currency
    }
)
if created:
    print(f"Yangi kassa yaratildi: {kassa.name}")

# if __name__ == "__main__":
#     create_initial_data()