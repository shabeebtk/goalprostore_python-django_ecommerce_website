from django.db import models
from accounts.models import CustomUser
from django.conf import settings
from imagekit.models import ImageSpecField
from .image_processors import Square_Thumbnail, Sixteen_Nine_Thumbnail, Banner_Thumbnail
from imagekit.processors import ResizeToFill
# Create your models here.

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    category_image = models.ImageField(upload_to='category/', null=True, blank=True)
    
    def __str__(self):
        return self.category_name
    
class Brand(models.Model):
    brand_name = models.CharField(max_length=50, unique=True)
    brand_image = models.ImageField(upload_to='brand/', null=True, blank=True)
    
    def __str__(self):
        return self.brand_name 
    
class Products(models.Model):
    GENDER_CHOICE = (
        ('Male', 'MALE'),
        ('Female', 'FEMALE'),
        ('Both', 'BOTH'),
    )
    
    product_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    gender = models.CharField(max_length=12, choices=GENDER_CHOICE, default='Both')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.BooleanField(default=True)
    image_1 = models.ImageField(upload_to='product_images/')
    image_2 = models.ImageField(upload_to='product_images/')
    image_3 = models.ImageField(upload_to='product_images/')        
    image_4 = models.ImageField(upload_to='product_images/')
    
    def __str__(self):
        return self.product_name
    
    def get_total_stock(self):
        return self.sizes.aggregate(total_stock = models.Sum('stock'))['total_stock']
        
class Size(models.Model):
    SIZE_CHOICES = (
        ('none', 'none'),
        ('S', 'small'),
        ('M', 'medium'),
        ('L', 'large'),
        ('XL', 'extra large'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10')
    )
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, unique=True)
    
    def __str__(self):
        return self.size
    
class Stock(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.product.product_name} - {self.size.size} - {self.quantity}"
    
    class Meta:
        unique_together = ['product', 'size']
    
        
class product_cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'product', 'size']
    
    def __str__(self):
        return f"{self.user.first_name} - {self.product.product_name} - Quantity: {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.price = self.product.price
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)
        
    
class wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    

class Banners(models.Model):
    THUMBNAIL_CHOICES = (
        ('square', 'square'),
        ('sixteen_nine', 'sixteen_nine'),
        ('banner', 'banner')
    )
    title = models.CharField(max_length=40)
    description = models.TextField()
    image = models.ImageField(upload_to='banners/')
    active = models.BooleanField(default=True)
    
    