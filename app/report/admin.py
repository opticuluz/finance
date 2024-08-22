from django.contrib import admin
from .models import Report, Report_for_category
from user.mixins import UserRestrictedAdminMixin
from payment.admin import UserCategoryFilter
from django.db.models import F
from django.db.models.functions import TruncMonth


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


class ReportCategoryAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    ordering = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            created_at_month=TruncMonth(F('created_at'))
        )
        return qs.order_by(
            '-created_at_month',
            '-changes_in_category_for_current_month',
            '-average_for_year'
            )

    list_display = [
        'created_at',
        'category',
        'changes_in_category_for_current_month',
        'average_for_year',
        'updated_at'
        ]
    list_filter = ['created_at', UserCategoryFilter, 'user']
    search_fields = ['category']
    readonly_fields = [
        'user',
        'category',
        'changes_in_category_for_current_month',
        'average_for_year',
        'created_at',
        'updated_at'
    ]


admin.site.register(Report_for_category, ReportCategoryAdmin)
