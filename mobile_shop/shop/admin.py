from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['full_name', 'phone', 'id']
    list_editable = ['status']  # ← تغییر وضعیت مستقیم از لیست
    inlines = [OrderItemInline]
    readonly_fields = ['total_price', 'created_at']
    
    fieldsets = (
        ('اطلاعات مشتری', {
            'fields': ('user', 'full_name', 'phone', 'address')
        }),
        ('اطلاعات سفارش', {
            'fields': ('total_price', 'status', 'created_at')
        }),
    )

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)