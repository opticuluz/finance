from django.contrib import admin
from .models import Account, Currency


class AccountAdmin(admin.ModelAdmin):
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

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Account, AccountAdmin)


class CurrencyAdmin(admin.ModelAdmin):
    ordering = ['title']
    list_display = ['title', 'symbol', 'default_currency']
    search_fields = ['title']


admin.site.register(Currency, CurrencyAdmin)
