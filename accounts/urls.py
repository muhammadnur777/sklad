from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('bozor/login/', views.bozor_login_view, name='bozor_login'),
    path('logout/', views.logout_view, name='logout'),
]