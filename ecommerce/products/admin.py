from django.contrib import admin
from .models import Products, Brand, Size, Category, product_cart, Stock, Banners
# Register your models here.


admin.site.register(Products)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Size)
admin.site.register(product_cart)
admin.site.register(Stock)
admin.site.register(Banners)