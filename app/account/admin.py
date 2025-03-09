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
from django.contrib.admin import SimpleListFilter


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
        'include_payment_in_report',
        'tags'
        ]
    exclude = ['amount', 'user']
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.order_by('-created_at')
        return queryset

    def get_amount(self, obj):
        if obj.charged_account.currency.cryptocurrency is None:
            return "{:.2f}".format(obj.amount)
        formatted_amount = "{:.18f}".format(obj.amount).rstrip('0')
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
        'include_payment_in_report',
        'tags'
        ]
    exclude = ['amount', 'user']
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.order_by('-created_at')
        return queryset

    def get_amount(self, obj):
        if obj.charged_account.currency.cryptocurrency is None:
            return "{:.2f}".format(obj.amount)
        formatted_amount = "{:.18f}".format(obj.amount).rstrip('0')
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


class CurrencyTypeFilter(SimpleListFilter):
    title = 'Currency Type'
    parameter_name = 'currency_type'

    def lookups(self, request, model_admin):
        return [
            ('crypto', 'Crypto'),
            ('fiat', 'Fiat')
        ]

    def queryset(self, request, queryset):
        if hasattr(queryset.model, 'cryptocurrency'):
            if self.value() == 'crypto':
                return queryset.filter(cryptocurrency__isnull=False)
            elif self.value() == 'fiat':
                return queryset.filter(cryptocurrency__isnull=True)
        elif hasattr(queryset.model, 'currency'):
            if self.value() == 'crypto':
                return queryset.filter(currency__cryptocurrency__isnull=False)
            elif self.value() == 'fiat':
                return queryset.filter(currency__cryptocurrency__isnull=True)
        return queryset


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
        CurrencyTypeFilter,
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
            return "{:.2f}".format(obj.balance)
        formatted_balance = "{:.18f}".format(obj.balance).rstrip('0')
        if formatted_balance.endswith('.'):
            formatted_balance += '00'
        return formatted_balance

    get_balance.short_description = 'Balance'

    def save_model(self, request, obj, form, change):
        calculate_balance_in_base_currency(instance=obj)
        super().save_model(request, obj, form, change)
        create_report_on_payment_item_save(
            sender=Account,
            instance=obj,
            from_admin=True
            )

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        create_report_on_payment_item_save(
            sender=Account,
            instance=obj,
            from_admin=True
            )


@receiver([post_save, post_delete], sender=Account)
def create_report_on_payment_item_save(sender, instance, **kwargs):
    if kwargs.get('from_admin', False):
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
    list_filter = [CurrencyTypeFilter]


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
        CurrencyTypeFilter,
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
