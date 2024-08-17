from django.apps import AppConfig


class ReportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'report'


class ReportCategoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'report_for_category'
