from django.contrib import admin
from logs.models import LogEntry, LogEntryCrypto


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'short_data']
    readonly_fields = ['created_at', 'data']
    list_filter = ['created_at']
    search_fields = ['data']

    def has_add_permission(self, request):
        return False

    def short_data(self, obj):
        data_str = str(obj.data)  # Преобразуем в строку
        return data_str[:300] + "..." if len(data_str) > 50 else data_str

    short_data.short_description = "Data"


@admin.register(LogEntryCrypto)
class LogEntryCryptoAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'short_data', 'type']
    readonly_fields = ['created_at', 'data', 'type']
    list_filter = ['created_at', 'type']
    search_fields = ['data']

    def has_add_permission(self, request):
        return False

    def short_data(self, obj):
        data_str = str(obj.data)  # Преобразуем в строку
        return data_str[:300] + "..." if len(data_str) > 50 else data_str

    short_data.short_description = "Data"
