from django.contrib import admin
from .models import Tag
from user.mixins import UserRestrictedAdminMixin


class TagAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    ordering = ['tag_name']
    list_display = ['tag_name', 'active']
    list_filter = ['active', 'user']
    search_fields = ['tag_name']
    readonly_fields = ['user', 'created_at', 'updated_at']


admin.site.register(Tag, TagAdmin)
