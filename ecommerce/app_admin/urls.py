from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_home, name='admin_home'),
    path('signin', views.admin_signin, name='admin_signin'),
    path('logout', views.admin_logout, name="admin_logout"),
    
    path('manage_users', views.manage_users, name='manage_users'),
    path('block_user/<user_id>', views.block_users, name='block_user'),
    path('unblock_user/<user_id>', views.unblock_users, name='unblock_user'),
    
    path('manage_products', views.manage_products, name='manage_products'),
    path('add_product', views.add_products, name='add_product'),
    path('product_unlist/<product_id>', views.product_unlist, name= 'product_unlist'),
    path('product_show/<product_id>', views.product_show, name= 'product_show'),
    path('edit_product/<product_id>', views.edit_product, name='edit_product'),
    
    path('manage_category', views.manage_category, name= 'manage_category'),
    path('add_category', views.add_category, name='add_category'),
    path('delete_category/<category_id>', views.delete_category, name='delete_category'),
    path('edit_category/<category_id>', views.edit_category, name='edit_category'),
    
    path('manage_brands', views.manage_brands, name='manage_brands'),
    path('add_brands', views.add_brands, name='add_brands'),
    path('edit_brands/<brand_id>', views.edit_brands, name='edit_brands'),
    path('delete_brands/<brand_id>', views.delete_brands, name='delete_brand'),
    
    path('manage_orders', views.manage_orders, name='manage_orders'),
    path('order_details/<order_id>', views.order_details, name='order_details'),
    path('download_sales_report', views.download_sales_report, name='download_sales_report'),
    
    
    path('crop', views.crop, name='crop'),
    path('upload_image/', views.upload_image, name='upload_image'), 
       
    path('coupons', views.manage_coupons, name='manage_coupons'),    
    path('add_coupon', views.add_coupon, name='add_coupon'),    
    path('edit_coupon/<coupon_id>', views.edit_coupon, name='edit_coupon'), 
       
    path('manage_banners', views.manage_banners, name='manage_banners'),   
    path('add_banner', views.add_banner, name='add_banner'),   
    path('edit_banner/<banner_id>', views.edit_banner, name='edit_banner'),   
    path('show_unlist_banner', views.show_unlist_banner, name='show_unlist_banner'),   
     
    
]

