from django.contrib import admin
from crypto.models import CryptoCurrency


class CryptoCurrencyAdmin(admin.ModelAdmin):
    ordering = ['-is_active', 'cmc_rank']
    list_display = [
        'title',
        'symbol',
        'is_active',
        'updated_at'
        ]
    search_fields = ['title', 'symbol']
    readonly_fields = [
        'cmc_id',
        'cmc_rank',
        'title',
        'symbol',
        'created_at',
        'updated_at'
        ]
    list_filter = ['is_active']


admin.site.register(CryptoCurrency, CryptoCurrencyAdmin)
