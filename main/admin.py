from django.contrib import admin
from django.contrib.auth.models import Group
from .models import *
    

admin.site.unregister(Group)
admin.site.register(CustomUser)
admin.site.register(Client)
admin.site.register(Currency)
admin.site.register(Benefit)
admin.site.register(Cource)
admin.site.register(Kassa)
admin.site.register(ClientBalance)
admin.site.register(KassaTransaction)
admin.site.register(ProductNotMixed)
admin.site.register(ProductPrice)
admin.site.register(Product)
admin.site.register(Production)
admin.site.register(Cost)
admin.site.register(Balans)
admin.site.register(BotSettings)
admin.site.register(Transfer)

admin.site.register(Order)
admin.site.register(OrderItem)
