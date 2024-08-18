from django.db import models
from django.conf import settings
from account.models import Account, CurrencyHistory
from category.models import Category
from django.db.models import Avg
from django.db.models.functions import TruncDate
from datetime import datetime
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from account.currency_conversion import base_currency_rate
from constance import config


PAYMENT_TYPE_CHOICES = [
        ('expenses', 'Expenses'),
        ('income', 'Income'),
        ('transfer', 'Transfer'),
    ]


class Payment(models.Model):

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_TYPE_CHOICES,
        default='expenses'
        )
    charged_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='charged_payments'
        )
    targed_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='targed_payments'
        )
    amount = models.DecimalField(default=0.0, max_digits=20, decimal_places=2)
    amount_in_base_currency = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2
        )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True
        )
    date = models.DateField()
    note = models.CharField(max_length=255, blank=True, null=True)
    include_payment_in_report = models.BooleanField(default=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.payment_type).capitalize()

    def save(self, *args, **kwargs):
        self.full_clean()
        calculate_amount_in_base_currency(self)
        super().save(*args, **kwargs)


def calculate_amount_in_base_currency(instance, **kwargs):
    instance_datetime = datetime.combine(instance.date, datetime.min.time())
    transaction_date = timezone.make_aware(instance_datetime)
    currency_histories = CurrencyHistory.objects.annotate(
        date_only=TruncDate('date_and_time')
        ).filter(
            currency__title=instance.charged_account.currency.title,
            date_only=TruncDate(transaction_date)
        )
    if currency_histories.exists():
        average_rate = (currency_histories.aggregate(Avg('rate_in_base'))
                        ['rate_in_base__avg']).quantize(
                Decimal('0.00'),
                rounding=ROUND_HALF_UP
                )
    else:
        latest_currency_history = CurrencyHistory.objects.filter(
            currency__title=instance.charged_account.currency.title,
            date_and_time__lt=transaction_date
        ).order_by('-date_and_time').first()
        if latest_currency_history:
            average_rate = latest_currency_history.rate_in_base
        else:
            first_currency_history = CurrencyHistory.objects.filter(
                currency__title=instance.charged_account.currency.title
            ).order_by('date_and_time').first()
            average_rate = first_currency_history.rate_in_base

    rate = base_currency_rate()
    base_currency = config.BASE_CURRENCY
    if rate is not None:
        if instance.charged_account.currency.title == base_currency:
            instance.amount_in_base_currency = instance.amount
        else:
            amount_in_base_currency = Decimal(
                instance.amount
                /
                average_rate
                )
            rounded_amount = amount_in_base_currency.quantize(
                Decimal('0.00'),
                rounding=ROUND_HALF_UP
                )
            instance.amount_in_base_currency = rounded_amount
    else:
        return None  # Вернуть None вместо вывода предупреждения
        # messages.warning(
        #     # request,
        #     _("Rate not found for %(currency)s")
        #     %
        #     {'currency': base_currency}
        # )
