from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Product, PriceHistory


@receiver(pre_save, sender=Product)
def track_price_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_product = Product.objects.get(pk=instance.pk)
    except Product.DoesNotExist:
        return

    if old_product.sell_price != instance.sell_price:
        PriceHistory.objects.create(
            product=instance,
            old_price=old_product.sell_price,
            new_price=instance.sell_price,
        )