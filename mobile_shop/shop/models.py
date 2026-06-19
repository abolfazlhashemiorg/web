from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
       return self.name
   

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.IntegerField()
    discount_percent = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    brand = models.CharField(max_length=100, blank=True)
    colors = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    guarantee_months = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def final_price(self):
        return self.price * (100 - self.discount_percent) // 100

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=11)
    address = models.TextField()
    total_price = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"سفارش{self.id}"