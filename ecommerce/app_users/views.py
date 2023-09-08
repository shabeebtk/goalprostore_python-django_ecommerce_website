from django.shortcuts import render, redirect
from products.views import home
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.cache import never_cache
import random
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password   
# Create your views here.

# @never_cache
# def user_signup(request):
#     if request.user.is_authenticated and request.user.is_superuser == False:
#         return redirect(home)
    
#     if request.method == 'POST':
#         username = request.POST['username']
#         user_email = request.POST['user_email']
#         user_phone = request.POST['user_phone']
#         user_password = request.POST['user_password']
#         user_confirm_password = request.POST.get('user_confirm_password')
#         print(user_confirm_password)
#         print(user_confirm_password)
#         if user_password is not None and user_password == user_confirm_password:
#             user = app_user.objects.create(username=username, email=user_email, phone=user_phone, password=user_password)
#             user.set_password(user_password)
#             user.save()
#             login(request, user)
#             return redirect(home)
#     sent_otp()
#     print("otp",sent_otp()) 
#     return render(request, 'user_register.html')

# def sent_otp():
#     s = ''
#     for x in range(0,4):
#         s+= str(random.randint(0,9))
#     return s


# @never_cache
# def user_signin(request):
#     if request.user.is_authenticated and request.user.is_superuser == False:
#         return redirect(home)
    
#     if request.method == 'POST':
#         username = request.POST['username']
#         user_email = request.POST['user_email']
#         user_password = request.POST['user_password']
        
#         user =  authenticate(username=username, email=user_email, password=user_password)
#         if user is not None and user.is_superuser == False:
#             login(request, user)
#             return redirect(home)
#         else:
#             error = 'invalid details'
#             return render(request, 'user_signin.html', {'error':error})
#     return render(request, 'user_signin.html')


# def user_logout(request):
#     if request.user.is_authenticated:
#         logout(request)
#     return redirect('user_signin')


