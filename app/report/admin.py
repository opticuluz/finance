from django.contrib import admin
from .models import Report
from core.mixins import UserRestrictedAdminMixin


class ReportAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):
    ordering = ['-created_at']
    list_display = [
        'created_at',
        'user',
        'income_in_current_month',
        'expenses_in_current_month',
        'total_balance_in_base_currency',
        ]
    list_filter = ['user']
    search_fields = ['user']
    readonly_fields = [
        'user',
        'income_in_current_month',
        'expenses_in_current_month',
        'total_balance_in_base_currency',
        'created_at',
        'updated_at'
        ]


admin.site.register(Report, ReportAdmin)
