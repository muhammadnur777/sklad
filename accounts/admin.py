
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from .models import User


# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     list_display = ['username', 'role', 'is_active']
#     list_filter = ['role', 'is_active']
#     fieldsets = (
#         (None, {'fields': ('username', 'password')}),
#         ('Rol', {'fields': ('role',)}),
#         ('Ruxsatlar', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
#     )
#     add_fieldsets = (
#         (None, {'fields': ('username', 'password1', 'password2', 'role')}),
#     )

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Rol', {'fields': ('role',)}),
        ('Ruxsatlar', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2', 'role')}),
    )

    SECRET_PASSWORD = 'admin777'

    def get_urls(self):
        custom_urls = [
            path('verify/', self.admin_site.admin_view(self.verify_view), name='accounts_user_verify'),
        ]
        return custom_urls + super().get_urls()

    def verify_view(self, request):
        if request.method == 'POST':
            password = request.POST.get('password', '')
            if password == self.SECRET_PASSWORD:
                request.session['users_verified'] = True
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
        if not request.session.get('users_verified'):
            return HttpResponseRedirect('verify/')
        return super().changelist_view(request, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        if not request.session.get('users_verified'):
            return HttpResponseRedirect('../verify/')
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not request.session.get('users_verified'):
            return HttpResponseRedirect('../verify/')
        return super().change_view(request, object_id, form_url, extra_context)