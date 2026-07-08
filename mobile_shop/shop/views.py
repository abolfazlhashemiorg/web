from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Cart, CartItem

def home(request):
    featured_products = Product.objects.filter(is_featured=True)[:8]
    categories = Category.objects.filter(is_active=True)
    latest_products=Product.objects.all().order_by("-created_at")[:4]
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'latest':latest_products,
    })

def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.filter(is_active=True)
    
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)
    
    return render(request, 'products.html', {
        'products': products,
        'categories': categories,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    colors = product.colors.split(',') if product.colors else []
    return render(request, 'product_detail.html', {
        'product': product,
        'colors': colors,
    })

def cart_view(request):
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    return render(request, 'cart.html', {'cart': cart})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # اگر کاربر لاگین هست، از user استفاده کن
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # اگر کاربر ناشناسه، از session_key استفاده کن
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    # اضافه کردن آیتم به سبد خرید
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return redirect('cart')
def checkout(request):
    return render(request, 'checkout.html')

def coming_soon(request):
    return render(request,'coming_soon.html')

def about_viev(request):
    return render(request,'about.html')