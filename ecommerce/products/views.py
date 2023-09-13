from django.shortcuts import render, redirect, get_object_or_404
from .models import Products, Size, Brand, Category, product_cart, Stock, Banners
from django.views.decorators.cache import never_cache
from accounts.models import CustomUser
from django.db.models import Count, Sum
from django.http import JsonResponse
from accounts.decorators import active_non_superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F

# Create your views here.
def home(request):
    new_products = Products.objects.prefetch_related().filter(status = True).order_by('-id')[:4]
    print(new_products)
    all_products = Products.objects.prefetch_related().filter(status = True)[:8]
    all_categories = Category.objects.all()
    if request.user.is_authenticated:   
        cart_count = product_cart.objects.filter(user=request.user).aggregate(count = Count('user'))
        cart_count = cart_count['count']
    else:
        cart_count = 0
    all_brands = Brand.objects.all()
    banner = Banners.objects.filter(active=True)
    check_user_signin = request.user.is_authenticated
    
    context = {
        'cart_count':cart_count,
        'all_brands': all_brands,
        'new_products': new_products,
        'all_products' : all_products,
        'all_categories':all_categories,
        'banners':banner,
        'check_user_signin':check_user_signin
    }   
    return render(request, 'home.html', context)

def shop(request, sort_order=None, search=False):
    # all_products = Products.objects.prefetch_related().filter(status = True)
    if request.user.is_authenticated:   
        cart_count = product_cart.objects.filter(user=request.user).aggregate(count = Count('user'))
        cart_count = cart_count['count']
    else:
        cart_count = 0
        
    check_user_signin = request.user.is_authenticated
    selected_brands = request.GET.getlist('brands')
    selected_categories = request.GET.getlist('category')
    products_queryset = Products.objects.prefetch_related().filter(status=True)
    search_products = request.GET.get('search')
    price_range = request.GET.get('price_range')
    selected_gender = request.GET.get('gender')
    
    if search_products:
        search_items = search_products.split()
        q_objects = Q()
        
        for item in search_items:
            q_objects |=  Q(product_name__icontains = item) | Q(category__category_name__icontains = item) | Q(brand__brand_name__icontains = item)
            
        search = Products.objects.filter(q_objects, status=True)
    else:
        search = []
        
           
    if selected_brands:
        selected_brands_objects = Brand.objects.filter(id__in=selected_brands)
        products_queryset = products_queryset.filter(brand__in=selected_brands_objects)
        
    if selected_categories:
        selected_category_objects = Category.objects.filter(id__in=selected_categories)
        products_queryset = products_queryset.filter(category__in=selected_category_objects)
        
    if selected_gender:
        products_queryset = Products.objects.filter(gender = selected_gender)
        
    if price_range:
        if price_range == 'under_500':
            products_queryset = products_queryset.filter(price__lt=500)
        elif price_range == '500-1000':
            products_queryset = products_queryset.filter(price__gte=500, price__lt=1000)
        elif price_range == '1000-1500':
            products_queryset = products_queryset.filter(price__gte=1000, price__lt=1500)
        elif price_range == '1500-2000':
            products_queryset = products_queryset.filter(price__gte=1500, price__lt=2000)
        elif price_range == 'greater_than_2000':
            products_queryset = products_queryset.filter(price__gte=2000)
    
    if sort_order == 'low_to_high':
        products_queryset = products_queryset.order_by('price')
        
    if sort_order == 'high_to_low':
        products_queryset = products_queryset.order_by('-price')
        
    products_paginator = Paginator(products_queryset, 6)
    page = request.GET.get('page')
    all_products = products_paginator.get_page(page)
        
    all_categories = Category.objects.all()
    all_brands = Brand.objects.all()
        
    context = {
        'all_products' : all_products,
        'cart_count':cart_count, 
        'all_categories':all_categories,
        'all_brands':all_brands,
        'selected_categories': selected_categories,
        'selected_brands':selected_brands,
        'search' : search,
        'search_product': search_products,
        'check_user_signin':check_user_signin
    }
    return render(request, 'shop.html', context)   

# recently viewed products
def recently_viewed( request, post_id ):
    if not "recently_viewed" in request.session:
        request.session["recently_viewed"] = []
        request.session["recently_viewed"].append(post_id)
    else:
        if post_id in request.session["recently_viewed"]:
            request.session["recently_viewed"].remove(post_id)
        request.session["recently_viewed"].insert(0, post_id)
        if len(request.session["recently_viewed"]) > 5:
            request.session["recently_viewed"].pop()
    print(request.session["recently_viewed"])
    request.session.modified =True


def product_profile(request, product_id):
    product = Products.objects.get(id = product_id)
    check_user_signin = request.user.is_authenticated
    size_stock = Stock.objects.filter(product = product_id, quantity__gt=0)
        
    if request.user.is_authenticated:   
        cart_count = product_cart.objects.filter(user=request.user).aggregate(count = Count('user'))
        cart_count = cart_count['count']
    else:
        cart_count = 0
    total_stock = Stock.objects.filter(product = product).aggregate(stock_count = Sum('quantity'))
    
    h = recently_viewed(request, product_id)  
     
    
    recently_viewed_items = Products.objects.filter(pk__in=request.session.get("recently_viewed", [])).exclude(id = product_id)
    
    print(recently_viewed_items)
                                                   
    if request.method == 'POST':
            quantity = request.POST['quantity']
            input_size = request.POST['size']
            
            if input_size != "#":
                quantity = int(quantity)
                size = Size.objects.get(size = input_size)
                stock = Stock.objects.get(product=product, size=size)
                if request.user.is_authenticated:
                    already_added = product_cart.objects.filter(user=request.user, product=product_id, size=size).exists()
                    if quantity > stock.quantity:
                        quantity_error = 'no stock'
                        return render(request, 'product_profile.html', {'product': product, 'cart_count':cart_count, 'all_sizes':size_stock, 'quantity_error':quantity_error, 'total_stock':total_stock, 'check_user_signin':check_user_signin})
                        
                    if already_added is False:
                        add_cart = product_cart.objects.create(user=request.user, product=product, quantity=quantity, size=size)
                        add_cart.save()
                        messages.success(request, 'product added to cart')
                    else:
                        already_added_error = 'product already added to cart'
                        return render(request, 'product_profile.html', {'product': product, 'cart_count':cart_count, 'all_sizes':size_stock, 'already_added':already_added_error, 'total_stock':total_stock, 'check_user_signin':check_user_signin})
                else:
                    return redirect('user_signin')
            else:
                select_size_error = 'select your size'
                return render(request, 'product_profile.html', {'product': product, 'cart_count':cart_count, 'all_sizes':size_stock, 'select_size_error':select_size_error, 'total_stock':total_stock, 'check_user_signin':check_user_signin})
    return render(request, 'product_profile.html', {'product': product, 'cart_count':cart_count, 'all_sizes':size_stock, 'total_stock':total_stock['stock_count'], 'check_user_signin':check_user_signin, 'recently_viewed_items':recently_viewed_items})

@active_non_superuser_required
def products_cart(request):
    cart_items = product_cart.objects.prefetch_related().filter(user = request.user).order_by('created_at')
    cart_total = product_cart.objects.filter(user=request.user).aggregate(total_sum = Sum('total_price'))
            
    if len(cart_items) < 1:
        cart_empty = 'empty'
        cart_total = 0
        return render(request, 'cart.html', {'cart_empty': cart_empty, "cart_total":cart_total})
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total['total_sum'],
    }
    return render(request, 'cart.html', context)

@active_non_superuser_required
def add_to_cart(request, product_id):
    if request.user.is_authenticated and request.user.is_superuser==False:
        if request.method == 'POST':
            product = Products.objects.get(id = product_id)
            quantity = request.POST['quantity']
            input_size = request.POST['size']
            quantity = int(quantity)
            size = Size.objects.get(size = input_size)
            stock = Stock.objects.get(product=product, size=size)
            already_added = product_cart.objects.filter(user=request.user, product=product_id, size=size).exists()
            if already_added is False:
                add_cart = product_cart.objects.create(user=request.user, product=product, quantity=quantity, size=size)
                add_cart.save()
                messages.success(request, 'product added to cart')
                return redirect(product_profile, product_id)
            else:
                return redirect(product_profile, product_id)
    return redirect(product_profile, product_id)

def remove_cart_item(request, item_id):
    if request.user.is_authenticated and request.user.is_superuser==False:
        remove = product_cart.objects.get(id = item_id)
        remove.delete()
        return redirect(products_cart)
   
def increment_quantity(request, cart_id, quantity):
    quantity = int(quantity)
    item = product_cart.objects.get(id = cart_id)
    product = item.product
    size = item.size
    
    stock = Stock.objects.get(product=product, size=size)
    item.quantity = quantity + 1
    if item.quantity > stock.quantity:
        messages.error(request, 'no stock available')
        return redirect(products_cart)
    item.save()
    return redirect(products_cart)
   

def decrement_quantity(request, cart_id, quantity):
    quantity = int(quantity)
    if quantity > 1:
        item = product_cart.objects.get(id = cart_id)
        product = item.product
        size = item.size
        
        stock = Stock.objects.get(product=product, size=size)
        item.quantity = quantity - 1
        item.save()
        return redirect(products_cart)
    else:
        return redirect(products_cart)
