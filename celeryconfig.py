CELERY_RESULT_BACKEND = "alchemy_backend.CeleryBackend"

CARROT_BACKEND = "alchemy_backend.CarrotBackend"
INSTALLED_APPS = ("celery", "ghettoq", )

CELERY_IMPORTS = ("tasks", )

#CELERYD_LOG_FILE = "celery.log"
#CELERYD_LOG_LEVEL = "DEBUG"

