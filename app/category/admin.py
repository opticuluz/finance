from django.contrib import admin
from .models import Category


class CategoryAdmin(admin.ModelAdmin):

    ordering = ['-created_at']
    list_display = ['created_at', 'category_name', 'active', 'user']
    list_filter = ['active', 'user']
    search_fields = ['category_name']
    readonly_fields = ['created_at', 'updated_at']


admin.site.register(Category, CategoryAdmin)
