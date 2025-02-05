from django.contrib import admin
from .models import Goal
from user.mixins import UserRestrictedAdminMixin
from account.models import Account


class GoalAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    ordering = ['title']
    filter_horizontal = ('accounts',)
    list_display = [
        'title',
        'sum',
        'currency',
        'sum_in_base',
        'remaining_sum_in_base',
        'calculation_method',
        'last_date',
        'amount_per_month'
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
        return super().formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(Goal, GoalAdmin)
