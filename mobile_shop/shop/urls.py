from django.urls import path
from . import views

urlpatterns = [
    # ============================================================
    # صفحات اصلی فروشگاه
    # ============================================================
    path('', views.home, name='home'),  # صفحه اصلی
    path('products/', views.product_list, name='product_list'),  # لیست محصولات با فیلتر
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),  # جزئیات محصول
    
    # ============================================================
    # سبد خرید و تسویه حساب
    # ============================================================
    path('cart/', views.cart_view, name='cart'),  # نمایش سبد خرید
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # افزودن به سبد
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),  # حذف از سبد
    path('checkout/', views.checkout, name='checkout'),  # تسویه حساب و ثبت سفارش
    
    # ============================================================
    # سفارشات
    # ============================================================
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),  # جزئیات یک سفارش
    path('orders/', views.orders_list, name='orders_list'),  # لیست سفارش‌های کاربر
    
    # ============================================================
    # صفحات استاتیک
    # ============================================================
    path('about/', views.about_view, name='about'),  # درباره ما
    path('coming-soon/', views.coming_soon, name='coming_soon'),  # در حال توسعه
]