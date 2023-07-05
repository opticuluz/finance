from django.contrib import admin, messages
from .models import Cashflow
from core.mixins import UserRestrictedAdminMixin
from django.utils import timezone


class CashflowAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    class Media:
        js = ['js/cashflow_admin.js']

    ordering = ['-created_at']
    list_display = [
        'created_at',
        'payment_type',
        'charged_account',
        'targed_account',
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        form.base_fields['charged_account'].queryset = form.base_fields['charged_account'].queryset.filter(user=request.user)
        form.base_fields['targed_account'].queryset = form.base_fields['targed_account'].queryset.filter(user=request.user)
        form.base_fields['category'].queryset = form.base_fields['category'].queryset.filter(user=request.user)
        return form

    def save_model(self, request, obj, form, change):
        if obj.payment_type == 'transfer' and not obj.targed_account:
            messages.error(request, 'Target account must be specified for transfers.')
        elif obj.payment_type == 'transfer' and (obj.charged_account == obj.targed_account):
            messages.error(request, 'Charged account and target account cannot be the same.')
        elif obj.payment_type != 'transfer' and obj.targed_account:
            messages.error(request, 'Target account must be empty for expenses and income.')
        elif obj.date > timezone.now().date():
            messages.error(request, 'Date cannot be in the future.')
        else:
            obj.user = request.user
            super().save_model(request, obj, form, change)


admin.site.register(Cashflow, CashflowAdmin)
