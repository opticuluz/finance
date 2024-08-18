from django.db import models


class LogEntry(models.Model):
    class Meta:
        verbose_name = 'Log entry'
        verbose_name_plural = 'Log entries'

    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()

    def __str__(self):
        return str(self.created_at)
