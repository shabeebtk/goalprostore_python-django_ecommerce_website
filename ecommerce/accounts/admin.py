from django.contrib import admin
from .models import CustomUser, User_address
# Register your models here.


admin.site.register(CustomUser)
admin.site.register(User_address)

