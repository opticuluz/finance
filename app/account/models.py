from django.db import models
from django.conf import settings


class Currency(models.Model):

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    title = models.CharField(max_length=3, unique=True)
    symbol = models.CharField(max_length=1)
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        blank=True,
        null=True
        )
    rate_in_base = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Account(models.Model):
    account_name = models.CharField(max_length=100, unique=False)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    balance = models.DecimalField(default=0.0, max_digits=20, decimal_places=2)
    balance_in_base_currency = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    credit_card_limit = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    credit_card_limit_in_base_currency = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    available_balance = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    available_balance_in_base_currency = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    note = models.CharField(max_length=255, blank=True, null=True)
    include_account_in_report = models.BooleanField(default=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    my_order = models.IntegerField(
        default=0,
        blank=False,
        null=False,
        db_index=True
    )

    def __str__(self):
        if self.currency.title == 'USD':
            return f'{self.account_name}: ${self.balance}'
        else:
            sign = self.currency.symbol
            return f'{self.account_name}: {self.balance} {sign}'
