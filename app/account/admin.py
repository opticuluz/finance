from django.contrib import admin, messages
from .models import Account, Currency
from core.mixins import UserRestrictedAdminMixin
from cashflow.models import Cashflow
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum, Q, Case, When, Value
from django.db import models
from report.models import Report
from constance import config
from django.utils.translation import gettext_lazy as _


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


def base_currency_rate():
    base_currency = config.BASE_CURRENCY
    try:
        base_currency_obj = Currency.objects.get(title=base_currency)
        if base_currency_obj.rate:
            return base_currency_obj.rate
        else:
            messages.warning(
                # request,
                _("Rate not found for %(currency)s")
                %
                {'currency': base_currency}
            )
    except Currency.DoesNotExist:
        messages.warning(
            # request,
            _("Base currency %(currency)s not found")
            %
            {'currency': base_currency}
        )

    return None


class AccountAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):
    ordering = ['account_name', 'currency']
    list_display = [
        'account_name',
        'balance',
        'currency',
        'balance_in_base_currency',
        'include_account_in_report'
        ]
    list_filter = ['account_name', 'include_account_in_report', 'user']
    search_fields = ['account_name', 'user']
    readonly_fields = [
        'balance',
        'balance_in_base_currency',
        'credit_card_limit_in_base_currency',
        'available_balance',
        'available_balance_in_base_currency',
        'user',
        'created_at',
        'updated_at'
        ]
    inlines = [CashflowInline, CashflowTargedInline]

    def save_model(self, request, obj, form, change):
        if obj.currency.title == config.BASE_CURRENCY:
            obj.balance_in_base_currency = obj.balance
        else:
            rate = Decimal(base_currency_rate()) / obj.currency.rate
            obj.balance_in_base_currency = Decimal(obj.balance) * rate

        if obj.credit_card_limit != Decimal('0.0'):
            obj.available_balance = (
                Decimal(obj.balance) + obj.credit_card_limit
                )
            if obj.currency.title == config.BASE_CURRENCY:
                obj.credit_card_limit_in_base_currency = obj.credit_card_limit
            else:
                rate = Decimal(base_currency_rate()) / obj.currency.rate
                obj.credit_card_limit_in_base_currency = (
                    Decimal(obj.credit_card_limit) * rate
                    )
                obj.available_balance_in_base_currency = (
                    Decimal(obj.available_balance) * rate
                    )
        else:
            obj.available_balance = 0
            obj.credit_card_limit_in_base_currency = 0
            obj.available_balance_in_base_currency = 0

        super().save_model(request, obj, form, change)

    actions = ['recalculate_balance_in_base_currency', 'create_report']

    def recalculate_balance_in_base_currency(self, request, queryset):
        for account in queryset:
            if account.currency.title == config.BASE_CURRENCY:
                account.balance_in_base_currency = account.balance
            else:
                rate = Decimal(base_currency_rate()) / account.currency.rate
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

        current_year_start = datetime.now().replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
            )
        income_year = queryset.annotate(
            total_income=Sum(
                'charged_cashflows__amount_in_base_currency',
                filter=Q(
                    charged_cashflows__payment_type='income',
                    charged_cashflows__date__gte=current_year_start
                    )
                )
        ).values('total_income').aggregate(
            Sum('total_income')
            )['total_income__sum'] or 0.0
        expenses_year = queryset.annotate(
            total_expenses=Sum(
                'charged_cashflows__amount_in_base_currency',
                filter=Q(
                    charged_cashflows__payment_type='expenses',
                    charged_cashflows__date__gte=current_year_start
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

        total_available_balance = queryset.filter(
            user=request.user
            ).aggregate(
            total_balance=Sum(
                Case(
                    When(credit_card_limit=0,
                         then='balance_in_base_currency'
                         ),
                    default=Value(0),
                    output_field=models.DecimalField(),
                )
            ) + Sum(
                'available_balance_in_base_currency')
            )['total_balance'] or 0.0

        messages.success(request, "Report created successfully.")

        report = Report.objects.filter(
            user=request.user,
            created_at__year=current_month_start.year,
            created_at__month=current_month_start.month
        ).last()

        if report:
            report.total_balance_in_base_currency = total_balance
            report.total_available_balance_in_base_currency = (
                total_available_balance
                )
            report.income_in_current_month = income
            report.expenses_in_current_month = expenses
            report.income_in_current_year = income_year
            report.expenses_in_current_year = expenses_year
            report.save()
        else:
            report = Report.objects.create(
                user=request.user,
                total_balance_in_base_currency=total_balance,
                total_available_balance_in_base_currency=(
                    total_available_balance
                    ),
                income_in_current_month=income,
                expenses_in_current_month=expenses,
                income_in_current_year=income_year,
                expenses_in_current_year=expenses_year
            )
            report.save()

    create_report.short_description = "Create report"


admin.site.register(Account, AccountAdmin)


class CurrencyAdmin(admin.ModelAdmin):
    ordering = ['title']
    list_display = ['title', 'symbol', 'rate_in_base', 'updated_at']
    search_fields = ['title']
    exclude = ('rate',)
    readonly_fields = ['rate_in_base', 'created_at', 'updated_at']


admin.site.register(Currency, CurrencyAdmin)
