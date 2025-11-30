from django.contrib import admin
from .models import Goal, GoalItem
from user.mixins import UserRestrictedAdminMixin
from account.models import Account
import decimal
from django import forms


class GoalAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    ordering = ['title']
    filter_horizontal = ('accounts', 'items')
    list_display = [
        'title',
        'sum_in_base',
        'remaining_sum_in_base',
        'calculation_method',
        'last_date',
        'amount_per_month',
        'updated_at'
        ]
    list_filter = ['user']
    search_fields = ['title']
    readonly_fields = [
        'sum_in_base',
        'remaining_sum_in_base',
        'user',
        'created_at',
        'updated_at'
        ]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "accounts":
            kwargs["queryset"] = Account.objects.filter(user=request.user)
        if db_field.name == "items":
            kwargs["queryset"] = GoalItem.objects.filter(user=request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not getattr(obj, 'user', None):
            obj.user = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Goal, GoalAdmin)


class GoalItemAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    ordering = ['title']
    list_display = [
        'title',
        'get_amount',
        'currency',
        'amount_in_base',
        'created_at'
    ]
    list_filter = ['user', 'currency']
    search_fields = ['title']
    readonly_fields = [
        'amount_in_base',
        'user',
        'created_at',
        'updated_at'
    ]

    def save_model(self, request, obj, form, change):
        if not getattr(obj, 'user', None):
            obj.user = request.user
        super().save_model(request, obj, form, change)

    class DecimalWithoutTrailingZeroesWidget(forms.TextInput):
        def format_value(self, value):
            if value is None:
                return ''
            if isinstance(value, float) or isinstance(value, decimal.Decimal):
                value = "{:.18f}".format(value).rstrip('0')
                if value.endswith('.'):
                    value += '00'
            return super().format_value(value)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        form.base_fields[
            'amount'
            ].widget = self.DecimalWithoutTrailingZeroesWidget()
        return form

    def get_amount(self, obj):
        if obj.currency and getattr(
            obj.currency, 'cryptocurrency', None
        ) is None:
            return "{:.2f}".format(obj.amount)
        formatted = "{:.18f}".format(obj.amount).rstrip('0')
        if formatted.endswith('.'):
            formatted += '00'
        return formatted

    get_amount.short_description = 'Amount'


admin.site.register(GoalItem, GoalItemAdmin)
