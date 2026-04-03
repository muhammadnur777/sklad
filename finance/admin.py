

from django.contrib import admin
from django.db.models import F
from .models import Sale, SaleItem, Purchase, PurchaseItem, StockMovement
from inventory.models import Product
from .models import Sale, SaleItem, Purchase, PurchaseItem, StockMovement, Shop, BazarStock, BazarSale

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['name']

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    fields = ['product', 'quantity', 'sell_price']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'total_amount', 'purchase_date']
    list_filter = ['purchase_date']
    fields = ['purchase_date', 'note']
    inlines = [PurchaseItemInline]

    class Media:
        js = ('js/purchase_autofill.js',)

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        purchase = form.instance
        total = 0

        for item in purchase.items.all():
            item.total = item.quantity * item.product.sell_price
            item.save()

            total += item.total

            Product.objects.filter(pk=item.product_id).update(
                stock=F('stock') + item.quantity
            )

            StockMovement.objects.get_or_create(
                product=item.product,
                movement_type='purchase',
                quantity=item.quantity,
                price=item.product.sell_price,
                defaults={'created_at': purchase.purchase_date}
            )

        purchase.total_amount = total
        purchase.save(update_fields=['total_amount'])


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ['product', 'quantity', 'price']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'client_name', 'status', 'total_amount', 'sale_date']
    list_filter = ['status', 'sale_date']
    search_fields = ['client_name']
    fields = ['client_name', 'status', 'sale_date', 'note']
    inlines = [SaleItemInline]

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'price', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False