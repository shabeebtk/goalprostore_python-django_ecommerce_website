from django.urls import path
from . import views

urlpatterns = [
    path('checkout', views.checkout, name="checkout"),
    path('order', views.create_order, name="order"),
    path('order_success', views.order_success, name='order_success'),
    
    path('handlerequest', views.handlerequest, name = 'handlerequest'),
    path('select_address', views.select_address, name = 'select_address'),
    
]
