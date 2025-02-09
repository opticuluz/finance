from django.contrib import admin  # , messages
# from django.utils.translation import gettext_lazy as _
from .models import Account, Currency, CurrencyHistory, CryptoCurrency
from user.mixins import UserRestrictedAdminMixin
from payment.models import Payment
from report.tasks import create_report
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from adminsortable2.admin import SortableAdminMixin
from payment.admin import calculate_balance_in_base_currency
from rangefilter.filters import DateTimeRangeFilterBuilder
from django import forms


class PaymentInline(admin.TabularInline):
    model = Payment
    fk_name = 'charged_account'
    readonly_fields = [
        'created_at',
        'payment_type',
        'charged_account',
        'targed_account',
        'get_amount',
        'amount_in_base_currency',
        'category',
        'date',
        'note',
        'include_payment_in_report'
        ]
    exclude = ['amount']
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

    def get_amount(self, obj):
        if obj.charged_account.currency.cryptocurrency is None:
            return f"{obj.amount: .2f}"
        formatted_amount = f"{obj.amount: .18f}".rstrip('0')
        if formatted_amount.endswith('.'):
            formatted_amount += '00'
        return formatted_amount

    get_amount.short_description = 'Amount'


class PaymentTargedInline(admin.TabularInline):
    model = Payment
    fk_name = 'targed_account'
    readonly_fields = [
        'created_at',
        'payment_type',
        'charged_account',
        'targed_account',
        'get_amount',
        'amount_in_base_currency',
        'category',
        'date',
        'note',
        'include_payment_in_report'
        ]
    exclude = ['amount']
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

    def get_amount(self, obj):
        if obj.charged_account.currency.cryptocurrency is None:
            return f"{obj.amount: .2f}"
        formatted_amount = f"{obj.amount: .18f}".rstrip('0')
        if formatted_amount.endswith('.'):
            formatted_amount += '00'
        return formatted_amount

    get_amount.short_description = 'Amount'


# def base_currency_rate():
#     base_currency = config.BASE_CURRENCY
#     try:
#         base_currency_obj = Currency.objects.get(title=base_currency)
#         if base_currency_obj.rate:
#             return base_currency_obj.rate
#         else:
#             return None  # Вернуть None вместо вывода предупреждения
#             # messages.warning(
#             #     # request,
#             #     _("Rate not found for %(currency)s")
#             #     %
#             #     {'currency': base_currency}
#             # )
#     except Currency.DoesNotExist:
#         return None  # Вернуть None вместо вывода предупреждения
#         # messages.warning(
#         #     # request,
#         #     _("Base currency %(currency)s not found")
#         #     %
#         #     {'currency': base_currency}
#         # )

#     return None


class AccountAdmin(
        SortableAdminMixin,
        UserRestrictedAdminMixin,
        admin.ModelAdmin
        ):
    ordering = ['my_order']
    list_display = [
        'account_name',
        'get_balance',
        'currency',
        'balance_in_base_currency',
        'include_account_in_report',
        'my_order'
        ]
    list_filter = [
        'account_name',
        'currency',
        'include_account_in_report',
        'user'
        ]
    search_fields = ['account_name', 'user']
    readonly_fields = [
        'get_balance',
        'balance_in_base_currency',
        'credit_card_limit_in_base_currency',
        'available_balance',
        'available_balance_in_base_currency',
        'user',
        'created_at',
        'updated_at'
        ]
    exclude = ['balance']
    inlines = [PaymentInline, PaymentTargedInline]

    def get_balance(self, obj):
        if obj.currency.cryptocurrency is None:
            return f"{obj.balance: .2f}"
        formatted_balance = f"{obj.balance: .18f}".rstrip('0')
        if formatted_balance.endswith('.'):
            formatted_balance += '00'
        return formatted_balance

    get_balance.short_description = 'Balance'

    def save_model(self, request, obj, form, change):

        calculate_balance_in_base_currency(instance=obj)

        # if obj.currency.title == config.BASE_CURRENCY:
        #     obj.balance_in_base_currency = obj.balance
        # else:
        #     rate = obj.currency.rate
        #     if rate is None:
        #         obj.balance_in_base_currency = Decimal('0.0')
        #     else:
        #         rate = Decimal(base_currency_rate()) / rate
        #         obj.balance_in_base_currency = Decimal(obj.balance) * rate

        # if obj.credit_card_limit != Decimal('0.0'):
        #     obj.available_balance = (
        #         Decimal(obj.balance) + obj.credit_card_limit
        #         )
        #     if obj.currency.title == config.BASE_CURRENCY:
        #         obj.credit_card_limit_in_base_currency = (
        #             obj.credit_card_limit
        #             )
        #         obj.available_balance_in_base_currency = (
        #             obj.available_balance
        #             )
        #     else:
        #         rate = obj.currency.rate
        #         if rate is None:
        #             obj.credit_card_limit_in_base_currency = Decimal('0.0')
        #             obj.available_balance_in_base_currency = Decimal('0.0')
        #         else:
        #             rate = Decimal(base_currency_rate()) / rate
        #             obj.credit_card_limit_in_base_currency = (
        #                 Decimal(obj.credit_card_limit) * rate
        #                 )
        #             obj.available_balance_in_base_currency = (
        #                 Decimal(obj.available_balance) * rate
        #                 )
        # else:
        #     obj.available_balance = 0
        #     obj.credit_card_limit_in_base_currency = 0
        #     obj.available_balance_in_base_currency = 0

        super().save_model(request, obj, form, change)


@receiver([post_save, post_delete], sender=Account)
def create_report_on_payment_item_save(sender, instance, **kwargs):
    user = instance.user
    create_report.delay(user.id)


admin.site.register(Account, AccountAdmin)


class CurrencyAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'cryptocurrency' in self.fields:
            self.fields['cryptocurrency'].queryset = (
                CryptoCurrency.objects.filter(
                    is_active=True
                    ).order_by('cmc_rank')
            )

    class Meta:
        model = Currency
        fields = '__all__'


class CurrencyAdmin(admin.ModelAdmin):
    form = CurrencyAdminForm
    ordering = ['title']
    list_display = [
        'title',
        'symbol',
        'rate_in_base',
        'updated_at'
        ]
    search_fields = ['title']
    exclude = ('rate',)
    readonly_fields = [
        'rate_in_base',
        'created_at',
        'updated_at'
        ]


admin.site.register(Currency, CurrencyAdmin)


class CurrencyHistoryAdmin(admin.ModelAdmin):
    ordering = ['-date_and_time', 'currency__title']
    list_display = [
        'date_and_time',
        'currency',
        'rate_in_base',
        'base_currency',
        'updated_at'
        ]
    list_filter = [
        ('date_and_time', DateTimeRangeFilterBuilder()),
        'currency'
        ]
    search_fields = ['date_and_time']
    readonly_fields = [
        'date_and_time',
        'currency',
        'rate_in_base',
        'base_currency',
        'created_at',
        'updated_at'
        ]


admin.site.register(CurrencyHistory, CurrencyHistoryAdmin)
