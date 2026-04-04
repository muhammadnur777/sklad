

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
    extra = 0
    fields = ['product', 'quantity']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# @admin.register(Purchase)
# class PurchaseAdmin(admin.ModelAdmin):
#     list_display = ['__str__', 'total_amount', 'purchase_date']
#     list_filter = ['purchase_date']
#     fields = ['purchase_date', 'note', 'total_amount']
#     readonly_fields = ['purchase_date', 'note', 'total_amount']
#     inlines = [PurchaseItemInline]

#     def has_add_permission(self, request):
#         return False

#     def has_change_permission(self, request, obj=None):
#         return True

#     def has_delete_permission(self, request, obj=None):
#         return False



@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'total_amount', 'purchase_date']
    list_filter = ['purchase_date']
    fields = ['purchase_date', 'note', 'total_amount']
    readonly_fields = ['purchase_date', 'note', 'total_amount']
    inlines = [PurchaseItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ['product', 'quantity', 'price']

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

    SECRET_PASSWORD = 'admin777'

    def get_urls(self):
        from django.urls import path
        custom_urls = [
            path('verify/', self.admin_site.admin_view(self.verify_view), name='finance_sale_verify'),
        ]
        return custom_urls + super().get_urls()

    def verify_view(self, request):
        from django.shortcuts import render
        from django.http import HttpResponseRedirect
        if request.method == 'POST':
            password = request.POST.get('password', '')
            if password == self.SECRET_PASSWORD:
                request.session['sale_verified'] = True
                return HttpResponseRedirect('../')
            else:
                return render(request, 'admin/verify_password.html', {
                    'error': 'Parol noto\'g\'ri!',
                    'title': 'Parolni kiriting',
                })
        return render(request, 'admin/verify_password.html', {
            'title': 'Parolni kiriting',
        })

    def changelist_view(self, request, extra_context=None):
        if not request.session.get('sale_verified'):
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('verify/')
        return super().changelist_view(request, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        if not request.session.get('sale_verified'):
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('../verify/')
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not request.session.get('sale_verified'):
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('../verify/')
        return super().change_view(request, object_id, form_url, extra_context)

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