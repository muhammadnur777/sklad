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
            # Диапазон: 2026-04-01_2026-04-09
            if '_' in period:
                parts = period.split('_')
                if len(parts) == 2:
                    d1 = parts[0].split('-')
                    d2 = parts[1].split('-')
                    if len(d1) == 3 and len(d2) == 3:
                        return date(int(d1[0]), int(d1[1]), int(d1[2])), date(int(d2[0]), int(d2[1]), int(d2[2]))

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


def get_product_shipments(product_name: str, period: str = 'barchasi') -> dict:
    """
    Конкретный товар бозорга қанча юборилганини кўрсатади.
    """
    from finance.models import SaleItem, Sale, Shop
    from inventory.models import Product

    date_from, date_to = _parse_period(period)

    # Поиск товара
    products = Product.objects.filter(name__icontains=product_name, is_active=True)

    if not products.exists():
        words = product_name.split()
        q = Q(is_active=True)
        for word in words:
            q &= Q(name__icontains=word)
        products = Product.objects.filter(q)

    if not products.exists() and len(product_name) > 2:
        first_word = product_name.split()[0] if product_name.split() else product_name
        products = Product.objects.filter(name__icontains=first_word, is_active=True)

    if not products.exists():
        all_products = Product.objects.filter(is_active=True).values_list('name', flat=True)[:50]
        return {
            'error': f'Tovar "{product_name}" topilmadi',
            'available_products': list(all_products),
        }

    result = []
    for product in products[:5]:
        per_box = product.per_box if product.per_box > 0 else 1

        # Все отправки этого товара
        shipment_items = SaleItem.objects.filter(
            product=product,
            sale__note__startswith='Bozorga',
            sale__sale_date__gte=date_from,
            sale__sale_date__lte=date_to,
        ).select_related('sale')

        total_qty = shipment_items.aggregate(
            total_qty=Sum('quantity'),
            total_sum=Sum('total'),
            count=Count('id'),
        )

        qty = total_qty['total_qty'] or 0

        # По магазинам
        shops_data = []
        for shop in Shop.objects.all():
            shop_items = shipment_items.filter(sale__note__contains=shop.name)
            shop_total = shop_items.aggregate(
                qty=Sum('quantity'),
                total=Sum('total'),
                count=Count('id'),
            )
            if shop_total['qty']:
                shops_data.append({
                    'shop': shop.name,
                    'qty': shop_total['qty'] or 0,
                    'boxes': (shop_total['qty'] or 0) // per_box,
                    'total': shop_total['total'] or 0,
                    'shipments': shop_total['count'] or 0,
                })

        # Детали каждой отправки
        details = []
        for item in shipment_items.order_by('-sale__sale_date')[:20]:
            details.append({
                'date': str(item.sale.sale_date),
                'destination': item.sale.note,
                'qty': item.quantity,
                'boxes': item.quantity // per_box,
                'price': item.price,
                'total': item.total,
            })

        result.append({
            'product': product.name,
            'period': f'{date_from} — {date_to}',
            'total_shipped_qty': qty,
            'total_shipped_boxes': qty // per_box,
            'total_sum': total_qty['total_sum'] or 0,
            'total_shipments': total_qty['count'] or 0,
            'current_stock': product.stock,
            'current_stock_boxes': product.stock // per_box,
            'per_box': per_box,
            'shops': shops_data,
            'details': details,
        })

    return {'results': result}

def get_stock_forecast(days_analysis: int = 30, limit: int = 20) -> dict:
    """
    Прогноз когда закончатся товары на складе.
    Считает среднедневные продажи за days_analysis дней и делит на остаток.
    """
    from finance.models import BazarSaleItem
    from inventory.models import Product

    today = date.today()
    date_from = today - timedelta(days=days_analysis)

    products = Product.objects.filter(is_active=True, stock__gt=0).select_related('category')

    results = []
    for product in products:
        per_box = product.per_box if product.per_box > 0 else 1

        total_sold = BazarSaleItem.objects.filter(
            product=product,
            sale__sale_date__gte=date_from,
            sale__sale_date__lte=today,
        ).aggregate(total=Sum('quantity'))['total'] or 0

        daily_avg = total_sold / days_analysis if total_sold > 0 else 0

        if daily_avg > 0:
            days_left = round(product.stock / daily_avg)
            runs_out = str(today + timedelta(days=days_left))
        else:
            days_left = None
            runs_out = None

        if days_left is None:
            status = 'no_sales'
        elif days_left <= 7:
            status = 'urgent'
        elif days_left <= 14:
            status = 'warning'
        else:
            status = 'ok'

        results.append({
            'product': product.name,
            'stock': product.stock,
            'stock_boxes': product.stock // per_box,
            'sold_last_period': total_sold,
            'daily_avg': round(daily_avg, 1),
            'days_left': days_left,
            'runs_out_date': runs_out,
            'status': status,
            'category': product.category.name if product.category else '',
        })

    results.sort(key=lambda x: (x['days_left'] is None, x['days_left'] or 9999))

    urgent = [r for r in results if r['status'] == 'urgent']
    warning = [r for r in results if r['status'] == 'warning']

    return {
        'analysis_period_days': days_analysis,
        'total_products_with_stock': len(results),
        'urgent_count': len(urgent),
        'warning_count': len(warning),
        'forecast': results[:limit],
    }


def get_slow_moving_products(days_threshold: int = 30, limit: int = 20) -> dict:
    """
    Товары с низким оборотом: есть на складе, но давно не продавались И не отправлялись на базар.
    """
    from finance.models import BazarSaleItem, SaleItem
    from inventory.models import Product

    today = date.today()
    date_from = today - timedelta(days=days_threshold)

    # Товары которые продавались на базаре
    sold_ids = set(
        BazarSaleItem.objects.filter(
            sale__sale_date__gte=date_from,
            sale__sale_date__lte=today,
        ).values_list('product_id', flat=True).distinct()
    )

    # Товары которые отправлялись (ketuvlar)
    shipped_ids = set(
        SaleItem.objects.filter(
            sale__note__startswith='Bozorga',
            sale__sale_date__gte=date_from,
            sale__sale_date__lte=today,
        ).values_list('product_id', flat=True).distinct()
    )

    # Исключаем оба — ни продано, ни отправлено
    active_ids = sold_ids | shipped_ids

    slow_products = Product.objects.filter(
        is_active=True,
        stock__gt=0,
    ).exclude(id__in=active_ids).select_related('category')

    results = []
    for p in slow_products:
        per_box = p.per_box if p.per_box > 0 else 1

        # Последняя продажа на базаре
        last_bazar = BazarSaleItem.objects.filter(product=p).order_by('-sale__sale_date').select_related('sale').first()
        # Последняя отправка
        last_ship = SaleItem.objects.filter(
            product=p, sale__note__startswith='Bozorga'
        ).order_by('-sale__sale_date').select_related('sale').first()

        if last_bazar:
            last_sale_date = str(last_bazar.sale.sale_date)
            days_since_sale = (today - last_bazar.sale.sale_date).days
        else:
            last_sale_date = 'hech qachon'
            days_since_sale = None

        if last_ship:
            last_ship_date = str(last_ship.sale.sale_date)
            days_since_ship = (today - last_ship.sale.sale_date).days
        else:
            last_ship_date = 'hech qachon'
            days_since_ship = None

        results.append({
            'product': p.name,
            'stock': p.stock,
            'stock_boxes': p.stock // per_box,
            'stock_value': p.stock * p.sell_price,
            'last_sale_date': last_sale_date,
            'days_since_last_sale': days_since_sale,
            'last_shipment_date': last_ship_date,
            'days_since_last_shipment': days_since_ship,
            'category': p.category.name if p.category else '',
        })

    results.sort(key=lambda x: x['stock_value'], reverse=True)

    total_value = sum(r['stock_value'] for r in results)

    return {
        'threshold_days': days_threshold,
        'slow_moving_count': len(results),
        'total_frozen_value': total_value,
        'products': results[:limit],
    }


def get_unsold_products(period: str = 'oy', limit: int = 30) -> dict:
    """
    Все активные товары которые не продавались за период.
    Показывает и те у кого есть остаток, и те у кого нет.
    """
    from finance.models import BazarSaleItem
    from inventory.models import Product

    date_from, date_to = _parse_period(period)

    sold_ids = set(
        BazarSaleItem.objects.filter(
            sale__sale_date__gte=date_from,
            sale__sale_date__lte=date_to,
        ).values_list('product_id', flat=True).distinct()
    )

    total_active = Product.objects.filter(is_active=True).count()

    unsold = Product.objects.filter(
        is_active=True,
    ).exclude(id__in=sold_ids).select_related('category')

    results = []
    for p in unsold:
        per_box = p.per_box if p.per_box > 0 else 1
        results.append({
            'product': p.name,
            'stock': p.stock,
            'stock_boxes': p.stock // per_box,
            'stock_value': p.stock * p.sell_price,
            'category': p.category.name if p.category else '',
            'has_stock': p.stock > 0,
        })

    results.sort(key=lambda x: (-x['stock_value'], x['product']))

    with_stock = [r for r in results if r['has_stock']]
    without_stock = [r for r in results if not r['has_stock']]

    return {
        'period': f'{date_from} — {date_to}',
        'total_active_products': total_active,
        'sold_products_count': len(sold_ids),
        'unsold_count': len(results),
        'unsold_with_stock': len(with_stock),
        'unsold_without_stock': len(without_stock),
        'total_frozen_value': sum(r['stock_value'] for r in with_stock),
        'products': results[:limit],
    }


def get_shipment_vs_sales(period: str = 'oy', limit: int = 20) -> dict:
    """
    Сравнение: сколько отправлено на базар vs сколько продано.
    Показывает эффективность каждого товара.
    """
    from finance.models import SaleItem, BazarSaleItem

    date_from, date_to = _parse_period(period)

    shipped_qs = SaleItem.objects.filter(
        sale__note__startswith='Bozorga',
        sale__sale_date__gte=date_from,
        sale__sale_date__lte=date_to,
    ).values('product__id', 'product__name', 'product__per_box').annotate(
        shipped_qty=Sum('quantity'),
        shipped_sum=Sum('total'),
    )

    sold_qs = BazarSaleItem.objects.filter(
        sale__sale_date__gte=date_from,
        sale__sale_date__lte=date_to,
    ).values('product__id', 'product__name', 'product__per_box').annotate(
        sold_qty=Sum('quantity'),
        sold_sum=Sum('total'),
    )

    shipped_map = {item['product__id']: item for item in shipped_qs}
    sold_map = {item['product__id']: item for item in sold_qs}

    all_ids = set(shipped_map.keys()) | set(sold_map.keys())

    results = []
    for pid in all_ids:
        s = shipped_map.get(pid, {})
        b = sold_map.get(pid, {})

        shipped_qty = s.get('shipped_qty') or 0
        sold_qty = b.get('sold_qty') or 0
        per_box = s.get('product__per_box') or b.get('product__per_box') or 1
        if per_box == 0:
            per_box = 1
        product_name = s.get('product__name') or b.get('product__name', '')

        if shipped_qty > 0:
            efficiency = round(sold_qty / shipped_qty * 100, 1)
            remaining = shipped_qty - sold_qty
        else:
            efficiency = None
            remaining = None

        results.append({
            'product': product_name,
            'shipped_qty': shipped_qty,
            'shipped_boxes': shipped_qty // per_box,
            'sold_qty': sold_qty,
            'sold_boxes': sold_qty // per_box,
            'efficiency_pct': efficiency,
            'remaining_on_bazar': remaining,
            'remaining_boxes': remaining // per_box if remaining is not None else None,
        })

    results.sort(key=lambda x: (x['efficiency_pct'] is None, -(x['efficiency_pct'] or 0)))

    total_shipped = sum(r['shipped_qty'] for r in results)
    total_sold = sum(r['sold_qty'] for r in results)

    return {
        'period': f'{date_from} — {date_to}',
        'total_shipped_qty': total_shipped,
        'total_sold_qty': total_sold,
        'overall_efficiency': round(total_sold / total_shipped * 100, 1) if total_shipped > 0 else 0,
        'products_count': len(results),
        'products': results[:limit],
    }


def get_monthly_trend(months: int = 6) -> dict:
    """
    Помесячная статистика продаж за последние N месяцев.
    """
    from finance.models import BazarSale
    from django.db.models.functions import TruncMonth

    today = date.today()

    # Начало периода: первый день месяца N месяцев назад
    year = today.year
    month = today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    date_from = date(year, month, 1)

    monthly = BazarSale.objects.filter(
        sale_date__gte=date_from,
    ).annotate(
        month=TruncMonth('sale_date'),
    ).values('month').annotate(
        total=Sum('total_amount'),
        count=Count('id'),
        paid=Sum('total_amount', filter=Q(payment_status='paid')),
        debt=Sum('total_amount', filter=Q(payment_status='debt')),
    ).order_by('month')

    result = []
    for m in monthly:
        dt = m['month']
        result.append({
            'month': dt.strftime('%Y-%m') if dt else '',
            'month_name': dt.strftime('%B %Y') if dt else '',
            'total': m['total'] or 0,
            'transactions': m['count'] or 0,
            'paid': m['paid'] or 0,
            'debt': m['debt'] or 0,
        })

    trend_pct = 0
    if len(result) >= 2:
        last_total = result[-1]['total']
        prev_total = result[-2]['total']
        if prev_total > 0:
            trend_pct = round((last_total - prev_total) / prev_total * 100, 1)

    return {
        'months_count': months,
        'monthly_data': result,
        'trend_vs_prev_month': trend_pct,
        'best_month': max(result, key=lambda x: x['total']) if result else None,
        'worst_month': min(result, key=lambda x: x['total']) if result else None,
        'total_for_period': sum(r['total'] for r in result),
    }


def get_product_full_stats(product_name: str, period: str = 'barchasi') -> dict:
    """
    Полная статистика по конкретному товару: склад, продажи, отправки, цены, долги, тренд.
    """
    from finance.models import BazarSaleItem, SaleItem
    from inventory.models import Product, PriceHistory

    today = date.today()
    date_from, date_to = _parse_period(period)

    # Поиск товара
    products = Product.objects.filter(name__icontains=product_name, is_active=True)
    if not products.exists():
        words = product_name.split()
        q = Q(is_active=True)
        for word in words:
            q &= Q(name__icontains=word)
        products = Product.objects.filter(q)
    if not products.exists() and len(product_name) > 2:
        first_word = product_name.split()[0] if product_name.split() else product_name
        products = Product.objects.filter(name__icontains=first_word, is_active=True)

    if not products.exists():
        all_products = Product.objects.filter(is_active=True).values_list('name', flat=True)[:50]
        return {'error': f'Tovar "{product_name}" topilmadi', 'available_products': list(all_products)}

    results = []
    for product in products[:3]:
        per_box = product.per_box if product.per_box > 0 else 1

        # --- 1. Склад ---
        stock_info = {
            'stock': product.stock,
            'stock_boxes': product.stock // per_box,
            'stock_value': product.stock * product.sell_price,
            'sell_price': product.sell_price,
            'per_box': per_box,
            'min_stock': product.min_stock,
            'is_low_stock': product.is_low_stock,
            'category': product.category.name if product.category else '',
            'unit': product.unit.short_name if product.unit else '',
        }

        # --- 2. Продажи на базаре (BazarSaleItem) ---
        bazar_agg = BazarSaleItem.objects.filter(
            product=product,
            sale__sale_date__gte=date_from,
            sale__sale_date__lte=date_to,
        ).aggregate(
            total_qty=Sum('quantity'),
            total_sum=Sum('total'),
            count=Count('id'),
        )
        bazar_qty = bazar_agg['total_qty'] or 0

        # По магазинам (продажи)
        from finance.models import Shop
        shops_sales = []
        for shop in Shop.objects.all():
            s = BazarSaleItem.objects.filter(
                product=product,
                sale__shop=shop,
                sale__sale_date__gte=date_from,
                sale__sale_date__lte=date_to,
            ).aggregate(qty=Sum('quantity'), total=Sum('total'))
            if s['qty']:
                shops_sales.append({
                    'shop': shop.name,
                    'qty': s['qty'] or 0,
                    'boxes': (s['qty'] or 0) // per_box,
                    'total': s['total'] or 0,
                })

        # Последние продажи (5 шт)
        recent_sales = []
        for item in BazarSaleItem.objects.filter(product=product).order_by('-sale__sale_date').select_related('sale', 'sale__shop')[:5]:
            recent_sales.append({
                'date': str(item.sale.sale_date),
                'qty': item.quantity,
                'boxes': item.quantity // per_box,
                'price': item.price,
                'total': item.total,
                'shop': item.sale.shop.name if item.sale.shop else '',
                'client': item.sale.client_name or '',
            })

        sales_info = {
            'total_qty': bazar_qty,
            'total_boxes': bazar_qty // per_box,
            'total_sum': bazar_agg['total_sum'] or 0,
            'transactions': bazar_agg['count'] or 0,
            'by_shop': shops_sales,
            'recent': recent_sales,
        }

        # --- 3. Отправки на базар (ketuvlar) ---
        ship_agg = SaleItem.objects.filter(
            product=product,
            sale__note__startswith='Bozorga',
            sale__sale_date__gte=date_from,
            sale__sale_date__lte=date_to,
        ).aggregate(
            total_qty=Sum('quantity'),
            total_sum=Sum('total'),
            count=Count('id'),
        )
        ship_qty = ship_agg['total_qty'] or 0

        # По магазинам (отправки)
        shops_ship = []
        for shop in Shop.objects.all():
            s = SaleItem.objects.filter(
                product=product,
                sale__note__startswith='Bozorga',
                sale__note__contains=shop.name,
                sale__sale_date__gte=date_from,
                sale__sale_date__lte=date_to,
            ).aggregate(qty=Sum('quantity'), total=Sum('total'))
            if s['qty']:
                shops_ship.append({
                    'shop': shop.name,
                    'qty': s['qty'] or 0,
                    'boxes': (s['qty'] or 0) // per_box,
                    'total': s['total'] or 0,
                })

        # Последние отправки (5 шт)
        recent_shipments = []
        for item in SaleItem.objects.filter(
            product=product, sale__note__startswith='Bozorga'
        ).order_by('-sale__sale_date').select_related('sale')[:5]:
            recent_shipments.append({
                'date': str(item.sale.sale_date),
                'qty': item.quantity,
                'boxes': item.quantity // per_box,
                'price': item.price,
                'total': item.total,
                'destination': item.sale.note,
            })

        shipments_info = {
            'total_qty': ship_qty,
            'total_boxes': ship_qty // per_box,
            'total_sum': ship_agg['total_sum'] or 0,
            'shipments_count': ship_agg['count'] or 0,
            'by_shop': shops_ship,
            'recent': recent_shipments,
        }

        # --- 4. Отправлено vs продано (эффективность) ---
        efficiency = round(bazar_qty / ship_qty * 100, 1) if ship_qty > 0 else None

        # --- 5. Прогноз запасов ---
        last_30_sold = BazarSaleItem.objects.filter(
            product=product,
            sale__sale_date__gte=today - timedelta(days=30),
            sale__sale_date__lte=today,
        ).aggregate(total=Sum('quantity'))['total'] or 0
        daily_avg = round(last_30_sold / 30, 1)
        if daily_avg > 0:
            days_left = round(product.stock / daily_avg)
            runs_out = str(today + timedelta(days=days_left))
        else:
            days_left = None
            runs_out = None

        forecast_info = {
            'sold_last_30_days': last_30_sold,
            'daily_avg': daily_avg,
            'days_left': days_left,
            'runs_out_date': runs_out,
        }

        # --- 6. История цен ---
        price_history = []
        for ch in PriceHistory.objects.filter(product=product).order_by('-changed_at')[:5]:
            price_history.append({
                'old_price': ch.old_price,
                'new_price': ch.new_price,
                'change': ch.new_price - ch.old_price,
                'date': ch.changed_at.strftime('%d.%m.%Y'),
            })

        # --- 7. Долги по этому товару ---
        debt_items = BazarSaleItem.objects.filter(
            product=product,
            sale__payment_status='debt',
        ).aggregate(qty=Sum('quantity'), total=Sum('total'), count=Count('id'))

        debts_info = {
            'debt_qty': debt_items['qty'] or 0,
            'debt_sum': debt_items['total'] or 0,
            'debt_transactions': debt_items['count'] or 0,
        }

        # --- 8. Месячный тренд (последние 4 месяца) ---
        from django.db.models.functions import TruncMonth
        monthly = BazarSaleItem.objects.filter(
            product=product,
        ).annotate(
            month=TruncMonth('sale__sale_date'),
        ).values('month').annotate(
            qty=Sum('quantity'),
            total=Sum('total'),
        ).order_by('-month')[:4]

        monthly_trend = []
        for m in monthly:
            dt = m['month']
            monthly_trend.append({
                'month': dt.strftime('%Y-%m') if dt else '',
                'qty': m['qty'] or 0,
                'boxes': (m['qty'] or 0) // per_box,
                'total': m['total'] or 0,
            })
        monthly_trend.reverse()

        results.append({
            'product': product.name,
            'period': f'{date_from} — {date_to}',
            'stock': stock_info,
            'sales': sales_info,
            'shipments': shipments_info,
            'efficiency_pct': efficiency,
            'forecast': forecast_info,
            'price_history': price_history,
            'debts': debts_info,
            'monthly_trend': monthly_trend,
        })

    return {'results': results}


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
    'get_product_shipments': get_product_shipments,
    'get_stock_forecast': get_stock_forecast,
    'get_slow_moving_products': get_slow_moving_products,
    'get_unsold_products': get_unsold_products,
    'get_shipment_vs_sales': get_shipment_vs_sales,
    'get_monthly_trend': get_monthly_trend,
    'get_product_full_stats': get_product_full_stats,
}