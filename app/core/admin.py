from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from core import models


class UserAdmin(BaseUserAdmin):

    ordering = ['-registration_date']
    list_display = ['registration_date', 'email', 'is_active']
    fieldsets = (
        (None, {'fields': ('email', 'password', 'name')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                )
            }
        ),
        (_('Important dates'), {'fields': (
            'registration_date',
            'last_login',
            )}),
    )
    readonly_fields = ['registration_date', 'last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'name',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(id=request.user.id)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            # Make permissions field read-only for non-superusers
            return list(self.readonly_fields) + [
                'email',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups'
                ]
        return self.readonly_fields


admin.site.register(models.User, UserAdmin)
