from django.db import models
from django.conf import settings
from account.models import Account, Currency
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from constance import config
from account.currency_conversion import base_currency_rate


class GoalItem(models.Model):

    class Meta:
        verbose_name = 'Goal item'
        verbose_name_plural = 'Goal items'

    title = models.CharField(max_length=255)
    amount = models.DecimalField(
        default=0.0,
        max_digits=36,
        decimal_places=18
    )
    currency = models.ForeignKey(
        Currency,
        default=1,
        on_delete=models.PROTECT
    )
    amount_in_base = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_amount_in_base(self):
        try:
            if self.currency.title == config.BASE_CURRENCY:
                return Decimal(
                    self.amount
                    ).quantize(Decimal('0.00'),
                               rounding=ROUND_HALF_UP)
        except Exception:
            pass

        if getattr(self.currency, 'rate_in_base', None) is not None:
            try:
                rate = Decimal(self.currency.rate_in_base)
                if getattr(self.currency, 'cryptocurrency', None):
                    return (
                        Decimal(self.amount) * rate
                        ).quantize(Decimal('0.00'),
                                   rounding=ROUND_HALF_UP)
                return (
                    Decimal(self.amount) / rate
                    ).quantize(Decimal('0.00'),
                               rounding=ROUND_HALF_UP)
            except Exception:
                pass

        if getattr(self.currency, 'rate', None):
            try:
                rate_in_base = Decimal(
                    base_currency_rate()
                    ) / Decimal(self.currency.rate)
                if getattr(self.currency, 'cryptocurrency', None):
                    return (
                        Decimal(self.amount) * rate_in_base
                        ).quantize(Decimal('0.00'),
                                   rounding=ROUND_HALF_UP)
                return (
                    Decimal(self.amount) / rate_in_base
                    ).quantize(Decimal('0.00'),
                               rounding=ROUND_HALF_UP)
            except Exception:
                pass

        return Decimal('0.00')

    def save(self, *args, **kwargs):
        try:
            self.amount_in_base = self.calculate_amount_in_base()
        except Exception:
            pass
        super().save(*args, **kwargs)

    def formatted_amount(self):
        if self.currency.cryptocurrency is None:
            return f"{self.amount: .2f}"
        formatted_amount = f"{self.amount: .18f}".rstrip('0')
        if formatted_amount.endswith('.'):
            formatted_amount += '00'

        return formatted_amount

    def __str__(self):
        amount_str = self.formatted_amount()
        if self.currency.title == 'USD':
            return f'{self.title}: ${amount_str}'
        else:
            sign = self.currency.symbol or ''
            return f'{self.title}: {amount_str} {sign}'


class Goal(models.Model):

    class Meta:
        verbose_name = 'Goal'
        verbose_name_plural = 'Goals'

    title = models.CharField(max_length=255)
    items = models.ManyToManyField(GoalItem, blank=True)
    sum_in_base = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    remaining_sum_in_base = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    CALCULATION_METHODS = [
        ('amount', 'By amount'),
        ('date', 'By date')
    ]
    calculation_method = models.CharField(
        max_length=10,
        choices=CALCULATION_METHODS,
        default='amount',
    )
    accounts = models.ManyToManyField(Account, blank=True)
    last_date = models.DateField(blank=True, null=True)
    amount_per_month = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
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
        return self.title

    def calculate_goal_data(self):
        if not self.sum_in_base or self.sum_in_base == 0:
            self.remaining_sum_in_base = Decimal('0.00')
            self.last_date = None
            self.amount_per_month = Decimal('0.00')
            self.save()
            return

        total_balance = sum(
            account.balance_in_base_currency for account in self.accounts.all()
        ) if self.accounts.exists() else 0
        remaining_amount = self.sum_in_base - total_balance

        if self.calculation_method == 'amount':
            if self.amount_per_month > 0:
                months_to_goal = remaining_amount / self.amount_per_month
                calculated_date = (
                    date.today() + timedelta(
                        days=int(Decimal(months_to_goal) * 30)
                        )
                    )
                self.last_date = calculated_date
                self.remaining_sum_in_base = remaining_amount
                self.save()

        elif self.calculation_method == 'date':
            months_to_goal = (self.last_date - date.today()).days / 30
            if months_to_goal > 0:
                calculated_amount_per_month = (
                    remaining_amount / Decimal(months_to_goal)
                    )
                self.amount_per_month = calculated_amount_per_month.quantize(
                    Decimal('0.00'),
                    rounding=ROUND_HALF_UP
                )
                self.remaining_sum_in_base = remaining_amount
                self.save()
