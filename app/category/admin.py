from django.contrib import admin
from .models import Category


class CategoryAdmin(admin.ModelAdmin):

    ordering = ['-created_at']
    list_display = ['created_at', 'category_name', 'active']
    list_filter = ['active', 'user']
    search_fields = ['category_name']
    readonly_fields = ['user', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Category, CategoryAdmin)
