from django.contrib import admin
from django import forms
from .models import Category, Unit, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name']


class ProductForm(forms.ModelForm):
    box_count_edit = forms.IntegerField(
        label='Korobka soni',
        required=False,
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            per_box = self.instance.per_box if self.instance.per_box > 0 else 1
            self.fields['box_count_edit'].initial = self.instance.stock // per_box


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ['name', 'category', 'sell_price', 'stock', 'box_count_display', 'per_box', 'unit', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name']
    list_editable = ['sell_price', 'per_box', 'is_active']
    fields = ['name', 'category', 'unit', 'sell_price', 'box_count_edit', 'per_box', 'stock', 'min_stock', 'is_active']

    def box_count_display(self, obj):
        return f'{obj.box_count} kor.'
    box_count_display.short_description = 'Korobka'

    def has_delete_permission(self, request, obj=None):
        return True

    def save_model(self, request, obj, form, change):
        box_count_edit = form.cleaned_data.get('box_count_edit')
        if box_count_edit is not None:
            per_box = obj.per_box if obj.per_box > 0 else 1
            obj.stock = box_count_edit * per_box
        super().save_model(request, obj, form, change)