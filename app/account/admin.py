from django.contrib import admin, messages
from .models import Account, Currency
from core.mixins import UserRestrictedAdminMixin
from cashflow.models import Cashflow
from django.conf import settings
# from djmoney.contrib.exchange import get_rate
# from djmoney.contrib.exchange.models import get_rate
# from djmoney.contrib.exchange.backends import FixerBackend
from djmoney.contrib.exchange.models import get_rate, Rate
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal


class CashflowInline(admin.TabularInline):
    model = Cashflow
    fk_name = 'charged_account'
    readonly_fields = [
        'created_at',
        'payment_type',
        'charged_account',
        'targed_account',
        'amount',
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
    readonly_fields = ['balance', 'balance_in_base_currency', 'user', 'created_at', 'updated_at']
    inlines = [CashflowInline]
        

    def save_model(self, request, obj, form, change):
        if obj.currency.title == settings.BASE_CURRENCY:
            obj.balance_in_base_currency = obj.balance
        else:
            # rate = get_rate(obj.currency.currency, settings.BASE_CURRENCY)
            # obj.balance_in_base_currency = Decimal(obj.balance) * rate
            obj.balance_in_base_currency = Decimal(obj.balance) * get_rate(obj.currency.title, settings.BASE_CURRENCY)
        super().save_model(request, obj, form, change)


    # actions = ['recalculate_balance_in_base_currency']
    
    # def recalculate_balance_in_base_currency(self, request, queryset):
    #     for account in queryset:
    #         if account.currency.title == settings.BASE_CURRENCY:
    #             account.balance_in_base_currency = account.balance
    #         else:
    #             rate = Rate.objects.filter(
    #                 currency=account.currency.title,
    #                 to_currency=settings.BASE_CURRENCY
    #             ).order_by('-last_updated').first()
    #             if rate:
    #                 account.balance_in_base_currency = account.balance * Decimal(rate.rate)
    #             else:
    #                 messages.warning(request, f"Rate not found for {account.currency.title}")
    #                 continue
    #         account.save()
    #     messages.success(request, "Balance in base currency recalculated for selected accounts.")
    
    # recalculate_balance_in_base_currency.short_description = "Recalculate balance in base currency"


    actions = ['recalculate_balance_in_base_currency']
    
    def recalculate_balance_in_base_currency(self, request, queryset):
        for account in queryset:
            if account.currency.title == settings.BASE_CURRENCY:
                account.balance_in_base_currency = account.balance
            else:
                rate = get_rate(account.currency.title, settings.BASE_CURRENCY)
                if rate:
                    account.balance_in_base_currency = account.balance * rate
                else:
                    messages.warning(request, f"Rate not found for {account.currency.title}")
                    continue
            account.save()
        messages.success(request, "Balance in base currency recalculated for selected accounts.")
    
    recalculate_balance_in_base_currency.short_description = "Recalculate balance in base currency"

    # @receiver(post_save, sender=Account)
    # def recalculate_balance_in_base_currency(sender, instance, **kwargs):
    #     if kwargs['created'] or 'currency' in instance.changed_fields:
    #         instance.save()

    # @receiver(post_save, sender=Rate)
    # def recalculate_account_balance_in_base_currency(sender, instance, **kwargs):
    #     accounts = Account.objects.filter(currency__currency=instance.source_currency)
    #     for account in accounts:
    #         if account.currency.currency != settings.BASE_CURRENCY:
    #             account.save()

    # @receiver(post_save, sender=Rate)
    # def recalculate_account_balance_in_base_currency(sender, instance, **kwargs):
    #     accounts = Account.objects.filter(currency__title=instance.source_currency)
    #     for account in accounts:
    #         if account.currency.title != settings.BASE_CURRENCY:
    #             last_update = instance.last_update
    #             rate = get_rate(account.currency.title, settings.BASE_CURRENCY, last_update)
    #             account.balance_in_base_currency = account.balance * rate
    #             account.save()


admin.site.register(Account, AccountAdmin)





class CurrencyAdmin(admin.ModelAdmin):
    ordering = ['title']
    list_display = ['title', 'symbol']
    search_fields = ['title']


admin.site.register(Currency, CurrencyAdmin)
