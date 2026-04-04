from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout


def login_view(request):
    error = ''
    if request.method == 'POST':
        password = request.POST.get('password', '')

        from .models import User
        for user in User.objects.filter(is_active=True):
            if user.check_password(password):
                login(request, user)
                # Запоминаем зону доступа
                request.session['zone'] = 'sklad'
                return redirect('/')

        # Проверяем пароли бозара
        BOZOR_PASSWORDS = {
            'bozor389': 3899,  # пароль: bozor1 -> магазин с id=1
            'bozor184': 1844,  # пароль: bozor2 -> магазин с id=2
        }

        if password in BOZOR_PASSWORDS:
            # Логиним под первым активным пользователем
            user = User.objects.filter(is_active=True).first()
            if user:
                login(request, user)
                shop_id = BOZOR_PASSWORDS[password]
                request.session['zone'] = 'bozor'
                request.session['shop_id'] = shop_id
                return redirect(f'/bozor/{shop_id}/')

        error = 'Parol noto\'g\'ri'

    return render(request, 'accounts/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')