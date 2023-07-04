from django.contrib import admin
from .models import Category


class CategoryAdmin(admin.ModelAdmin):
    ordering = ['category_name']
    list_display = ['category_name', 'active']
    list_filter = ['active']
    search_fields = ['category_name']


admin.site.register(Category, CategoryAdmin)
