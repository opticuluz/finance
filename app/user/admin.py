from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from user import models


class UserAdmin(BaseUserAdmin):

    ordering = ['-registration_date']
    list_display = ['registration_date', 'email', 'is_active']
    fieldsets = (
        (None, {'fields': ('email', 'password', 'name', 'timezone')}),
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
        (
            _('Account Security'),
            {
                'fields': ('two_factor_link',),
            }
        ),
        (
            _('Important dates'),
            {
                'fields': ('registration_date', 'last_login',)
            }
        ),
    )
    readonly_fields = ['registration_date', 'last_login', 'two_factor_link']
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

    def two_factor_link(self, obj):
        return format_html(
            '<a href="{url}" target="_blank">{text}</a>',
            url="/account/two_factor/",
            text="Set up Two-Factor Authentication"
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(id=request.user.id)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return list(self.readonly_fields) + [
                'email',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups'
                ]
        return self.readonly_fields


admin.site.register(models.User, UserAdmin)
