from django.contrib import admin
from .models import orders, order_items, order_address, Coupons, Coupon_applied_users, wallet_transaction, user_wallet, order_cancellation_message
# Register your models here.

admin.site.register(orders)
admin.site.register(order_items)
admin.site.register(order_address)
admin.site.register(Coupons)
admin.site.register(Coupon_applied_users)
admin.site.register(wallet_transaction)
admin.site.register(user_wallet)
admin.site.register(order_cancellation_message)
