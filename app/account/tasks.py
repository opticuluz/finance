# from celery import shared_task
# from celery.utils.log import get_task_logger
from finance.celery import app
from account.admin import update_all_rates


# # logger = get_task_logger(__name__)


@app.task
def update_rates():
    update_all_rates()
    # logger.info("The sample task just ran.")


# from django.utils.module_loading import import_string

# from celery import Celery
# from djmoney import settings


# app = Celery('tasks', broker='pyamqp://guest@localhost//')


# @app.task
# def update_rates(backend=settings.EXCHANGE_BACKEND, **kwargs):
#               'djmoney.contrib.exchange.backends.FixerBackend'
#     backend = import_string(backend)()
#     backend.update_rates(**kwargs)

# from celery import shared_task
# from django.utils.module_loading import import_string
# from finance import settings

# @shared_task
# def update_rates(backend=settings.EXCHANGE_BACKEND, **kwargs):
#     backend = import_string(backend)()
#     # FixerBackend().update_rates(**kwargs)
#     backend.update_rates(**kwargs)
