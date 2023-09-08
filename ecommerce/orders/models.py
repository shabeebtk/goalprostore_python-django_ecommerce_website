from django.db import models
from accounts.models import User_address
from products.models import Products, Size
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from datetime import date
import random
import string
# Create your models here.



class Coupons(models.Model):
    DISCOUNT_CHOICE = (
        ('percentage', 'percentage'),
        ('amount', 'amount')
    )
    coupon_code = models.CharField(max_length=20, unique=True)
    discount = models.PositiveIntegerField()
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICE)
    public_coupon = models.BooleanField(default=False)
    minimum_amount_required = models.PositiveIntegerField()
    maximum_discount = models.PositiveIntegerField()
    valid_from = models.DateField()
    valid_to = models.DateField()
    active = models.BooleanField()
    
    def __str__(self):
        return f"{self.coupon_code}"
    
    def save(self, *args, **kwargs):
        today = date.today()
        today = str(today)
        if str(self.valid_to) < str(today):
            self.active = False
        else:
            self.active = True
        super().save(*args, **kwargs)
    
        
    
class orders(models.Model):
    order_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")
    coupon_applied = models.BooleanField(default=False)
    discount = models.ForeignKey(Coupons, on_delete=models.SET_NULL, null=True)
    order_date = models.DateTimeField()
    status_modified_date = models.DateTimeField(null=True, blank=True)
    return_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.first_name} - {self.order_id}"
    
    def generate_order_id(self):
        prefix = 'ORD'
        random_digits = ''.join(random.choices(string.digits, k=8))
        return f"{prefix}{random_digits}"
    
    def save(self, *args, **kwargs):
        if not self.order_date:
            self.order_date = datetime.now()
            
        if not self.status_modified_date:
            self.status_modified_date = self.order_date + timezone.timedelta(days=7)
        
        if self.status == 'shipped' and self.status_modified_date <= timezone.now():
            self.status = 'delivered'
            self.return_date = self.status_modified_date + timezone.timedelta(days=7)
            
        if self.status == 'delivered':
            self.return_date = self.status_modified_date + timedelta(days=7)
            
        if not self.order_id:
            unique_order_id_found = False
            while not unique_order_id_found:
                new_order_id = self.generate_order_id()
                if not orders.objects.filter(order_id=new_order_id).exists():
                    self.order_id = new_order_id
                    unique_order_id_found = True
        super().save(*args, **kwargs)
        
class order_cancellation_message(models.Model):
    ORDER_STATUS_CHOICE = (
        ('cancel', 'cancel'),
        ('return', 'return')
    )
    order_id = models.ForeignKey(orders, on_delete=models.CASCADE)
    message = models.TextField()
    reason = models.CharField(max_length=30)
    order_status = models.CharField(choices=ORDER_STATUS_CHOICE)
        
class Coupon_applied_users(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_id = models.ForeignKey(orders, on_delete=models.CASCADE) 
    coupon = models.ForeignKey(Coupons, on_delete=models.CASCADE)
    
    def __str__(self) -> str:
        return self.user.email, self.coupon.coupon_code 
        
class Razorpay_orders(models.Model):
    order_id = models.ForeignKey(orders, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=500, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=500, null=True,  blank=True)
    razorpay_signature = models.CharField(max_length=500, null=True, blank=True)
        

class order_address(models.Model):
    order_id = models.ForeignKey(orders, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=12)
    address = models.TextField()
    pincode = models.CharField(max_length=6)
    state = models.CharField(max_length=20)
    city = models.CharField(max_length=20)
    place = models.CharField(max_length=20)
    landmark = models.CharField(max_length=50)
    
    def __str__(self):
        return self.order_id.order_id


class order_items(models.Model):
    order_no = models.ForeignKey(orders, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.order_no} - {self.product.product_name} - {self.total_price}" 
    
class user_wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    
class wallet_transaction(models.Model):
    STATUS_CHOICE = (
        ('debit', 'debit'),
        ('credit', 'credit')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_id = models.ForeignKey(orders, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICE)
    
    def save(self, *args, **kwargs):
        if not self.date:
            self.date = datetime.now()     
        super().save(*args, **kwargs)

