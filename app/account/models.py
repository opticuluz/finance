from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from crypto.models import CryptoCurrency


class Currency(models.Model):

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    title = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=10)
    cryptocurrency = models.ForeignKey(
        CryptoCurrency,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
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

    def clean(self):
        if self.cryptocurrency:
            existing_currency = Currency.objects.filter(
                cryptocurrency=self.cryptocurrency
            ).exclude(id=self.id)

            if existing_currency.exists():
                raise ValidationError(
                    "Эта криптовалюта уже привязана к другой валюте!"
                    )

    def __str__(self):
        return self.title


class CurrencyHistory(models.Model):

    class Meta:
        verbose_name = 'Currency history'
        verbose_name_plural = 'Currency history'

    date_and_time = models.DateTimeField()
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    rate_in_base = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    base_currency = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.currency.title}: {self.rate_in_base}'


class Account(models.Model):
    account_name = models.CharField(max_length=100, unique=False)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    balance = models.DecimalField(
        default=0.0,
        max_digits=36,
        decimal_places=18
        )
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

    def formatted_balance(self):
        if self.currency.cryptocurrency is None:
            return f"{self.balance: .2f}"
        formatted_balance = f"{self.balance: .18f}".rstrip('0')
        if formatted_balance.endswith('.'):
            formatted_balance += '00'

        return formatted_balance

    def __str__(self):
        balance_str = self.formatted_balance()
        if self.currency.title == 'USD':
            return f'{self.account_name}: ${balance_str}'
        else:
            sign = self.currency.symbol or ''
            return f'{self.account_name}: {balance_str} {sign}'
