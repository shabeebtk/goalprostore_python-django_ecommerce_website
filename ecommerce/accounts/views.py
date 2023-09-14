from django.shortcuts import render, redirect
from products.views import home
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.cache import never_cache
import random, math
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password 
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash
from accounts.models import CustomUser
from django.conf import settings
from django.contrib import messages
from datetime import datetime
from accounts.models import User_address
from orders.models import order_address, order_items, orders, Coupon_applied_users, Coupons, wallet_transaction, user_wallet, order_cancellation_message
from accounts.decorators import active_non_superuser_required
from django.utils import timezone
from products.models import Stock, product_cart
from django.db.models import Count, Sum
from django.urls import reverse
# pdf
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os

# user signup 
@never_cache
def user_signup(request):
    if request.user.is_authenticated and request.user.is_superuser == False:
        return redirect(home)
    
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        request.session['firstname'] = firstname
        request.session['lastname'] = lastname
        request.session['email'] = email
        request.session['phone'] = phone
        request.session['password'] = password
       
        if password is not None and password == confirm_password:
            if CustomUser.objects.filter(email = email).exists():
                error = 'email already registered'
                return render(request, 'user_register.html', {'error':error})
            elif CustomUser.objects.filter(phone = phone).exists():
                error = 'phone already registered'
                return render(request, 'user_register.html', {'error':error})
            else:
                sent_otp(request)
                return render(request, 'email_otp.html', {'user_email':email})
    return render(request, 'user_register.html')

def sent_otp(request):
    digits = "0123456789"
    OTP = ""
    for i in range(4) :
        OTP += digits[math.floor(random.random() * 10)]
    request.session['otp'] = OTP
    subject = 'Goal pro OTP verification'
    message = f'you OTP is {OTP} to confirm your email'
    #send_mail(subject, message, settings.EMAIL_HOST_USER, [request.session['email']], fail_silently=False)
    return render(request, 'email_otp.html')

def email_otp_verification(request):
    if request.method == 'POST':
        email_otp = request.POST.get('email_otp')
    if email_otp == request.session.get('otp'):
        user = CustomUser.objects.create_user(first_name = request.session['firstname'], 
                                                last_name = request.session['lastname'],
                                                email = request.session['email'],
                                                phone = request.session['phone'],
                                                password = request.session['password'])
        user.set_password(request.session['password'])
        user.email_verified = True
        user.save()
        wallet = user_wallet.objects.create(user = user, balance=0)
        wallet.save()
        login(request, user)
        return redirect(home)
    else:
        return render(request, 'email_otp.html')


# user signin 
@never_cache
def user_signin(request):
    if request.user.is_authenticated and request.user.is_superuser == False:
        return redirect(home)
    
    if request.method == 'POST':
        user_email = request.POST['user_email']
        user_password = request.POST['user_password']
        
        user =  authenticate(email=user_email, password=user_password)
        if user is not None and user.is_superuser == False:
            login(request, user)
            return redirect(home)
        else:
            error = 'invalid details'
            return render(request, 'user_signin.html', {'error':error})
    return render(request, 'user_signin.html')

def otp_generator():
    digits = "0123456789"
    OTP = ""
    for i in range(4) :
        OTP += digits[math.floor(random.random() * 10)]
    return OTP

def forgot_password(request):
    if request.method == 'POST':
        user_email = request.POST.get('user_email')
        request.session['user_email'] = user_email
        email_exists = CustomUser.objects.filter(email = user_email).exists()
        if user_email is not None and email_exists:
            otp = otp_generator()
            request.session['otp'] = otp
            subject = 'Goal pro OTP verification'
            message = f'confirm your email {otp} to change password'
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user_email], fail_silently=False)
            return redirect(confirm_otp)
        else:
            email_invalid = 'invalid email'
            return render(request, 'forgot_password.html', {'email_invalid':email_invalid})
    return render(request, 'forgot_password.html')

@never_cache
def confirm_otp(request):
    if request.method == 'POST':
        email_otp = request.POST.get('email_otp')
        if len(email_otp) > 1 and email_otp == request.session['otp']:
            return redirect(change_password)
        else:
            otp_error = 'invalid otp'
            return render(request, 'confirm_otp.html', {'otp_error': otp_error, 'user_email': request.session['user_email']})
    return render(request, 'confirm_otp.html', {'user_email': request.session['user_email'] })

@never_cache
def change_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')
    
        if len(new_password) > 3 and new_password == confirm_new_password:
            user = CustomUser.objects.get(email = request.session['user_email'])
            user.password = new_password
            user.set_password(new_password)
            user.save()
            return redirect(user_signin)
        else:
            new_password_error = 'confirm your password'
            return render(request, 'change_password.html', {'new_password_error': new_password_error})
    return render(request, 'change_password.html')

# user logout 
@active_non_superuser_required
def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('user_signin')

@active_non_superuser_required
def user_profile(request):
    user = CustomUser.objects.get(email = request.user)
    cart_count = product_cart.objects.filter(user=request.user).aggregate(count = Count('user'))

    return render(request, 'user_dashboard.html', {'user_logout': user.first_name, 'user':user, 'cart_count':cart_count['count']})

@active_non_superuser_required
def user_address(request):
    user = CustomUser.objects.get(email = request.user)
    all_address = User_address.objects.filter(user = user)
    return render(request, 'user_address.html', {'all_address' : all_address})

@active_non_superuser_required
def delete_address(request, address_id):
    address = User_address.objects.get(id = address_id)
    address.delete()
    return redirect(user_address)

@active_non_superuser_required
def edit_address(request, address_id):
    address = User_address.objects.get(id = address_id)
    if request.method == 'POST':
        address_name = request.POST['address_name']
        address_phone = request.POST['address_phone']
        address_details = request.POST['address']
        address_place = request.POST['address_place']
        address_pincode = request.POST['address_pincode']
        address_city = request.POST['address_city']
        address_state = request.POST['address_state']
        address_landmark = request.POST['address_landmark']
        
        if address_name and address_phone and address_details and address_place and address_place and address_pincode and address_city and address_state:
            address.name = address_name
            address.phone = address_phone
            address.address = address_details
            address.place = address_place
            address.pincode = address_pincode
            address.city = address_city
            address.state = address.state
            address.landmark = address_landmark
            address.save()
            return redirect(user_address)
        else:
            address_error = 'fill all fields'
            render(request, 'edit_address.html', {'edit_address' : address, 'address_error':address_error})
    return render(request, 'edit_address.html', {'edit_address' : address})

def add_address(request):
    user = CustomUser.objects.get(email=request.user)
    if request.method == 'POST':
        address_name = request.POST['address_name']
        address_phone = request.POST['address_phone']
        address_details = request.POST['address']
        address_place = request.POST['address_place']
        address_pincode = request.POST['address_pincode']
        address_city = request.POST['address_city']
        address_state = request.POST['address_state']
        address_landmark = request.POST['address_landmark']
        
        if address_name and address_phone and address_details and address_place and address_place and address_pincode and address_city and address_state:
            address = User_address.objects.create(user=user, name=address_name, phone=address_phone, address=address_details, pincode=address_pincode, state=address_state, city=address_city, place=address_place, landmark=address_landmark)
            address.save()
            return redirect(user_address)
        else:
            address_error = 'fill all fields'
            return redirect(user_address)
  


# user all order details 
@active_non_superuser_required
def user_orders(request):
    user = CustomUser.objects.get(email = request.user)
    user_order = orders.objects.filter(user=user).order_by('-order_date')
    context = {
        'user_orders': user_order
    }
    return render(request, 'orders/user_orders.html', context)


@active_non_superuser_required
def user_order_details(request, order_id):
    order = orders.objects.get(id = order_id)
    address = order_address.objects.get(order_id = order_id)
    sub_total = order_items.objects.filter(order_no=order).aggregate(total_sum = Sum('total_price'))
    coupon_discount = 0
    if order.coupon_applied == True:
        coupon = Coupons.objects.get(coupon_code = order.discount)
        if coupon.discount_type == 'amount':
            coupon_discount = coupon.discount
        elif coupon.discount_type == 'percentage':
            coupon_discount = (coupon.discount / 100) * float(sub_total['total_sum'])
            if coupon_discount > coupon.maximum_discount:
                coupon_discount = coupon.maximum_discount

    return_date = order.return_date
    time_now = datetime.now()
    return_date_with_time = False
    if return_date != None:
        return_date_with_time = datetime.combine(return_date, datetime.min.time())
   
    context = {
        'order':order,
        'order_address': address,
        'time_now' : time_now,
        'return_expire_date': return_date_with_time,
        'sub_total': sub_total['total_sum'],
        'coupon_discount':coupon_discount
    }
    return render(request, 'orders/user_order_details.html', context)

@active_non_superuser_required
def cancel_order(request, order_id):
    order_user = CustomUser.objects.get(email = request.user)
    order = orders.objects.get(id = order_id)
    order_products = order_items.objects.filter(order_no_id = order)
    order.status = 'cancelled'
    order.status_modified_date = datetime.now()
    for item in order_products:
        stock = Stock.objects.get(product = item.product, size = item.size)
        stock.quantity += item.quantity
        stock.save()
        
    # reason of cancellation 
    if request.method == 'POST':
        user_message = request.POST['cancel_messsage']
        user_reason = request.POST['cancel_reason']
        order_status = 'cancel'
        cancel_message = order_cancellation_message.objects.create(order_id = order, message=user_message, reason=user_reason, order_status=order_status)
        cancel_message.save()

    if order.payment_method == 'razorpay' or order.payment_method == 'wallet':
            if user_wallet.objects.filter(user=order_user).exists():
                wallet = user_wallet.objects.get(user = order_user)
                refund_cash = order.total_amount
                wallet.balance = wallet.balance + refund_cash
                wallet_history = wallet_transaction.objects.create(user=order_user, order_id=order, amount=refund_cash, status='credit')
                wallet.save()
                wallet_history.save()
            else:
                wallet = user_wallet.objects.create(user = order_user, balance=0)
                refund_cash = order.total_amount
                wallet.balance += refund_cash
                wallet_history = wallet_transaction.objects.create(user=order_user, order_id=order, amount=refund_cash, status='credit') 
                wallet.save()
                wallet_history.save()        
    order.save()
    return redirect(user_order_details, order_id)

@active_non_superuser_required
def order_return(request, order_id):
    order_user = CustomUser.objects.get(email = request.user)
    order = orders.objects.get(id = order_id)
   
    return_date = order.return_date
    time_now = datetime.now()
    return_date_with_time = datetime.combine(return_date, datetime.min.time())
    
    if order.status == 'delivered' and time_now < return_date_with_time:
        order_products = order_items.objects.filter(order_no_id = order)
        order.status = 'returned'
        order.return_date = datetime.now()
        for item in order_products:
            stock = Stock.objects.get(product = item.product, size = item.size)
            stock.quantity += item.quantity
            stock.save()
            order.save()
            
        # reason of cancellation 
        if request.method == 'POST':
            user_message = request.POST['return_messsage']
            user_reason = request.POST['return_reason']
            order_status = 'retur'
            cancel_message = order_cancellation_message.objects.create(order_id = order, message=user_message, reason=user_reason, order_status=order_status)
            cancel_message.save()
            
        if user_wallet.objects.filter(user=order_user).exists():
            wallet = user_wallet.objects.get(user = order_user)
            refund_cash = order.total_amount
            wallet.balance = wallet.balance + refund_cash
            wallet_history = wallet_transaction.objects.create(user=order_user, order_id=order, amount=refund_cash, status='credit')
            wallet.save()
            wallet_history.save()
        else:
            wallet = user_wallet.objects.create(user = order_user, balance=0)
            refund_cash = order.total_amount
            wallet.balance += refund_cash
            wallet_history = wallet_transaction.objects.create(user=order_user, order_id=order, amount=refund_cash, status='credit') 
            wallet.save()
            wallet_history.save()
    return redirect(user_order_details, order_id)

# pdf 
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)#, link_callback=fetch_resources)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def GenerateInvoice(request, order_id):
    user = CustomUser.objects.get(email = request.user)
    order = orders.objects.get(id = order_id)
    ordered_items = order_items.objects.filter(order_no = order)
    sub_total = order_items.objects.filter(order_no=order).aggregate(total_sum = Sum('total_price'))
    sub_total1 = float(sub_total['total_sum'])
    discount = sub_total1 - float(order.total_amount)

    if order_address.objects.filter(order_id = order).exists():
        ordered_address = order_address.objects.get(order_id=order)
    else:
        ordered_address = "None"
 
    data = {
            'order':order,
            'order_id': order.order_id,
            'user': user.first_name + ' ' +  user.last_name,
            'user_email': 'email',
            'ordered_items':ordered_items,
            'address': ordered_address,
            'sub_total': sub_total1,
            'discount':discount     
        }
    
    pdf = render_to_pdf('orders/invoice.html', data)
    # return HttpResponse(pdf, content_type='application/pdf')
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Goalpro{ order.order_id }.pdf"
        content = "inline; filename='%s'" %(filename)
        #download = request.GET.get("download")
        #if download:
        content = "attachment; filename=%s" %(filename)
        response['Content-Disposition'] = content
        return response
    return redirect(user_order_details, order_id)

# user_personal_details

@active_non_superuser_required
def user_personal_details(request):
    user = CustomUser.objects.get(email = request.user)
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        if user.first_name != firstname:    
            user.first_name = firstname
        
        if user.last_name != lastname:    
            user.last_name = lastname
        
        user.save()
        if user.email != email and len(email) > 3:
            if CustomUser.objects.filter(email = email).exists():
                error = 'email already registered'
                return render(request, 'user_personal_details/user_personal_details.html', {'error':error})  
            else: 
                request.session['new_email'] = email
                request.session['new_email_otp'] = otp_generator()
                request.session['old_email_otp'] = otp_generator()
                
                get_new_email_otp = request.session['new_email_otp']
                get_old_email_otp = request.session['old_email_otp']
                
                # new email 
                new_email_subject = 'Goal pro OTP verification'
                new_email_message = f'confirm your email {get_new_email_otp} to change email'
                send_mail(new_email_subject, new_email_message, settings.EMAIL_HOST_USER, [email], fail_silently=False)
                
                # old email 
                old_email_subject = 'Goal pro OTP verification'
                old_email_message = f'confirm your email {get_old_email_otp} to change email'
                send_mail(old_email_subject, old_email_message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
                return redirect(user_change_email)
    return render(request, 'user_personal_details/user_personal_details.html', {'user':user})

@active_non_superuser_required
def user_change_email(request):
    user = CustomUser.objects.get(email = request.user)
    new_email = request.session['new_email']
    old_email = request.user
    get_new_email_otp = request.session['new_email_otp']
    get_old_email_otp = request.session['old_email_otp']

    if request.method == 'POST':
        new_email_otp = request.POST.get('new_email_otp')
        old_email_otp = request.POST.get('old_email_otp')
        
        if new_email_otp == get_new_email_otp and get_old_email_otp == old_email_otp:
            user.email = new_email
            user.email_verified = True
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'email changed successfully')
            return redirect(user_personal_details)
        else:
            otp_error = 'OTP verification failed'
            return render(request, 'user_personal_details/user_confirm_email.html', {'new_email': new_email, 'old_email':old_email, 'otp_error':otp_error})
    return render(request, 'user_personal_details/user_confirm_email.html', {'new_email': new_email, 'old_email':old_email})

@active_non_superuser_required
def user_password_reset(request):
    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_new_password = request.POST['confirm_new_password']
        
        user = CustomUser.objects.get(email = request.user)
        if old_password and new_password and confirm_new_password:
            if len(new_password) < 5:
                len_error = 'password length too short'
                return render(request, 'user_personal_details/reset_password.html', {'len_error': len_error})
            if new_password == confirm_new_password:
                if check_password(old_password, user.password):
                    user.password = new_password
                    user.set_password(new_password)
                    user.save()
                    login(request, user)
                    return redirect(user_password_reset)
                else:
                    error = 'Incorrect old password'
                    return render(request, 'user_personal_details/reset_password.html', {'error': error})
            else:
                confirm_error = 'confirm password must be same'
                return render(request, 'user_personal_details/reset_password.html', {'confirm_error': confirm_error}) 
    return render(request, 'user_personal_details/reset_password.html') 

@active_non_superuser_required

def user_wallet_balance(request):
    user = CustomUser.objects.get(email = request.user)
    if user_wallet.objects.filter(user=user).exists():   
        wallet_balance = user_wallet.objects.get(user=user)
        transactions = wallet_transaction.objects.filter(user=user).order_by('-date')
        
        context = {
            'wallet_balance':wallet_balance,
            'all_transactions': transactions
        }
    return render(request, 'user_wallet.html', context)



