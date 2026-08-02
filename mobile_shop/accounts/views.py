from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from shop.models import Order, Cart, CartItem

def register_view(request):
    """ثبت‌نام کاربر جدید"""
    if request.user.is_authenticated:
        return redirect('/')  # استفاده از آدرس مستقیم

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'ثبت‌نام با موفقیت انجام شد! خوش آمدید.')
            return redirect('/')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را اصلاح کنید.')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """ورود کاربر"""
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                # انتقال سبد خرید مهمان به کاربر لاگین‌شده
                if request.session.session_key:
                    session_key = request.session.session_key
                    guest_cart = Cart.objects.filter(session_key=session_key).first()
                    if guest_cart:
                        user_cart, created = Cart.objects.get_or_create(user=user)
                        for item in guest_cart.items.all():
                            user_item, created = CartItem.objects.get_or_create(
                                cart=user_cart,
                                product=item.product,
                                defaults={'quantity': item.quantity}
                            )
                            if not created:
                                user_item.quantity += item.quantity
                                user_item.save()
                        guest_cart.delete()

                messages.success(request, f'خوش آمدید {user.first_name or user.username}!')
                return redirect('/')
            else:
                messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
        else:
            messages.error(request, 'لطفاً اطلاعات را به درستی وارد کنید.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """خروج کاربر"""
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید.')
    return redirect('/')


@login_required
def profile_view(request):
    """پروفایل کاربر و نمایش سفارش‌ها"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'profile.html', {'orders': orders})