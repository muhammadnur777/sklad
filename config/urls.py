

from django.contrib import admin
from django.urls import path, include
from inventory.views import ai_chat_api
from inventory.views import (
    product_price_api, bozor_send_api, download_sale_excel,
    bazar_sell_api, bazar_sale_detail_api, bazar_mark_paid_api,
    xabar_count_api, xabar_read_api, delete_old_records, product_stats_api
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/product-price/<int:product_id>/', product_price_api, name='product_price_api'),
    path('api/bozor-send/', bozor_send_api, name='bozor_send_api'),
    path('api/download-excel/<int:sale_id>/', download_sale_excel, name='download_sale_excel'),
    path('api/bazar-sell/', bazar_sell_api, name='bazar_sell_api'),
    path('api/bazar-sale-detail/<int:sale_id>/', bazar_sale_detail_api, name='bazar_sale_detail'),
    path('api/bazar-mark-paid/<int:sale_id>/', bazar_mark_paid_api, name='bazar_mark_paid'),
    path('api/xabar-count/', xabar_count_api, name='xabar_count'),
    path('api/xabar-read/', xabar_read_api, name='xabar_read'),
    path('', include('accounts.urls')),
    path('', include('inventory.urls')),
    path('api/delete-old-records/', delete_old_records, name='delete_old_records'),
    path('api/product-stats/<int:product_id>/', product_stats_api, name='product_stats'),
    path('api/ai-chat/', ai_chat_api, name='ai_chat'),
]