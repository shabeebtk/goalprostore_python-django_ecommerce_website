from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.user_signup, name = 'user_signup'),
    path('signin', views.user_signin, name='user_signin'),
    path('user_logout', views.user_logout, name='user_logout'),
    path('email_otp', views.sent_otp, name='email_otp'),
    path('email_otp_verification', views.email_otp_verification, name='email_otp_verification'),
    path('forgot_password', views.forgot_password, name='forgot_password'),
    path('change_password', views.change_password, name='change_password'),
    path('confirm_otp', views.confirm_otp, name='confirm_otp'),
    path('user_dashboard', views.user_profile, name='user_dashboard'),
    
    path('user_address', views.user_address, name='user_address'),
    path('add_address', views.add_address, name='add_address'),
    path('address_delete/<address_id>', views.delete_address, name='address_delete'),
    path('edit_address/<address_id>', views.edit_address, name='edit_address'),
    
    path('user_orders', views.user_orders, name='user_orders'),
    path('user_order_details/<order_id>', views.user_order_details, name="user_order_details"),
    path('user_order_cancel/<order_id>', views.cancel_order, name="cancel_order"),
    
    path('personal_details', views.user_personal_details, name="user_personal_details"),
    path('order_return/<order_id>', views.order_return, name="order_return"),
    path('user_email_change', views.user_change_email, name="user_email_change"),
    path('user_password_reset', views.user_password_reset, name="user_password_reset"),
    
    path('user_wallet', views.user_wallet_balance, name="user_wallet"),
    
    path('download_invoice/<order_id>', views.GenerateInvoice, name='download_invoice')
    
    
]

