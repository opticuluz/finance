from django.contrib import admin
from .models import Category


class CategoryAdmin(admin.ModelAdmin):

    ordering = ['-created_at']
    list_display = ['created_at', 'category_name', 'active']
    list_filter = ['active', 'user']
    search_fields = ['category_name']
    readonly_fields = ['user', 'created_at', 'updated_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        return queryset
    
    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if not request.user.is_superuser:
            list_filter = [f for f in list_filter if f != 'user']
        return list_filter

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Category, CategoryAdmin)
