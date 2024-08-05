from django.contrib import admin
from .models import Report
from user.mixins import UserRestrictedAdminMixin


class ReportAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):
    ordering = ['-created_at']
    list_display = [
        'created_at',
        'income_in_current_month',
        'expenses_in_current_month',
        'income_in_current_year',
        'expenses_in_current_year',
        'total_balance_in_base_currency',
        'total_available_balance_in_base_currency',
        'updated_at'
        ]
    list_filter = ['user']
    search_fields = ['user']
    readonly_fields = [
        'user',
        'income_in_current_month',
        'expenses_in_current_month',
        'income_in_current_year',
        'expenses_in_current_year',
        'total_balance_in_base_currency',
        'total_available_balance_in_base_currency',
        'created_at',
        'updated_at'
        ]


admin.site.register(Report, ReportAdmin)
