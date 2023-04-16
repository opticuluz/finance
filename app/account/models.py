from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Currency(models.Model):

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    title = models.CharField(max_length=3, unique=True)
    symbol = models.CharField(max_length=1, unique=True)
    default_currency = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def clean(self):
        if self.default_currency:
            if Currency.objects.filter(default_currency=True).exclude(pk=self.pk).exists():
                raise ValidationError('Only one currency can be default')
        super().clean()


class Account(models.Model):
    account_name = models.CharField(max_length=100, unique = True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    starting_balance = models.DecimalField(default=0.0, max_digits=20, decimal_places=2)
    balance = models.DecimalField(default=0.0, max_digits=20, decimal_places=2)
    note = models.CharField(max_length=255, blank=True, null=True)
    include_balance_in_current_month = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.account_name
