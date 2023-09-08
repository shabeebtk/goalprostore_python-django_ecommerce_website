from django.http import HttpResponse
from django.shortcuts import render, redirect
from products.models import product_cart, Stock
from products.views import products_cart
from accounts.models import CustomUser, User_address
from django.db.models import Count, Sum
from accounts.decorators import active_non_superuser_required
from .models import orders, order_items, order_address, Coupons, Coupon_applied_users, wallet_transaction, user_wallet
from django.views.decorators.cache import never_cache
from products.views import home
from django.conf import settings
from django.http import HttpResponseBadRequest
import datetime
from django.contrib import messages
from django.http import JsonResponse



# razor pay payment integration 
import razorpay
from django.contrib.sites.shortcuts import get_current_site
from .constants import PaymentStatus
from django.views.decorators.csrf import csrf_exempt

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

context = {
    
}
# user side 
@active_non_superuser_required
@never_cache
def checkout(request):
    if request.session.get('order_placed'):
        request.session['order_placed'] = False
        return redirect(order_success)
    cart_items = product_cart.objects.prefetch_related().filter(user = request.user).order_by('created_at')
    if len(cart_items) < 1:
        return redirect(products_cart)
    user = CustomUser.objects.get(email = request.user)
    checkout_items = product_cart.objects.filter(user = user)
    all_address = User_address.objects.filter(user = user)
    cart_total = product_cart.objects.filter(user=request.user).aggregate(total_sum = Sum('total_price'))
    sub_total = product_cart.objects.filter(user=request.user).aggregate(total_sum = Sum('total_price'))
    razorpay_cash = cart_total['total_sum'] * 100
    razorpay_cash = int(razorpay_cash)
    
    public_coupons = Coupons.objects.filter(public_coupon = True)
    # coupon
    coupon_applied = ''
    discount = 0
    request.session['coupon_applied'] = coupon_applied
    coupon_code = request.GET.get('coupon_inp')
    if coupon_code:
        try:
            coupon = Coupons.objects.get(coupon_code=coupon_code, active=True)
            if Coupon_applied_users.objects.filter(coupon = coupon, user = user).exists():
                    messages.warning(request, 'You have already applied this coupon.')
            else:
                if coupon.discount_type == 'amount':
                    if cart_total['total_sum'] < coupon.minimum_amount_required:
                        messages.warning(request, f'minimum amount ₹{coupon.minimum_amount_required} required')
                    else:
                        discount = coupon.discount
                        coupon_applied = coupon.coupon_code
                        request.session['coupon_applied'] = coupon_applied
                        messages.success(request, 'coupon applied')
                        cart_total['total_sum'] -= discount
                        razorpay_cash = int(cart_total['total_sum'] * 100)
                    
                elif coupon.discount_type == 'percentage':
                    cart_total['total_sum'] = float(cart_total['total_sum'])
                    discount = (coupon.discount / 100) * cart_total['total_sum']
                                        
                    if cart_total['total_sum'] < coupon.minimum_amount_required:
                        messages.warning(request, f'minimum amount ₹{coupon.minimum_amount_required} required')
                        
                    elif discount > coupon.maximum_discount:
                        discount = coupon.maximum_discount
                        coupon_applied = coupon.coupon_code
                        cart_total['total_sum'] -= discount
                        razorpay_cash = int(cart_total['total_sum'] * 100) 
                        request.session['coupon_applied'] = coupon_applied
                        messages.success(request, f'maximum amount ₹{coupon.maximum_discount} applied')
                         
                    else:
                        coupon_applied = coupon.coupon_code
                        request.session['coupon_applied'] = coupon_applied
                        messages.success(request, 'coupon applied')
                        cart_total['total_sum'] -= discount
                        razorpay_cash = int(cart_total['total_sum'] * 100)
        except:
            messages.error(request, 'invalid coupon or expired')     
       
    # razorpay
    currency = 'INR'
    amount = razorpay_cash 
    request.session['razorpay_amount'] = amount
    # Create a Razorpay Order
    razorpay_order = razorpay_client.order.create(dict(amount=amount,
                                                       currency=currency,
                                                       payment_capture='0'))
    razorpay_order_id = razorpay_order['id']
    callback_url = '/order/'+'handlerequest'
    
    
    # wallet 
    wallet_balance = 0
    if user_wallet.objects.filter(user=user).exists():   
        wallet_balance = user_wallet.objects.get(user=user)    
   
    
    context = {
        'checkout_items':checkout_items,
        'cart_total': cart_total['total_sum'], 
        'sub_total': sub_total['total_sum'],
        'all_address' : all_address,
        
        'razorpay_order_id': razorpay_order_id,
        'razorpay_merchant_id':settings.RAZORPAY_KEY_ID,
        'razorpay_amount' : amount,
        'currency': currency,
        'callback_url':callback_url,
        
        'coupon_applied' : coupon_applied,
        'public_coupons':public_coupons,
        'discount':discount,
        'wallet_balance':wallet_balance
    }    
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
            
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
            return redirect(checkout)
        else:
            address_error = 'fill all fields'
            return render(request, 'checkout.html', context)
        
    return render(request, 'checkout.html', context)

def select_address(request):
    address_id = request.POST.get('address_id')
    request.session['address_id'] = address_id
    return JsonResponse({'success': True})

@active_non_superuser_required
def create_order(request):
    if request.method == 'POST':
        address_id = request.POST.get('selected_address')        
        payment_method = request.POST.get('payment_method')
        coupon_applied = request.POST.get('coupon_val')


        if len(address_id) < 1 or len(payment_method) < 1:
            return redirect(checkout)
        
        user = CustomUser.objects.get(email = request.user)
        total_amount = product_cart.objects.filter(user=request.user).aggregate(total_sum = Sum('total_price'))

        order = orders.objects.create(user=user, payment_method=payment_method, total_amount=total_amount['total_sum'])

        if payment_method == 'wallet':
            if user_wallet.objects.filter(user=request.user).exists():   
                wallet = user_wallet.objects.get(user=request.user)
                wallet_balance = float(wallet.balance)
                total_amount = float(order.total_amount)
                if wallet_balance < total_amount:
                    order_delete = orders.objects.get(id = order.id)
                    order_delete.delete()
                    return redirect(checkout)
        
        address = User_address.objects.get(id =  address_id)
                
        order_id = orders.objects.get(id = order.id)
        user_cart_products = product_cart.objects.filter(user = user)

     
        address_order = order_address(order_id=order_id, name=address.name, phone=address.phone, address=address.address, pincode=address.pincode, state=address.state, city=address.city, place=address.place, landmark=address.landmark)
        
        if coupon_applied:
                coupon = Coupons.objects.get(coupon_code = coupon_applied)
                order.coupon_applied = coupon.coupon_code
                
                if coupon.discount_type == 'amount':
                    discount = coupon.discount
                    order.total_amount = order.total_amount - discount
                    order.discount = coupon
                    order.coupon_applied = True
                    
                elif coupon.discount_type == 'percentage':
                    discount = (coupon.discount / 100) * float(order.total_amount)
                    if discount > coupon.maximum_discount:
                        discount = coupon.maximum_discount
                        
                    order.total_amount = order.total_amount - discount
                    order.discount = coupon
                    order.coupon_applied = True
                    
        if payment_method == 'wallet':
            if user_wallet.objects.filter(user=user).exists():   
                        wallet = user_wallet.objects.get(user=user)
                        wallet_balance = float(wallet.balance)
                        total_amount = float(order.total_amount)
                        if wallet_balance > total_amount: 
                            wallet.balance = wallet_balance - float(order.total_amount)
                            wallet_history = wallet_transaction.objects.create(user=user, order_id=order, amount=order.total_amount, status='debit')
                            wallet.save()
                            wallet_history.save()  
                        else:
                            order_delete = orders.objects.get(id = order.id)
                            order_delete.delete()
                            return redirect(checkout)
        
        for item in user_cart_products:
            items = order_items(order_no = order_id, product = item.product, quantity=item.quantity, size=item.size, price=item.price, total_price=item.total_price)
            items.save()
            stock = Stock.objects.get(product=item.product, size=item.size)
            stock.quantity -= item.quantity
            stock.save()
                              
        order.save()
        address_order.save()
        
        if order.coupon_applied == True:
            user_coupon_applied = Coupon_applied_users.objects.create(user=user, coupon = coupon, order_id=order)
            user_coupon_applied.save()
            
        user_cart_products.delete()
        request.session['order_placed'] = True
        return redirect(order_success)

@active_non_superuser_required
def order_success(request):
    if request.session['order_placed'] == True or request.session['order_placed'] != None:
        request.session['order_placed'] = False
        return render(request, 'order_success.html')
    else:
        return redirect(products_cart)

@csrf_exempt
def handlerequest(request):
    if request.method == 'POST':
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            coupon_applied = request.session['coupon_applied']
            address_id  = request.session['address_id']
            
            if address_id == '':
                return redirect(checkout)
                        
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
                
            result = razorpay_client.utility.verify_payment_signature(
                params_dict)
            if result is not None:
                amount = request.session['razorpay_amount']
                try:
                    razorpay_client.payment.capture(payment_id, amount)
                    user = CustomUser.objects.get(email = request.user)
                    total_amount = product_cart.objects.filter(user=request.user).aggregate(total_sum = Sum('total_price'))
                    payment_method = 'razorpay'
                    order = orders.objects.create(user=user, payment_method=payment_method, total_amount=total_amount['total_sum'])
                    address = User_address.objects.get(id =  address_id)
                    order_id = orders.objects.get(id = order.id)
                    user_cart_products = product_cart.objects.filter(user = user)
                    order_address.objects.create(order_id=order_id, name=address.name, phone=address.phone, address=address.address, pincode=address.pincode, state=address.state, city=address.city, place=address.place, landmark=address.landmark)
                    
                    if coupon_applied:
                        coupon = Coupons.objects.get(coupon_code = coupon_applied)
                        order.coupon_applied = coupon.coupon_code

                        if coupon.discount_type == 'amount':
                            discount = coupon.discount
                            order.total_amount = order.total_amount - discount
                            order.discount = coupon
                            order.coupon_applied = True

                        elif coupon.discount_type == 'percentage':
                            discount = (coupon.discount / 100) * float(order.total_amount)
                            if discount > coupon.maximum_discount:
                                discount = coupon.maximum_discount

                            order.total_amount = order.total_amount - discount
                            order.discount = coupon
                            order.coupon_applied = True
                            
                    for item in user_cart_products:
                        items = order_items(order_no = order_id, product = item.product, quantity=item.quantity, size=item.size, price=item.price, total_price=item.total_price)
                        items.save()
                        stock = Stock.objects.get(product=item.product, size=item.size)
                        stock.quantity -= item.quantity
                        stock.save()
                            
                    order.save()
                    if order.coupon_applied == True:
                        user_coupon_applied = Coupon_applied_users.objects.create(user=user, coupon = coupon, order_id=order)
                        user_coupon_applied.save()
                    user_cart_products.delete()
                    request.session['order_placed'] = True
                    return redirect(order_success)
                except:
                    return render(request, 'payment_failed.html')
                
            else:
                return render(request, 'payment_failed.html')
        except:
            return HttpResponse("404 not found")
    else:
        return HttpResponseBadRequest()


    

