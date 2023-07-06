from django.contrib import admin, messages
from .models import Account, Currency
from core.mixins import UserRestrictedAdminMixin
from cashflow.models import Cashflow
from django.conf import settings
from djmoney.contrib.exchange.models import get_rate
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum, Q
from report.models import Report


class CashflowInline(admin.TabularInline):
    model = Cashflow
    fk_name = 'charged_account'
    readonly_fields = [
        'created_at',
        'payment_type',
        'charged_account',
        'targed_account',
        'amount',
        'amount_in_base_currency',
        'category',
        'date',
        'note'
        ]
    can_delete = False
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['user']
        return self.readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.order_by('-created_at')
        return queryset


class CashflowTargedInline(admin.TabularInline):
    model = Cashflow
    fk_name = 'targed_account'
    readonly_fields = [
        'created_at',
        'payment_type',
        'charged_account',
        'targed_account',
        'amount',
        'amount_in_base_currency',
        'category',
        'date',
        'note'
        ]
    can_delete = False
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        if obj:  # obj will be None when creating a new Account
            return self.readonly_fields + ['user']
        return self.readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.order_by('-created_at')
        return queryset


class AccountAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):
    ordering = ['-created_at']
    list_display = [
        'account_name',
        'balance',
        'currency',
        'balance_in_base_currency',
        'include_balance_in_current_month'
        ]
    list_filter = ['account_name', 'include_balance_in_current_month', 'user']
    search_fields = ['account_name', 'user']
    readonly_fields = [
        'balance',
        'balance_in_base_currency',
        'user',
        'created_at',
        'updated_at'
        ]
    inlines = [CashflowInline, CashflowTargedInline]

    def save_model(self, request, obj, form, change):
        if obj.currency.title == settings.BASE_CURRENCY:
            obj.balance_in_base_currency = obj.balance
        else:
            rate = get_rate(obj.currency.title, settings.BASE_CURRENCY)
            obj.balance_in_base_currency = Decimal(obj.balance) * rate
        super().save_model(request, obj, form, change)

    actions = ['recalculate_balance_in_base_currency', 'create_report']

    def recalculate_balance_in_base_currency(self, request, queryset):
        for account in queryset:
            if account.currency.title == settings.BASE_CURRENCY:
                account.balance_in_base_currency = account.balance
            else:
                rate = get_rate(account.currency.title, settings.BASE_CURRENCY)
                if rate:
                    account.balance_in_base_currency = account.balance * rate
                else:
                    messages.warning(
                        request,
                        f"Rate not found for {account.currency.title}"
                        )
                    continue
            account.save()
        messages.success(
            request,
            "Balance in base currency recalculated for selected accounts."
            )

    recalculate_balance_in_base_currency.short_description = (
        "Recalculate balance in base currency"
        )

    def create_report(self, request, queryset):
        current_month_start = datetime.now().replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
            )
        income = queryset.annotate(
            total_income=Sum(
                'charged_cashflows__amount_in_base_currency',
                filter=Q(
                    charged_cashflows__payment_type='income',
                    charged_cashflows__date__gte=current_month_start
                    )
                )
        ).values('total_income').aggregate(
            Sum('total_income')
            )['total_income__sum'] or 0.0
        expenses = queryset.annotate(
            total_expenses=Sum(
                'charged_cashflows__amount_in_base_currency',
                filter=Q(
                    charged_cashflows__payment_type='expenses',
                    charged_cashflows__date__gte=current_month_start
                    )
                )
        ).values('total_expenses').aggregate(
            Sum('total_expenses')
            )['total_expenses__sum'] or 0.0
        total_balance = queryset.filter(
            user=request.user
            ).aggregate(
            total_balance=Sum('balance_in_base_currency')
            )['total_balance'] or 0.0

        messages.success(request, "Report created successfully.")

        report = Report.objects.filter(
            user=request.user,
            created_at__year=current_month_start.year,
            created_at__month=current_month_start.month
        ).last()

        if report:
            report.total_balance_in_base_currency = total_balance
            report.income_in_current_month = income
            report.expenses_in_current_month = expenses
            report.save()
        else:
            report = Report.objects.create(
                user=request.user,
                total_balance_in_base_currency=total_balance,
                income_in_current_month=income,
                expenses_in_current_month=expenses
            )
            report.save()

    create_report.short_description = "Create report"


admin.site.register(Account, AccountAdmin)


class CurrencyAdmin(admin.ModelAdmin):
    ordering = ['title']
    list_display = ['title', 'symbol']
    search_fields = ['title']


admin.site.register(Currency, CurrencyAdmin)
