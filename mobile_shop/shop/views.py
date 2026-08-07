from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from .models import Product, Category, Cart, CartItem, Order, OrderItem

# ============================================================
# صفحه اصلی
# ============================================================
def home(request):
    """نمایش صفحه اصلی با محصولات ویژه، جدید و دسته‌بندی‌ها"""
    featured_products = Product.objects.filter(is_featured=True)[:8]
    categories = Category.objects.filter(is_active=True)
    latest_products = Product.objects.all().order_by('-created_at')[:4]
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'latest_products': latest_products,
    })

# ============================================================
# لیست محصولات با فیلتر و جستجوی پیشرفته (فاز ۳)
# ============================================================
def product_list(request):
    """نمایش لیست محصولات با قابلیت فیلتر پیشرفته"""
    products = Product.objects.all()
    categories = Category.objects.filter(is_active=True)
    
    # دریافت برندهای موجود برای فیلتر
    brands = Product.objects.values_list('brand', flat=True).distinct().exclude(brand='')
    
    # ========== فیلترها ==========
    # ۱. فیلتر بر اساس دسته‌بندی
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    # ۲. فیلتر بر اساس برند
    brand = request.GET.get('brand')
    if brand:
        products = products.filter(brand__icontains=brand)
    
    # ۳. فیلتر بر اساس محدوده قیمت
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=int(min_price))
    if max_price:
        products = products.filter(price__lte=int(max_price))
    
    # ۴. جستجو در نام و برند
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(brand__icontains=search)
        )
    
    # ۵. مرتب‌سازی
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')  # پیش‌فرض
    
    return render(request, 'products.html', {
        'products': products,
        'categories': categories,
        'brands': brands,
        'selected_brand': brand,
        'selected_category': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'search': search,
        'sort': sort,
    })

# ============================================================
# جزئیات محصول
# ============================================================
def product_detail(request, slug):
    """نمایش جزئیات کامل یک محصول"""
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
    """نمایش سبد خرید کاربر (لاگین یا مهمان)"""
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    return render(request, 'cart.html', {'cart': cart})# ============================================================
# افزودن به سبد خرید (پشتیبانی از کاربر لاگین و مهمان)
# ============================================================
def add_to_cart(request, product_id):
    """افزودن محصول به سبد خرید (با پشتیبانی از مهمان)"""
    product = get_object_or_404(Product, id=product_id)
    
    # دریافت یا ایجاد سبد خرید
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    # افزودن/به‌روزرسانی آیتم
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'✅ {product.name} به سبد خرید اضافه شد.')
    return redirect('cart')

# ============================================================
# حذف از سبد خرید
# ============================================================
def remove_from_cart(request, item_id):
    """حذف یک آیتم از سبد خرید"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'❌ {product_name} از سبد خرید حذف شد.')
    return redirect('cart')

# ============================================================
# تسویه حساب و ثبت سفارش (فاز ۲)
# ============================================================
def checkout(request):
    """تکمیل فرآیند خرید و ثبت سفارش"""
    # دریافت سبد خرید
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
        messages.warning(request, '🛒 سبد خرید شما خالی است!')
        return redirect('cart')
    
    # محاسبه قیمت کل
    total = sum(item.product.final_price * item.quantity for item in cart.items.all())
    
    # بررسی موجودی کالاها
    for item in cart.items.all():
        if item.quantity > item.product.stock:
            messages.error(request, f'⚠️ موجودی کالا "{item.product.name}" کافی نیست! (موجودی: {item.product.stock})')
            return redirect('cart')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        # اعتبارسنجی فرم
        if not full_name or not phone or not address:
            messages.error(request, '❌ لطفاً تمام فیلدها را پر کنید!')
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
                        product_price=item.product.final_price,quantity=item.quantity
                    )
                    
                    # کم کردن موجودی با قفل روی ردیف
                    product = Product.objects.select_for_update().get(id=item.product.id)
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save()
                    else:
                        raise ValueError(f"موجودی {product.name} کافی نیست!")
                
                # ۳. پاک کردن سبد خرید
                cart.items.all().delete()
                
                messages.success(request, f'🎉 سفارش شما با موفقیت ثبت شد! شماره سفارش: #{order.id}')
                return redirect('order_detail', order_id=order.id)
                
        except Exception as e:
            messages.error(request, f'❌ خطا در ثبت سفارش: {str(e)}')
            return redirect('cart')
    
    return render(request, 'checkout.html', {
        'cart': cart,
        'total': total,
    })

# ============================================================
# جزئیات سفارش برای کاربر (فاز ۲)
# ============================================================
@login_required
def order_detail(request, order_id):
    """نمایش جزئیات کامل یک سفارش برای کاربر"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()
    return render(request, 'order_detail.html', {
        'order': order,
        'items': items,
    })

# ============================================================
# لیست سفارش‌های کاربر (فاز ۳)
# ============================================================
@login_required
def orders_list(request):
    """نمایش لیست تمام سفارش‌های کاربر"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders_list.html', {'orders': orders})

# ============================================================
# صفحات استاتیک
# ============================================================
def about_view(request):
    """صفحه درباره ما"""
    return render(request, 'about.html')

def coming_soon(request):
    """صفحه در حال توسعه"""
    return render(request, 'coming_soon.html')