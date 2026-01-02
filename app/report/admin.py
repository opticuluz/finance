from django.contrib import admin
from .models import Report, Report_for_category
from user.mixins import UserRestrictedAdminMixin
from payment.admin import UserCategoryFilter
from django.db.models import F
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from datetime import datetime
from django.utils.http import urlencode
from django.shortcuts import redirect
from rangefilter.filters import DateRangeFilterBuilder
from django.utils.formats import get_format


class ReportAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):
    ordering = ['-created_at']

    def changelist_view(self, request, extra_context=None):
        if (
            'created_at__range__gte' not in request.GET
            and 'created_at__range__lte' not in request.GET
        ):
            input_formats = get_format('DATE_INPUT_FORMATS')
            date_fmt = input_formats[0] if input_formats else '%Y-%m-%d'
            current_year = now().year
            start_date = datetime(current_year, 1, 1).strftime(date_fmt)
            params = dict(request.GET.copy())
            params['created_at__range__gte'] = start_date
            return redirect(f"{request.path}?{urlencode(params)}")
        return super().changelist_view(request, extra_context)

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
    list_filter = [("created_at", DateRangeFilterBuilder()), 'user']
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
        ).filter(
            average_for_year__gt=0
        )
        return qs.order_by(
            '-created_at_month',
            '-changes_in_category_for_current_month',
            '-average_for_year'
            )

    def changelist_view(self, request, extra_context=None):
        if (
            'created_at__range__gte' not in request.GET
            and 'created_at__range__lte' not in request.GET
        ):
            input_formats = get_format('DATE_INPUT_FORMATS')
            date_fmt = input_formats[0] if input_formats else '%Y-%m-%d'
            current_year = now().year
            current_month = now().month
            start_date = datetime(
                current_year,
                current_month,
                1
                ).strftime(date_fmt)
            params = dict(request.GET.copy())
            params['created_at__range__gte'] = start_date
            return redirect(f"{request.path}?{urlencode(params)}")
        return super().changelist_view(request, extra_context)

    list_display = [
        'created_at',
        'category',
        'changes_in_category_for_current_month',
        'average_for_year',
        'updated_at'
        ]
    list_filter = [
        ("created_at", DateRangeFilterBuilder()),
        UserCategoryFilter,
        'user'
        ]
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
