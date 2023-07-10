from django.db import models
from django.conf import settings
from constance import config


class Report(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
        )
    total_balance_in_base_currency = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    income_in_current_month = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    expenses_in_current_month = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    income_in_current_year = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    expenses_in_current_year = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report for {self.user.email} in {config.BASE_CURRENCY}"
