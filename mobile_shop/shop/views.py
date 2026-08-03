from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from .models import Product, Category, Cart, CartItem, Order, OrderItem

# ============================================================
# صفحه اصلی
# ============================================================
def home(request):
    featured_products = Product.objects.filter(is_featured=True)[:8]
    categories = Category.objects.filter(is_active=True)
    latest_products = Product.objects.all().order_by('-created_at')[:4]
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'latest_products': latest_products,
    })

# ============================================================
# لیست محصولات با فیلتر و جستجو
# ============================================================
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

# ============================================================
# جزئیات محصول
# ============================================================
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    colors = product.colors.split(',') if product.colors else []
    return render(request, 'product_detail.html', {
        'product': product,
        'colors': colors,
    })

# ============================================================
# سبد خرید (پشتیبانی از کاربر لاگین و مهمان)
# ============================================================
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

# ============================================================
# افزودن به سبد خرید (پشتیبانی از کاربر لاگین و مهمان)
# ============================================================
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} به سبد خرید اضافه شد.')
    return redirect('cart')

# ============================================================
# حذف از سبد خرید
# ============================================================
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, 'محصول از سبد خرید حذف شد.')
    return redirect('cart')

# ============================================================
# تسویه حساب و ثبت سفارش (فاز ۲)
# ============================================================
def checkout(request):# دریافت سبد خرید
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    # اگر سبد خرید خالی است
    if not cart or not cart.items.exists():
        messages.warning(request, 'سبد خرید شما خالی است!')
        return redirect('cart')
    
    # محاسبه قیمت کل
    total = sum(item.product.final_price * item.quantity for item in cart.items.all())
    
    # بررسی موجودی کالاها
    for item in cart.items.all():
        if item.quantity > item.product.stock:
            messages.error(request, f'موجودی کالا "{item.product.name}" کافی نیست! (موجودی: {item.product.stock})')
            return redirect('cart')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        # اعتبارسنجی ساده فرم
        if not full_name or not phone or not address:
            messages.error(request, 'لطفاً تمام فیلدها را پر کنید!')
            return render(request, 'checkout.html', {
                'cart': cart,
                'total': total,
            })
        
        try:
            with transaction.atomic():
                # ۱. ایجاد سفارش
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    full_name=full_name,
                    phone=phone,
                    address=address,
                    total_price=total,
                    status='pending'
                )
                
                # ۲. ذخیره آیتم‌های سفارش و کم کردن موجودی
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.name,
                        product_price=item.product.final_price,
                        quantity=item.quantity
                    )
                    
                    # کم کردن موجودی
                    product = Product.objects.select_for_update().get(id=item.product.id)
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save()
                    else:
                        raise ValueError(f"موجودی {product.name} کافی نیست!")
                
                # ۳. پاک کردن سبد خرید
                cart.items.all().delete()
                
                messages.success(request, f'سفارش شما با موفقیت ثبت شد! شماره سفارش: #{order.id}')
                return redirect('order_detail', order_id=order.id)
                
        except Exception as e:
            messages.error(request, f'خطا در ثبت سفارش: {str(e)}')
            return redirect('cart')
    
    return render(request, 'checkout.html', {
        'cart': cart,
        'total': total,
    })

# ============================================================
# جزئیات سفارش برای کاربر (فاز ۲)
# ============================================================
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()
    return render(request, 'order_detail.html', {
        'order': order,
        'items': items,
    })

# ============================================================
# صفحه در حال توسعه
# ============================================================
def coming_soon(request):
    return render(request, 'coming_soon.html')

# ============================================================
# درباره ما
# ============================================================
def about_view(request):
    return render(request, 'about.html')