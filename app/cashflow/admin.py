from django.contrib import admin
from .models import Cashflow


class CashflowAdmin(admin.ModelAdmin):

    ordering = ['-created_at']
    list_display = [
        'created_at',
        'payment_type',
        'charged_account',
        'amount',
        'category',
        'date'
        ]
    list_filter = ['created_at', 'date', 'payment_type', 'charged_account', 'user']
    search_fields = ['amount']
    readonly_fields = ['created_at', 'updated_at']


admin.site.register(Cashflow, CashflowAdmin)
