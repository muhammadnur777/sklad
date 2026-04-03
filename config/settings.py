from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-k)tw^d1927c27(j-%yos%&t@s!si0sd$se5=x4!^1p&8=8axfk'

DEBUG = True

ALLOWED_HOSTS = []


# ───────────────────────────────────────────
# ПРИЛОЖЕНИЯ
# ───────────────────────────────────────────

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Наши приложения
    'accounts',
    'inventory',
    'finance',
    'reports',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.ZoneMiddleware',  # наша кастомная middleware для зон доступа
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # папка templates в корне
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ───────────────────────────────────────────
# БАЗА ДАННЫХ — PostgreSQL
# ───────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sklad_db',
        'USER': 'postgres',
        'PASSWORD': '8743',   # <-- сюда вставь свой пароль
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# ───────────────────────────────────────────
# КАСТОМНАЯ МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ
# ───────────────────────────────────────────

AUTH_USER_MODEL = 'accounts.User'


# ───────────────────────────────────────────
# ПАРОЛИ
# ───────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = []

# ───────────────────────────────────────────
# ЯЗЫК И ВРЕМЯ
# ───────────────────────────────────────────

LANGUAGE_CODE = 'uz'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


# ───────────────────────────────────────────
# СТАТИКА И МЕДИА
# ───────────────────────────────────────────

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ───────────────────────────────────────────
# АВТОРИЗАЦИЯ
# ───────────────────────────────────────────

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


JAZZMIN_SETTINGS = {
    'site_title': 'SKLAD Admin',
    'site_header': 'SKLAD',
    'site_brand': 'SKLAD',
    'welcome_sign': 'SKLAD tizimiga xush kelibsiz',
    'copyright': 'SKLAD',
    'search_model': 'inventory.Product',
    'topmenu_links': [
        {'name': 'Saytga qaytish', 'url': '/'},
    ],
    'show_ui_builder': False,
    'icons': {
        'accounts.User': 'fas fa-user',
        'inventory.Product': 'fas fa-box',
        'inventory.Category': 'fas fa-tags',
        'inventory.Unit': 'fas fa-ruler',
        'finance.Sale': 'fas fa-shopping-cart',
        'finance.Purchase': 'fas fa-truck',
        'finance.StockMovement': 'fas fa-history',
    },
    'hide_models': ['auth.Group'],
    'changeform_format': 'single',
}

JAZZMIN_UI_TWEAKS = {
    'theme': 'lightly',
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-outline-success',
    },
    'accent': 'accent-danger',
    'custom_css': 'css/admin-custom.css',
}