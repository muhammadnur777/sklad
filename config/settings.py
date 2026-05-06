from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())



INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.contrib.humanize', # https://django-humaze.readthedocs.io/en/latest/
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
    'accounts.middleware.ZoneMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}



BOZOR_PASSWORDS = {
    config('BOZOR_1_PASSWORD'): 1,
    config('BOZOR_2_PASSWORD'): 2,
}


AUTH_USER_MODEL = 'accounts.User'



AUTH_PASSWORD_VALIDATORS = []


LANGUAGE_CODE = 'uz'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True




STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



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
    'theme': 'cosmo',
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