from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop', views.shop, name='shop'),
    path('product_profile/<product_id>/', views.product_profile, name='product_profile'),
    path('cart', views.products_cart, name='cart'),
    path('add_to_cart/<product_id>', views.add_to_cart, name='add_to_cart'),
    path('remove_cart_item/<item_id>', views.remove_cart_item, name='remove_cart_item'),
    path('increment/<cart_id>/<quantity>', views.increment_quantity, name='increment_quantity'),
    path('decrement/<cart_id>/<quantity>', views.decrement_quantity, name='decrement_quantity'),
    path('shop/<str:sort_order>', views.shop, name='shop_sorted'),
    path('shop/<str:sort_order>', views.shop, name='shop_sorted')
 ]