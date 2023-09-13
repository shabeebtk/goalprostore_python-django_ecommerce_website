from django.shortcuts import get_object_or_404, render, redirect
from products.models import Products, Size, Category, Brand, Stock, Banners
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import CustomUser
from orders.models import orders, order_items, order_address, Coupon_applied_users, Coupons, order_cancellation_message
from django.contrib import messages
from datetime import datetime
from django.http import JsonResponse
from django.db.models import Sum
from accounts.decorators import superuser_required
from datetime import date, datetime, timedelta
from django.db.models import Count, Sum
from django.db.models import Q

# pdf 
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os


@never_cache
@superuser_required 
def admin_home(request):
    if request.user.is_superuser:
        total_orders = orders.objects.filter(status = 'delivered').aggregate(total = Count('id'))
        total_earnings = orders.objects.filter(status = 'delivered').aggregate(total_earned = Sum('total_amount'))
        total_users = CustomUser.objects.filter(is_active=True).aggregate(total_users = Count('id'))
        total_products = Products.objects.aggregate(total_products = Count('id'))
        
        # chart data 
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        orders_data = {
            orders.objects
            .values('order_date')
            .annotate(earnings = Sum('total_amount'))
            .order_by('order_date')
        }
        dates = []
        earnings = []
        for item in orders_data:
            dates.append(item.values('order_date')) 
            earnings.append(item.values('earnings'))     
                    
        context = {
            'total_orders': total_orders['total'],
            'total_earnings' : total_earnings['total_earned'],
            'total_users':total_users['total_users'],
            'total_products':total_products['total_products'],
            'dates': dates,
            'earnings':earnings
        }
        return render(request, 'admin.html', context)
    else:
        return redirect(admin_signin)
    
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)#, link_callback=fetch_resources)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
    
def download_sales_report(request):
    if request.method == 'GET':
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']
        
        if start_date and end_date and start_date <= end_date:
            order = orders.objects.filter(order_date__gte=start_date, order_date__lte=end_date)
            total = orders.objects.filter(order_date__gte=start_date, order_date__lte=end_date).filter(status = 'delivered').aggregate(total = Sum('total_amount'))
    
            data = {
            'orders':order,
            'total':total['total'],
            'start_date':start_date,
            'end_date':end_date 
        }

            pdf = render_to_pdf('sales_report.html', data)
            #return HttpResponse(pdf, content_type='application/pdf')
            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = f"selesreport{ start_date }{ end_date }.pdf"
                content = "inline; filename='%s'" %(filename)
                #download = request.GET.get("download")
                #if download:
                content = "attachment; filename=%s" %(filename)
                response['Content-Disposition'] = content
                return response
        return redirect(admin_home)
    return redirect(admin_home)
            
@never_cache
def admin_signin(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect(admin_home)
    if request.method == 'POST':
        email = request.POST['admin_email']
        password = request.POST['admin_password']
        user = authenticate(email=email, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect(admin_home)  
        else:
            login_error = 'invalid details'
            return render(request, 'admin_signin.html', {'login_error':login_error})
    return render(request, 'admin_signin.html')

def admin_logout(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect(admin_signin)


# manage users 
@superuser_required
def manage_users(request):
    users = CustomUser.objects.filter(is_superuser = False)
    search_user = request.GET.get('search_user')
    if search_user:
        users = CustomUser.objects.filter(
            Q(first_name__icontains=search_user) |
            Q(last_name__icontains=search_user) |
            Q(email__icontains=search_user)
        ).filter(is_superuser=False)    
    
    return render(request, 'users/manage_users.html', {'all_users':users})

@superuser_required
def block_users(request, user_id):
    block_user = CustomUser.objects.get(id = user_id)
    block_user.is_active = False
    block_user.save()
    return redirect(manage_users)

@superuser_required
def unblock_users(request, user_id):
    block_user = CustomUser.objects.get(id = user_id)
    block_user.is_active = True
    block_user.save()
    return redirect(manage_users)

# manage Products
@superuser_required
def manage_products(request):
    search_product = request.GET.get('search_product')
    products = Products.objects.annotate(total_stock=Sum('stock__quantity')).order_by('id')
    if search_product:
        products = Products.objects.annotate(total_stock=Sum('stock__quantity')).order_by('id').filter(
            Q(product_name__icontains=search_product) |
            Q(category__category_name__icontains=search_product) |
            Q(brand__brand_name__icontains=search_product) 
        )
    return render(request, 'products/manage_products.html', {'all_products' : products, 'search_product':search_product})

@superuser_required
def add_products(request):
    all_category = Category.objects.all()
    all_brands = Brand.objects.all()
    # size_and_stock = Size_Stock.objects.prefetch_related()
    
    if request.method == 'POST':
        product_name = request.POST['product_name']
        description = request.POST['product_description']
        price = request.POST['product_price']
        gender = request.POST.get('gender')
        image_1 = request.FILES.get('product_image_1')
        image_2 = request.FILES.get('product_image_2')
        image_3 = request.FILES.get('product_image_3')
        image_4 = request.FILES.get('product_image_4')
        
        print(gender)
        
        category_id = request.POST['product_category']
        category = get_object_or_404(Category, id=category_id)
        
        brand_id = request.POST['product_brand']
        brand = get_object_or_404(Brand, id=brand_id)
                
        new_product = Products(product_name=product_name, category=category, brand=brand, description=description, price=price, gender=gender, image_1=image_1, image_2=image_2, image_3=image_3, image_4=image_4)
        new_product.save()
        
        # stocks with size
        small_size = Size.objects.get(size = 'S')
        medium_size = Size.objects.get(size = 'M')
        large_size = Size.objects.get(size = 'L')
        xlarge_size = Size.objects.get(size = 'XL')
        size_5 = Size.objects.get(size = '5')
        size_7 = Size.objects.get(size = '7')
        size_8 = Size.objects.get(size = '8')
        size_9 = Size.objects.get(size = '9')
        size_10 = Size.objects.get(size = '10')
        
        small_stock = request.POST['small_stock']
        medium_stock = request.POST['medium_stock']
        large_stock = request.POST['large_stock']
        xlarge_stock = request.POST['xlarge_stock']
        stock_5 = request.POST['5_stock']
        stock_7 = request.POST['7_stock']
        stock_8 = request.POST['8_stock']
        stock_9 = request.POST['9_stock']
        stock_10 = request.POST['10_stock']
       
        if new_product.category.category_name == 'jersey' or new_product.category.category_name == 'shorts':
            if len(small_stock) > 0:    
                Stock.objects.create(product = new_product, size = small_size, quantity = small_stock).save()
            else:
                Stock.objects.create(product = new_product, size = small_size, quantity = "0").save()
                
            if len(medium_stock) > 0:    
                Stock.objects.create(product = new_product, size = medium_size, quantity = medium_stock).save()
            else:
                Stock.objects.create(product = new_product, size = medium_size, quantity = "0").save()
            
            if len(large_stock) > 0:    
                Stock.objects.create(product = new_product, size = large_size, quantity = medium_stock).save()
            else:
                Stock.objects.create(product = new_product, size = large_size, quantity = "0").save()
            
            if len(xlarge_stock) > 0:    
                Stock.objects.create(product = new_product, size = xlarge_size, quantity = xlarge_stock).save()
            else:
                Stock.objects.create(product = new_product, size = xlarge_size, quantity = "0").save()
                 
        elif new_product.category.category_name == 'football boot':        
            Stock.objects.create(product = new_product, size = size_7, quantity = stock_7).save()
            Stock.objects.create(product = new_product, size = size_8, quantity = stock_8).save()       
            Stock.objects.create(product = new_product, size = size_9, quantity = stock_9).save()       
            Stock.objects.create(product = new_product, size = size_10, quantity = stock_10).save()
        else:
            Stock.objects.create(product = new_product, size = size_5, quantity = stock_5).save()
            
        return redirect(manage_products)
    return render(request, 'products/add_products.html', {'all_category': all_category, 'all_brands': all_brands})
        

# edit product
@superuser_required 
def edit_product(request, product_id):
    edit = Products.objects.get(id = product_id)
    all_categories = Category.objects.exclude(id = edit.category.id)
    all_brands = Brand.objects.exclude(id = edit.brand.id)
    
    # size 
    small_size = Size.objects.get(size = 'S')
    medium_size = Size.objects.get(size = 'M')
    large_size = Size.objects.get(size = 'L')
    xlarge_size = Size.objects.get(size = 'XL')
    size_7 = Size.objects.get(size = '7')
    size_8 = Size.objects.get(size = '8')
    size_9 = Size.objects.get(size = '9')
    size_10 = Size.objects.get(size = '10')
    size_5 = Size.objects.get(size = '5')
    
    # stock 
    small_stock = Stock.objects.filter(product = edit, size = small_size).first()
    medium_stock = Stock.objects.filter(product = edit, size = medium_size).first()
    large_stock = Stock.objects.filter(product = edit, size = large_size).first()
    xlarge_stock = Stock.objects.filter(product = edit, size = xlarge_size).first()
    stock_5 = Stock.objects.filter(product = edit, size = size_5).first()
    stock_7 = Stock.objects.filter(product = edit, size = size_7).first()
    stock_8 = Stock.objects.filter(product = edit, size = size_8).first()
    stock_9 = Stock.objects.filter(product = edit, size = size_9).first()
    stock_10 = Stock.objects.filter(product = edit, size = size_10).first()
    
    small_quantity = small_stock.quantity if small_stock else 0
    medium_quantity = medium_stock.quantity if medium_stock else 0
    large_quantity = large_stock.quantity if large_stock else 0
    xlarge_quantity = xlarge_stock.quantity if xlarge_stock else 0  
    quantity_5 = stock_5.quantity if stock_5 else 0
    quantity_7 = stock_7.quantity if stock_7 else 0
    quantity_8 = stock_8.quantity if stock_8 else 0
    quantity_9 = stock_9.quantity if stock_9 else 0
    quantity_10 = stock_10.quantity if stock_10 else 0

    if request.method == 'POST':
        edit.product_name = request.POST['product_name']
        edit.description = request.POST['product_description']
        edit.price = request.POST['product_price']
        edit.gender = request.POST.get('gender')
        image_1 = request.FILES.get('product_image_1')
        image_2 = request.FILES.get('product_image_2')
        image_3 = request.FILES.get('product_image_3')
        image_4 = request.FILES.get('product_image_4')
        
        if image_1 is not None:
            edit.image_1 = request.FILES.get('product_image_1')
            
        if image_2 is not None:
            edit.image_1 = request.FILES.get('product_image_2')
            
        if image_3 is not None:
            edit.image_1 = request.FILES.get('product_image_3')
            
        if image_4 is not None:
            edit.image_1 = request.FILES.get('product_image_4')
            
        small_stock = request.POST['small_stock']
        medium_stock = request.POST['medium_stock']
        large_stock = request.POST['large_stock']
        xlarge_stock = request.POST['xlarge_stock']
        stock_5  = request.POST['5_stock']
        stock_7 = request.POST['7_stock']
        stock_8 = request.POST['8_stock']
        stock_9 = request.POST['9_stock']   
        stock_10 = request.POST['10_stock']
       
        
        if edit.category.category_name == "jersey" or edit.category.category_name == "shorts":
            product_small = Stock.objects.get(product = edit, size = small_size)
            product_medium = Stock.objects.get(product = edit, size = medium_size)
            product_large = Stock.objects.get(product = edit, size = large_size)
            product_xlarge = Stock.objects.get(product = edit, size = xlarge_size)
            
            product_small.quantity = small_stock
            product_small.save()
            product_medium.quantity = medium_stock
            product_medium.save()
            product_large.quantity = large_stock
            product_large.save()
            product_xlarge.quantity = xlarge_stock
            product_xlarge.save()
            
        elif edit.category.category_name == "football boot":
            product_7= Stock.objects.get(product = edit, size = size_7)
            product_8 = Stock.objects.get(product = edit, size = size_8)
            product_9 = Stock.objects.get(product = edit, size = size_9)
            product_10 = Stock.objects.get(product = edit, size = size_10)
            
            product_7.quantity = stock_7
            product_7.save()
            product_8.quantity = stock_8
            product_8.save()
            product_9.quantity = stock_9
            product_9.save()
            product_10.quantity = stock_10
            product_10.save()
        else:
            product_5 = Stock.objects.get(product = edit, size = size_5)
            product_5.quantity = stock_5
            product_5.save()
        edit.save()
        return redirect(manage_products)
    
    context = {
        'edit_product':edit,
        'all_category':all_categories,
        'all_brands': all_brands,  
        'small' : small_quantity,
        'medium': medium_quantity,
        'large': large_quantity,
        'xlarge': xlarge_quantity,
        'size_5': quantity_5,
        'size_7': quantity_7,
        'size_8': quantity_8,
        'size_9': quantity_9,
        'size_10': quantity_10
    }
    return render(request, 'products/edit_products.html', context)

@superuser_required
def product_unlist(request, product_id):
    product = Products.objects.get(id = product_id) 
    product.status = False
    product.save()
    return redirect(manage_products)

@superuser_required
def product_show(request, product_id):
    product = Products.objects.get(id = product_id)
    product.status = True
    product.save()
    return redirect(manage_products)
    
    
# manage category 
@superuser_required
def manage_category(request):
    all_category = Category.objects.prefetch_related()
    return render(request, 'category/manage_category.html', {'all_category': all_category})

@superuser_required
def add_category(request):
    if request.method == "POST":
        category = Category()
        category.category_name = request.POST.get('category_name')
        category.category_image = request.FILES.get('category_image')
        category.save()
        return redirect(manage_category)

    return render(request, 'category/add_category.html')

@superuser_required
def delete_category(request, category_id):
    delete_category = Category.objects.get(id = category_id)
    delete_category.delete()
    return redirect(manage_category)

@superuser_required
def edit_category(request, category_id):
    edit = Category.objects.get(id = category_id)
    if request.method == 'POST':
        edit.category_name = request.POST.get('category_name')
        image = request.FILES.get('category_image')
        if image:           
            edit.category_image = image
        edit.save()
        return redirect(manage_category)
    return render(request, 'category/edit_category.html', {'edit_category':edit})


# manage brands
@superuser_required
def manage_brands(request):
    all_brands = Brand.objects.prefetch_related()
    return render(request, 'brands/manage_brands.html', {'all_brands': all_brands})
    
@superuser_required
def delete_brands(request, brand_id):
    delete_brand = Brand.objects.get(id = brand_id)
    delete_brand.delete()
    return redirect(manage_brands)

@superuser_required
def add_brands(request):
    if request.method == "POST":
        brand = brand()
        brand.brand_name = request.POST.get('brand_name')
        brand.brand_image = request.FILES.get('brand_image')
        brand.save()
        return redirect(manage_brands)
    return render(request, 'brands/add_brands.html')

@superuser_required
def edit_brands(request, brand_id):
    edit = Brand.objects.get(id = brand_id)
    if request.method == 'POST':
        edit.brand_name = request.POST.get('brand_name')
        image = request.FILES.get('brand_image')
        if image:    
            edit.brand_image = request.FILES.get('brand_image')
        print(edit.brand_name)
        edit.save()
        return redirect(manage_brands)
    return render(request, 'brands/edit_brands.html', {'edit_brand':edit})



# manage_orders 
@superuser_required
def manage_orders(request):
    all_orders = orders.objects.all().order_by('-order_date')

    context = {
        'all_orders': all_orders,
    }
    return render(request, 'orders/manage_orders.html', context)

@superuser_required
def order_details(request, order_id):
    order = orders.objects.get(id = order_id)
    order_products = order_items.objects.filter(order_no_id = order)
    order_address_details = order_address.objects.get(order_id = order_id)
    
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
    
    if request.method == 'POST':
        order_status = request.POST['order_status']
        if order.status != 'delivered' or order.status != 'cancelled':
            if order_status == 'cancelled':
                for item in order_products:
                    stock = Stock.objects.get(product = item.product, size = item.size)
                    stock.quantity += item.quantity
                    stock.save()
            if order_status == 'delivered':
                order.status_modified_date = datetime.now()
            order.status = order_status
            order.save()
            messages.success(request, f' saved changes to order {order_status}')
            return redirect(order_details, order.id)
        
    order_reason = ''  
    if order.status == 'cancelled' or order.status == 'returned':
        try:
            order_reason = order_cancellation_message.objects.get(order_id = order)
        except:
            order_reason = ''
            
        
    context = {
        'order': order,
        'order_address': order_address_details,
        'sub_total':sub_total['total_sum'],
        'coupon_discount':coupon_discount,
        'order_reason': order_reason
    }
    return render(request, 'orders/order_details.html', context)

@superuser_required
def crop(request):
    return render(request, 'products/crop.html')

@superuser_required
def upload_image(request):
    if request.method == 'POST' and request.FILES['croppedImage']:
        image = request.FILES['croppedImage']
        # Process and save the cropped image as needed
        return JsonResponse({'message': 'Image uploaded and cropped successfully.'})

    return JsonResponse({'message': 'Image upload failed.'})


# coupon management

@superuser_required
def manage_coupons(request):
    coupons = Coupons.objects.all()
    context = {
        'coupons':coupons,
    }
    today = date.today()
    today = str(today)
    for coupon in coupons:
        if str(coupon.valid_to) < str(today):
            coupon.active = False
            coupon.save()
    return render(request, 'coupons/coupons.html', context)

@superuser_required
def add_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST['coupon_code']
        discount = request.POST['coupon_discount']
        discount_type  = request.POST['discount_type']
        min_amount_required = request.POST['required_amount']
        max_discount = request.POST['max_discount']
        valid_from = request.POST['valid_from_date']
        valid_to = request.POST['valid_to_date']
        public_coupon = request.POST.get('public_coupon', None)
        
        if coupon_code and discount and discount_type and min_amount_required and max_discount and valid_from and valid_to:
            if valid_from > valid_to:
                error  = 'valid from date lower than valid to'
                return render(request, 'coupons/add_coupon.html', {'error': error})
                
            coupon = Coupons.objects.create(coupon_code=coupon_code, discount=discount, discount_type=discount_type,
                                            minimum_amount_required=min_amount_required, maximum_discount=max_discount,
                                            valid_from=valid_from, valid_to=valid_to, active=True)
            if public_coupon is not None:
                coupon.public_coupon = True
            coupon.save()
            return redirect(manage_coupons)
        else:
            error  = 'must fill all fields'
            return render(request, 'coupons/add_coupon.html', {'error': error})
    return render(request, 'coupons/add_coupon.html')

@superuser_required
def edit_coupon(request, coupon_id):
        coupon = Coupons.objects.get(id = coupon_id)
        
        if request.method == 'POST':
            coupon = Coupons.objects.get(id = coupon_id)
            
            coupon_code = request.POST['coupon_code']
            discount = request.POST['coupon_discount']
            discount_type  = request.POST['discount_type']
            min_amount_required = request.POST['required_amount']
            max_discount = request.POST['max_discount']
            valid_from = request.POST['valid_from_date']
            valid_to = request.POST['valid_to_date']
            public_coupon = request.POST.get('public_coupon', None)
                                
            if coupon_code and discount and discount_type and min_amount_required and max_discount:
                coupon.coupon_code = coupon_code
                coupon.discount = discount
                coupon.discount_type = discount_type
                coupon.minimum_amount_required = min_amount_required
                coupon.maximum_discount = max_discount
                
                if valid_from != '':
                    coupon.valid_from = valid_from                    
                    
                if valid_to != '':
                    coupon.valid_to = valid_to
                
                if valid_from > valid_to:
                    error = 'valid from date should lower than valid to'
                    return render(request, 'coupons/edit_coupon.html', {'edit':coupon, 'error':error})

                if public_coupon is not None:
                    coupon.public_coupon = True
                
                coupon.save()
                return redirect(manage_coupons)
  
        return render(request, 'coupons/edit_coupon.html', {'edit':coupon})
    
from django.http import JsonResponse
# --------banner--------- 
@superuser_required
def manage_banners(request):
    banner = Banners.objects.all()
    context = {
        'banners':banner
    }
    return render(request, 'banners/manage_banner.html', context)

def edit_banner(request, banner_id):
    banner = Banners.objects.get(id = banner_id)
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        image = request.FILES.get('image')
            
        if title and description:
            banner.title = title
            banner.description = description
            if image is not None:
                banner.image = image
            banner.save()
            return redirect(manage_banners)
    context = {
        'banner':banner
    }
    return render(request, 'banners/edit_banner.html', context)

def add_banner(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        image = request.FILES.get('image')
        
        if title and description and image:
            banner = Banners.objects.create(title = title, description=description, image=image)
            banner.save()

    return redirect(manage_banners)
            

def show_unlist_banner(request):
    if request.method == 'POST':
        banner_id = request.POST.get('banner_id')
        banner = Banners.objects.get(id=banner_id)
        if banner.active:    
            banner.active = False
        else:
            banner.active = True
        banner.save()
        
        template = 'banner_status.html'
        context = {'banner': banner}
        html_content = render(request, template, context).content
        
        return JsonResponse({'success': True, 'html_content':html_content})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


