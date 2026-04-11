from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('tovar/qoshish/', views.add_product, name='add_product'),
    path('tovar/toldirish/', views.refill_product, name='refill_product'),
    path('bozorga-ketish/', views.bozor_page, name='bozor_page'),
    path('bozor/<int:shop_id>/', views.bozordagi_tovarlar, name='bozordagi_tovarlar'),
    path('bozor/<int:shop_id>/sotuvlar/', views.bozor_sotuvlar, name='bozor_sotuvlar'),
    path('bozor/<int:shop_id>/qarzdorlar/', views.qarzdorlar_page, name='qarzdorlar'),
    path('bozor/<int:shop_id>/xabar/', views.xabar_page, name='xabar_skladga'),
    path('xabar/bozorga/', views.xabar_page, name='xabar_bozorga'),
    path('bozorga-ketuvlar/', views.bozorga_ketuvlar, name='bozorga_ketuvlar'),
    path('api/delete-old-records/', views.delete_old_records, name='delete_old_records'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/oylik-sotuvlar/', views.monthly_sales, name='monthly_sales'),
    path('bozor/<int:shop_id>/tovar-qoshish/', views.bazar_add_product, name='bazar_add_product'),
    path('bozorga-ketuvlar/pullar/', views.payment_history, name='payment_history'),
    path('ai-chat/', views.ai_chat_page, name='ai_chat'),
]