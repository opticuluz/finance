from django.contrib import admin
from .models import Category
from core.mixins import UserRestrictedAdminMixin


class CategoryAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    ordering = ['-created_at']
    list_display = ['created_at', 'category_name', 'active']
    list_filter = ['active', 'user']
    search_fields = ['category_name']
    readonly_fields = ['user', 'created_at', 'updated_at']


admin.site.register(Category, CategoryAdmin)
