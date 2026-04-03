from django.shortcuts import redirect, render


class ZoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем login, logout, admin, api
        path = request.path
        skip_paths = ['/login/', '/logout/', '/admin/', '/api/']
        if any(path.startswith(p) for p in skip_paths):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return self.get_response(request)

        zone = request.session.get('zone', 'sklad')

        # Бозарщик пытается зайти на склад
        sklad_paths = ['/', '/tovar/', '/bozorga-ketish/', '/bozorga-ketuvlar/', '/xabar/bozorga/']
        is_sklad_page = any(path == p or path.startswith(p) for p in sklad_paths) and not path.startswith('/bozor/')

        if zone == 'bozor' and is_sklad_page:
            if request.method == 'POST':
                password = request.POST.get('sklad_password', '')
                from accounts.models import User
                for user in User.objects.filter(is_active=True):
                    if user.check_password(password):
                        request.session['zone'] = 'sklad'
                        return redirect(path)
                return render(request, 'accounts/zone_block.html', {
                    'error': 'Parol noto\'g\'ri!',
                    'target': path,
                })
            return render(request, 'accounts/zone_block.html', {
                'target': path,
            })

        return self.get_response(request)