from datetime import date, timedelta
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate, TruncMonth
from functools import lru_cache
def _parse_period(period):
    """Парсит период и возвращает (date_from, date_to)"""
    today = date.today()

    if period == 'bugun' or period == 'today':
        return today, today
    elif period == 'hafta' or period == 'week':
        return today - timedelta(days=7), today
    elif period == 'oy' or period == 'month':
        return date(today.year, today.month, 1), today
    elif period == 'yil' or period == 'year':
        return date(today.year, 1, 1), today
    elif period == 'oxirgi_30' or period == 'last_30':
        return today - timedelta(days=30), today
    elif period == 'oxirgi_90' or period == 'last_90':
        return today - timedelta(days=90), today
    elif period == 'oxirgi_180' or period == 'last_180':
        return today - timedelta(days=180), today
    elif period == 'oxirgi_365' or period == 'last_365':
        return today - timedelta(days=365), today
    elif period in ('all', 'barchasi', 'hammasi', 'все', 'всё', 'all_time'):
        return date(2026, 1, 1), today
    else:
        try:
            parts = period.split('-')
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                specific = date(y, m, d)
                return specific, specific
            elif len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if m == 12:
                    return date(y, m, 1), date(y + 1, 1, 1) - timedelta(days=1)
                return date(y, m, 1), date(y, m + 1, 1) - timedelta(days=1)
        except (ValueError, IndexError):
            pass
        return today - timedelta(days=30), today

def get_sales_by_product(product_name: str, period: str = 'month') -> dict:
    """
    Получает данные о продажах конкретного товара за период.
    Возвращает: количество, сумму, по магазинам.
    """
    from finance.models import BazarSaleItem, Shop
    from inventory.models import Product

    date_from, date_to = _parse_period(period)

    # Сначала точный поиск
    products = Product.objects.filter(name__icontains=product_name, is_active=True)

    # Если не нашли — ищем по каждому слову
    if not products.exists():
        words = product_name.split()
        q = Q(is_active=True)
        for word in words:
            q &= Q(name__icontains=word)
        products = Product.objects.filter(q)

    # Если всё ещё не нашли — ищем по первому слову
    if not products.exists() and len(product_name) > 2:
        first_word = product_name.split()[0] if product_name.split() else product_name
        products = Product.objects.filter(name__icontains=first_word, is_active=True)

    if not products.exists():
        # Показываем похожие товары
        all_products = Product.objects.filter(is_active=True).values_list('name', flat=True)[:50]
        return {
            'error': f'Tovar "{product_name}" topilmadi',
            'available_products': list(all_products),
        }

    result = []
    for product in products[:5]:
        total_qty = BazarSaleItem.objects.filter(
            product=product,
            sale__sale_date__gte=date_from,
            sale__sale_date__lte=date_to,
        ).aggregate(
            total_qty=Sum('quantity'),
            total_sum=Sum('total'),
            count=Count('id'),
        )

        # По магазинам
        shops_data = []
        for shop in Shop.objects.all():
            shop_sales = BazarSaleItem.objects.filter(
                product=product,
                sale__shop=shop,
                sale__sale_date__gte=date_from,
                sale__sale_date__lte=date_to,
            ).aggregate(
                qty=Sum('quantity'),
                total=Sum('total'),
            )
            if shop_sales['qty']:
                shops_data.append({
                    'shop': shop.name,
                    'qty': shop_sales['qty'] or 0,
                    'total': shop_sales['total'] or 0,
                })

        per_box = product.per_box if product.per_box > 0 else 1
        qty = total_qty['total_qty'] or 0

        result.append({
            'product': product.name,
            'period': f'{date_from} — {date_to}',
            'sold_qty': qty,
            'sold_boxes': qty // per_box,
            'total_sum': total_qty['total_sum'] or 0,
            'transactions': total_qty['count'] or 0,
            'current_price': product.sell_price,
            'stock': product.stock,
            'stock_boxes': product.stock // per_box,
            'shops': shops_data,
        })

    return {'results': result}


def get_top_products(limit: int = 10, period: str = 'month', sort_by: str = 'quantity') -> dict:
    """
    Возвращает топ продаваемых товаров за период.
    sort_by: 'quantity' или 'revenue'
    """
    from finance.models import BazarSaleItem

    date_from, date_to = _parse_period(period)

    order_field = '-total_qty' if sort_by == 'quantity' else '-total_sum'

    top = BazarSaleItem.objects.filter(
        sale__sale_date__gte=date_from,
        sale__sale_date__lte=date_to,
    ).values(
        'product__name', 'product__sell_price', 'product__per_box'
    ).annotate(
        total_qty=Sum('quantity'),
        total_sum=Sum('total'),
        transactions=Count('id'),
    ).order_by(order_field)[:limit]

    results = []
    for i, item in enumerate(top, 1):
        per_box = item['product__per_box'] or 1
        results.append({
            'rank': i,
            'product': item['product__name'],
            'sold_qty': item['total_qty'] or 0,
            'sold_boxes': (item['total_qty'] or 0) // per_box,
            'total_sum': item['total_sum'] or 0,
            'transactions': item['transactions'],
            'price': item['product__sell_price'],
        })

    return {
        'period': f'{date_from} — {date_to}',
        'sort_by': sort_by,
        'top_products': results,
    }


def get_revenue(period: str = 'month') -> dict:
    """
    Общая выручка за период. С разбивкой по магазинам.
    """
    from finance.models import BazarSale, Shop

    date_from, date_to = _parse_period(period)

    total = BazarSale.objects.filter(
        sale_date__gte=date_from,
        sale_date__lte=date_to,
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id'),
        paid=Sum('total_amount', filter=Q(payment_status='paid')),
        debt=Sum('total_amount', filter=Q(payment_status='debt')),
    )

    shops_data = []
    for shop in Shop.objects.all():
        shop_total = BazarSale.objects.filter(
            shop=shop,
            sale_date__gte=date_from,
            sale_date__lte=date_to,
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id'),
        )
        shops_data.append({
            'shop': shop.name,
            'total': shop_total['total'] or 0,
            'transactions': shop_total['count'] or 0,
        })

    return {
        'period': f'{date_from} — {date_to}',
        'total_revenue': total['total'] or 0,
        'total_transactions': total['count'] or 0,
        'paid': total['paid'] or 0,
        'debt': total['debt'] or 0,
        'shops': shops_data,
    }


def get_daily_sales(period: str = 'week') -> dict:
    """
    Продажи по дням за период. Для анализа трендов.
    """
    from finance.models import BazarSale

    date_from, date_to = _parse_period(period)

    daily = BazarSale.objects.filter(
        sale_date__gte=date_from,
        sale_date__lte=date_to,
    ).values('sale_date').annotate(
        total=Sum('total_amount'),
        count=Count('id'),
    ).order_by('sale_date')

    days = []
    for d in daily:
        days.append({
            'date': str(d['sale_date']),
            'total': d['total'] or 0,
            'transactions': d['count'],
        })

    total_sum = sum(d['total'] for d in days)
    avg_daily = total_sum // len(days) if days else 0

    return {
        'period': f'{date_from} — {date_to}',
        'days': days,
        'total': total_sum,
        'avg_daily': avg_daily,
        'days_count': len(days),
    }


def get_debts_info() -> dict:
    """
    Информация о долгах (qarzdorlar).
    """
    from finance.models import BazarSale, Shop

    debts = BazarSale.objects.filter(payment_status='debt')

    total = debts.aggregate(
        total=Sum('total_amount'),
        count=Count('id'),
    )

    # По магазинам
    shops_data = []
    for shop in Shop.objects.all():
        shop_debts = debts.filter(shop=shop).aggregate(
            total=Sum('total_amount'),
            count=Count('id'),
        )
        shops_data.append({
            'shop': shop.name,
            'total': shop_debts['total'] or 0,
            'count': shop_debts['count'] or 0,
        })

    # Топ должников
    top_debtors = debts.values('client_name').annotate(
        total=Sum('total_amount'),
        count=Count('id'),
    ).order_by('-total')[:10]

    debtors = []
    for d in top_debtors:
        if d['client_name']:
            debtors.append({
                'name': d['client_name'],
                'total': d['total'] or 0,
                'count': d['count'],
            })

    return {
        'total_debt': total['total'] or 0,
        'total_count': total['count'] or 0,
        'shops': shops_data,
        'top_debtors': debtors,
    }


def get_warehouse_info() -> dict:
    """
    Информация о складе: общая стоимость, товары с низким остатком.
    """
    from inventory.models import Product

    products = Product.objects.filter(is_active=True).select_related('category', 'unit')

    total_value = sum(p.stock * p.sell_price for p in products)
    total_items = sum(p.stock for p in products)
    total_products = products.count()

    low_stock = []
    for p in products:
        if p.is_low_stock and p.min_stock > 0:
            per_box = p.per_box if p.per_box > 0 else 1
            low_stock.append({
                'product': p.name,
                'stock': p.stock,
                'boxes': p.stock // per_box,
                'min_stock': p.min_stock,
                'category': p.category.name if p.category else '',
            })

    return {
        'total_value': total_value,
        'total_items': total_items,
        'total_products': total_products,
        'low_stock_count': len(low_stock),
        'low_stock': low_stock[:20],
    }


def get_shipments_info(period: str = 'month') -> dict:
    """
    Информация о отправках на базар (ketuvlar) с деталями товаров.
    """
    from finance.models import Sale, SaleItem, Shop

    date_from, date_to = _parse_period(period)

    shipments = Sale.objects.filter(
        note__startswith='Bozorga',
        sale_date__gte=date_from,
        sale_date__lte=date_to,
    ).prefetch_related('items__product__category')

    total = shipments.aggregate(
        total=Sum('total_amount'),
        count=Count('id'),
    )

    # По магазинам
    shops_data = []
    for shop in Shop.objects.all():
        shop_total = shipments.filter(
            note__contains=shop.name
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id'),
        )
        shops_data.append({
            'shop': shop.name,
            'total': shop_total['total'] or 0,
            'count': shop_total['count'] or 0,
        })

    # Детали каждой отправки с товарами
    shipments_list = []
    for sale in shipments[:20]:
        items = []
        for item in sale.items.select_related('product').all():
            per_box = item.product.per_box if item.product.per_box > 0 else 1
            items.append({
                'product': item.product.name,
                'quantity': item.quantity,
                'boxes': item.quantity // per_box,
                'price': item.price,
                'total': item.total,
                'category': item.product.category.name if item.product.category else '',
            })
        shipments_list.append({
            'date': str(sale.sale_date),
            'note': sale.note,
            'total': sale.total_amount,
            'items': items,
        })

    return {
        'period': f'{date_from} — {date_to}',
        'total_amount': total['total'] or 0,
        'total_shipments': total['count'] or 0,
        'shops': shops_data,
        'shipments': shipments_list,
    }


def get_price_changes(limit: int = 20) -> dict:
    """
    Последние изменения цен.
    """
    from inventory.models import PriceHistory

    changes = PriceHistory.objects.select_related('product').order_by('-changed_at')[:limit]

    result = []
    for ch in changes:
        result.append({
            'product': ch.product.name,
            'old_price': ch.old_price,
            'new_price': ch.new_price,
            'change': ch.new_price - ch.old_price,
            'date': ch.changed_at.strftime('%d.%m.%Y %H:%M'),
        })

    return {
        'total_changes': PriceHistory.objects.count(),
        'recent_changes': result,
    }


def get_comparison(period1: str, period2: str) -> dict:
    """
    Сравнение двух периодов по выручке.
    """
    from finance.models import BazarSale

    d1_from, d1_to = _parse_period(period1)
    d2_from, d2_to = _parse_period(period2)

    rev1 = BazarSale.objects.filter(
        sale_date__gte=d1_from, sale_date__lte=d1_to,
    ).aggregate(total=Sum('total_amount'), count=Count('id'))

    rev2 = BazarSale.objects.filter(
        sale_date__gte=d2_from, sale_date__lte=d2_to,
    ).aggregate(total=Sum('total_amount'), count=Count('id'))

    total1 = rev1['total'] or 0
    total2 = rev2['total'] or 0

    if total1 > 0:
        change_pct = round((total2 - total1) / total1 * 100, 1)
    else:
        change_pct = 0

    return {
        'period1': f'{d1_from} — {d1_to}',
        'period1_revenue': total1,
        'period1_transactions': rev1['count'] or 0,
        'period2': f'{d2_from} — {d2_to}',
        'period2_revenue': total2,
        'period2_transactions': rev2['count'] or 0,
        'change_percent': change_pct,
        'change_amount': total2 - total1,
    }


# Реестр всех функций для AI
TOOLS_REGISTRY = {
    'get_sales_by_product': get_sales_by_product,
    'get_top_products': get_top_products,
    'get_revenue': get_revenue,
    'get_daily_sales': get_daily_sales,
    'get_debts_info': get_debts_info,
    'get_warehouse_info': get_warehouse_info,
    'get_shipments_info': get_shipments_info,
    'get_price_changes': get_price_changes,
    'get_comparison': get_comparison,
}