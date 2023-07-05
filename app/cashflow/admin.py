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
    list_filter = [
        'created_at',
        'date',
        'payment_type',
        'charged_account',
        'user'
        ]
    search_fields = ['amount']
    readonly_fields = ['user', 'created_at', 'updated_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        return queryset
    
    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if not request.user.is_superuser:
            list_filter = [f for f in list_filter if f != 'user']
        return list_filter

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Cashflow, CashflowAdmin)
