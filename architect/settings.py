

TSD_TYPE = 'Graphite'
GRAPHITE_HOST = '172.17.0.2'
GRAPHITE_INJEST_PORT = 2004
GRAPHITE_HTTP_PORT = 80
OPENTSD_HOST = '127.0.0.1'
OPENTSD_PORT = 4242

CONTRACTOR_HOST = 'http://127.0.0.1:8888'
CONTRACTOR_ROOT_PATH = '/api/v1/'
CONTRACTOR_PROXY = None

PROJECT_PATH = '/home/peter/Projects/t3kton/architect/lib/demo_test/auto_demo_load/'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@(a3yjcc(d3uxt)c7n(0vdfhe!$%u2(dvk^9^cg26+4wmih6l7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'architect.User',
    'architect.Project',
    'architect.Contractor',
    'architect.TimeSeries',
    'architect.Plan',
    'architect.Builder',
    'architect.Inspector',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'architect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'architect.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/opt/architect/db.sqlite3',
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
