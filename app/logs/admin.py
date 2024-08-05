from django.contrib import admin
from .models import LogEntry


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'data']
    readonly_fields = ['created_at', 'data']
    list_filter = ['created_at']
    search_fields = ['data']

    def has_add_permission(self, request):
        return False
