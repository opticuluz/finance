from django.contrib import admin
from .models import Account, Currency
from core.mixins import UserRestrictedAdminMixin
from cashflow.models import Cashflow


class CashflowInline(admin.TabularInline):
    model = Cashflow
    fk_name = 'charged_account'
    fk_name = 'targed_account'
    readonly_fields = ['created_at', 'payment_type', 'charged_account', 'targed_account', 'amount', 'category', 'date', 'note']
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
        'include_balance_in_current_month'
        ]
    list_filter = ['account_name', 'include_balance_in_current_month', 'user']
    search_fields = ['account_name', 'user']
    readonly_fields = ['user', 'created_at', 'updated_at']
    inlines = [CashflowInline]


admin.site.register(Account, AccountAdmin)


class CurrencyAdmin(admin.ModelAdmin):
    ordering = ['title']
    list_display = ['title', 'symbol', 'default_currency']
    search_fields = ['title']


admin.site.register(Currency, CurrencyAdmin)
