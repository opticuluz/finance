from django.contrib import admin, messages
from .models import Account, Currency
from user.mixins import UserRestrictedAdminMixin
from payment.models import Payment
from decimal import Decimal
from constance import config
from django.utils.translation import gettext_lazy as _


class PaymentInline(admin.TabularInline):
    model = Payment
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


class PaymentTargedInline(admin.TabularInline):
    model = Payment
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
    inlines = [PaymentInline, PaymentTargedInline]

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


admin.site.register(Account, AccountAdmin)


class CurrencyAdmin(admin.ModelAdmin):
    ordering = ['title']
    list_display = ['title', 'symbol', 'rate_in_base', 'updated_at']
    search_fields = ['title']
    exclude = ('rate',)
    readonly_fields = ['rate_in_base', 'created_at', 'updated_at']


admin.site.register(Currency, CurrencyAdmin)
