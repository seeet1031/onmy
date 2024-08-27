import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = True
#ALLOWED_HOSTS = ['ONMY2.us-east-1.elasticbeanstalk.com']
ALLOWED_HOSTS = []
AUTH_USER_MODEL = 'accounts.CustomUser'
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'appointments',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'onmy_database',
        'USER': 'root',
        'PASSWORD': 'king1031',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_L10N = True
USE_TZ = True
# サポートする言語の設定
LANGUAGES = [
    ('ja', 'Japanese'),
    ('en', 'English'),
    ('zh', 'Chinese'),
]
# 翻訳ファイルの保存場所
LOCALE_PATHS = [
    BASE_DIR / 'locale/',
]
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGOUT_REDIRECT_URL = 'user_login'
ADMIN_LOGOUT_REDIRECT_URL = '/admin/login/'
# Stripe設定
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', 'pk_test_51PmKavP8rwl4UjKOU4gqYh2TUFKKPwV2sspsMGP9qbVlhAnJOikUQMUUvnw9bUQ7RQkH4ELqjLwUJFaQLbw0BQ5v003XxHB0rZ')

GOOGLE_CLIENT_ID = '229045251836-fkfn0d3a5bcqcvj70ehb9kmsoonv1fjb.apps.googleusercontent.com'
GOOGLE_REDIRECT_URI = 'http://localhost:8000/callback'
GOOGLE_REFRESH_TOKEN="1//0eflCikgt6wE_CgYIARAAGA4SNwF-L9IrT1qecSSnoj34jRrSChXCC4FY6p7CZqOs6dnaKGjd94nuFThA5f3JjFYDT-7_QI6P_Yo"


# Google API Credentials Path
GOOGLE_API_CREDENTIALS = os.path.join(BASE_DIR, 'credentials.json')

# Google Calendar API Scopes
GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']


# 環境変数を読み込むための設定
env = environ.Env()

# プロジェクトのベースディレクトリを指定して.envファイルを読み込む
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# 機密情報を環境変数から取得
SECRET_KEY = env('DJANGO_SECRET_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
GOOGLE_CLIENT_SECRET = env('GOOGLE_CLIENT_SECRET')

