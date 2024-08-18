from django.contrib import admin
from .models import Category
from user.mixins import UserRestrictedAdminMixin


class CategoryAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    ordering = ['category_name']
    list_display = ['category_name', 'active']
    list_filter = ['active', 'user']
    search_fields = ['category_name']
    readonly_fields = ['user', 'created_at', 'updated_at']


admin.site.register(Category, CategoryAdmin)
