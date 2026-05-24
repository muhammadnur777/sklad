from django.db import models


class Category(models.Model):
    name = models.CharField('Kategoriya nomi', max_length=100)

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Unit(models.Model):
    name = models.CharField('Birlik nomi', max_length=50)
    short_name = models.CharField('Qisqa nomi', max_length=10)

    class Meta:
        verbose_name = 'O\'lchov birligi'
        verbose_name_plural = 'O\'lchov birliklari'

    def __str__(self):
        return self.short_name


class Product(models.Model):
    name = models.CharField('Tovar nomi', max_length=200)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        verbose_name='Kategoriya', related_name='products'
    )
    unit = models.ForeignKey(
        Unit, on_delete=models.PROTECT,
        verbose_name='O\'lchov birligi'
    )
    
    sell_price = models.IntegerField('Sotish narxi', default=0)
    stock = models.IntegerField('Qoldiq', default=0)
    min_stock = models.IntegerField('Minimal qoldiq', default=0)
    per_box = models.IntegerField('1 korobkada', default=1) # how many products in one box
    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)

    class Meta:
        verbose_name = 'Tovar'
        verbose_name_plural = 'Tovarlar'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.stock} {self.unit.short_name})'

    @property
    def is_low_stock(self):
        return self.stock <= self.min_stock

    @property
    def box_count(self):
        if self.per_box > 0:
            return self.stock // self.per_box
        return 0

    @property
    def total_value(self):
        return self.stock * self.sell_price
    
    qogoz_stock = models.IntegerField("Qog'oz qoldig'i", default=0)
    qogoz_per_unit = models.IntegerField("1 donaga qog'oz", default=1)
    

class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        verbose_name='Tovar', related_name='price_history'
    )
    old_price = models.IntegerField('Eski narx')
    new_price = models.IntegerField('Yangi narx')
    changed_at = models.DateTimeField('O\'zgargan sana', auto_now_add=True)

    class Meta:
        verbose_name = 'Narx tarixi'
        verbose_name_plural = 'Narx tarixi'
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.product.name}: {self.old_price} → {self.new_price}'
    



# Добавь поле в Product (внутри класса Product):


# Новая модель — история qog'oz
class QogozRecord(models.Model):
    TYPES = [('in', 'Kirim'), ('out', 'Chiqim')]

    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='qogoz_records')
    quantity   = models.IntegerField("Soni")
    record_type = models.CharField("Turi", max_length=5, choices=TYPES, default='in')
    date       = models.DateField("Sana")
    note       = models.TextField("Izoh", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Qog'oz"
        verbose_name_plural = "Qog'oz tarixi"

    def __str__(self):
        return f"{self.product.name} — {self.quantity} ({self.get_record_type_display()})"