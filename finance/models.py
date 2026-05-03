from django.db import models
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from inventory.models import Product

class Shop(models.Model):
    name = models.CharField('Dokon nomi', max_length=100)

    class Meta:
        verbose_name = 'Dokon'
        verbose_name_plural = 'Dokonlar'

    def __str__(self):
        return self.name

class Sale(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Qoralama'
        WAITING = 'waiting', 'To\'lov kutilmoqda'
        PAID = 'paid', 'To\'langan'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        verbose_name='Sotuvchi'
    )
    client_name = models.CharField('Mijoz ismi', max_length=200, blank=True)
    status = models.CharField(
        'Holat', max_length=20,
        choices=Status.choices, default=Status.DRAFT
    )
    total_amount = models.IntegerField('Umumiy summa', default=0)
    total_cost = models.IntegerField('Tan narxi summasi', default=0)
    profit = models.IntegerField('Foyda', default=0)
    note = models.TextField('Izoh', blank=True)
    sale_date = models.DateField('Sotuv sanasi', default=timezone.now)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)

    class Meta:
        verbose_name = 'Sotuv'
        verbose_name_plural = 'bozorga ketuvlar'
        ordering = ['-sale_date', '-created_at']

    def __str__(self):
        status_label = self.get_status_display()
        return f'Sotuv #{self.pk} — {self.total_amount} so\'m ({status_label})'


class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale, on_delete=models.CASCADE,
        related_name='items', verbose_name='Sotuv'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        verbose_name='Tovar'
    )
    quantity = models.IntegerField('Soni')
    price = models.IntegerField('Narxi')
    
    total = models.IntegerField('Jami', default=0)

    class Meta:
        verbose_name = 'Sotuv qatori'
        verbose_name_plural = 'Sotuv qatorlari'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.price
        
        super().save(*args, **kwargs)

    @property
    def box_count(self):
        if self.product.per_box > 0:
            return self.quantity // self.product.per_box
        return 0


class Purchase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        verbose_name='Qabul qiluvchi'
    )
    total_amount = models.IntegerField('Umumiy summa', default=0)
    note = models.TextField('Izoh', blank=True)
    purchase_date = models.DateField('Kirim sanasi', default=timezone.now)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)

    class Meta:
        verbose_name = 'Kirim'
        verbose_name_plural = 'Kirimlar'
        ordering = ['-purchase_date', '-created_at']

    def __str__(self):
        return f'Kirim #{self.pk} — {self.total_amount} so\'m'


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase, on_delete=models.CASCADE,
        related_name='items', verbose_name='Kirim'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        verbose_name='Tovar'
    )
    quantity = models.IntegerField('Soni')
    
    sell_price = models.IntegerField('Sotish narxi', default=0)
    total = models.IntegerField('Jami', default=0)

    class Meta:
        verbose_name = 'Kirim qatori'
        verbose_name_plural = 'Kirim qatorlari'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.sell_price
        super().save(*args, **kwargs)

class StockMovement(models.Model):
    class Type(models.TextChoices):
        SALE = 'sale', 'Sotuv'
        PURCHASE = 'purchase', 'Kirim'

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        verbose_name='Tovar'
    )
    movement_type = models.CharField(
        'Turi', max_length=20, choices=Type.choices
    )
    quantity = models.IntegerField('Soni')
    price = models.IntegerField('Narxi', default=0)
    created_at = models.DateTimeField('Sana', auto_now_add=True)

    class Meta:
        verbose_name = 'Tovar harakati'
        verbose_name_plural = 'Tovar harakatlari'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} | {self.get_movement_type_display()} | {self.quantity}'

    @classmethod
    def cleanup_old(cls):
        cutoff = timezone.now() - relativedelta(months=16)
        cls.objects.filter(created_at__lt=cutoff).delete()


class BazarStock(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        verbose_name='Tovar', related_name='bazar'
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE,
        verbose_name='Dokon', related_name='stocks',
        null=True
    )
    quantity = models.IntegerField('Bozordagi soni', default=0)

    class Meta:
        verbose_name = 'Bozordagi tovar'
        verbose_name_plural = 'Bozordagi tovarlar'
        unique_together = ['product', 'shop']

    def __str__(self):
        shop_name = self.shop.name if self.shop else 'Noma\'lum'
        return f'{self.product.name} — {self.quantity} ({shop_name})'

    @property
    def box_count(self):
        per_box = self.product.per_box if self.product.per_box > 0 else 1
        return self.quantity // per_box


class BazarSale(models.Model):
    class PaymentStatus(models.TextChoices):
        PAID = 'paid', 'To\'langan'
        DEBT = 'debt', 'Qarz'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        verbose_name='Sotuvchi'
    )
    client_name = models.CharField('Mijoz ismi', max_length=200, blank=True)
    client_phone = models.CharField('Mijoz telefoni', max_length=20, blank=True)
    shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE,
        verbose_name='Dokon', related_name='sales',
        null=True
    )
    payment_status = models.CharField(
        'To\'lov holati', max_length=20,
        choices=PaymentStatus.choices, default=PaymentStatus.PAID
    )
    total_amount = models.IntegerField('Umumiy summa', default=0)
    sale_date = models.DateField('Sotuv sanasi')
    note = models.TextField('Izoh', blank=True)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)

    class Meta:
        verbose_name = 'Bozor sotuvi'
        verbose_name_plural = 'Bozor sotuvlari'
        ordering = ['-sale_date', '-created_at']

    def __str__(self):
        return f'Bozor sotuv #{self.pk} — {self.total_amount} so\'m'


class BazarSaleItem(models.Model):
    sale = models.ForeignKey(
        BazarSale, on_delete=models.CASCADE,
        related_name='items', verbose_name='Sotuv'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        verbose_name='Tovar'
    )
    quantity = models.IntegerField('Soni')
    price = models.IntegerField('Narxi')
    total = models.IntegerField('Jami', default=0)

    class Meta:
        verbose_name = 'Bozor sotuv qatori'
        verbose_name_plural = 'Bozor sotuv qatorlari'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.price
        super().save(*args, **kwargs)


class Message(models.Model):
    class Direction(models.TextChoices):
        TO_SKLAD = 'to_sklad', 'Bozordan → Skladga'
        TO_BOZOR = 'to_bozor', 'Skladdan → Bozorga'

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        verbose_name='Yuboruvchi'
    )
    direction = models.CharField(
        'Yo\'nalish', max_length=20, choices=Direction.choices
    )
    text = models.TextField('Xabar')
    is_read = models.BooleanField('O\'qilgan', default=False)
    created_at = models.DateTimeField('Vaqt', auto_now_add=True)

    class Meta:
        verbose_name = 'Xabar'
        verbose_name_plural = 'Xabarlar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_direction_display()} — {self.text[:30]}'


class BozorPayment(models.Model):
    amount = models.IntegerField('Summa')
    payment_date = models.DateField('Sana')
    note = models.TextField('Izoh', blank=True)
    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)

    class Meta:
        verbose_name = 'Bozordan pul'
        verbose_name_plural = 'Bozordan pullar'
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f'{self.amount} so\'m — {self.payment_date}'
    

class BazarMovement(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Dokon')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Tovar')
    quantity_before = models.IntegerField('Oldin')
    quantity_after = models.IntegerField('Keyin')
    created_at = models.DateTimeField('Sana', auto_now_add=True)

    class Meta:
        verbose_name = 'Bozor harakati'
        verbose_name_plural = 'Bozor harakatlari'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} | {self.quantity_before} → {self.quantity_after}'


