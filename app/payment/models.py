import os
import hashlib
from django.db import models
from django.conf import settings
from account.models import Account, CurrencyHistory
from category.models import Category
from tag.models import Tag
from django.db.models import Avg
from django.db.models.functions import TruncDate
from datetime import datetime
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from account.currency_conversion import base_currency_rate
from constance import config
from finance.storage import ReceiptStorage
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .tasks import compress_receipt


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
    amount = models.DecimalField(default=0.0, max_digits=36, decimal_places=18)
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
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="payments"
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
            Payment.objects.filter(id=instance.id).update(
                amount_in_base_currency=instance.amount
                )
        else:
            if instance.charged_account.currency.cryptocurrency:
                amount_in_base_currency = Decimal(
                    instance.amount
                    *
                    average_rate
                    )
                rounded_amount = amount_in_base_currency.quantize(
                    Decimal('0.00'),
                    rounding=ROUND_HALF_UP
                    )
                instance.amount_in_base_currency = rounded_amount
                Payment.objects.filter(id=instance.id).update(
                    amount_in_base_currency=rounded_amount
                    )
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
                Payment.objects.filter(id=instance.id).update(
                    amount_in_base_currency=rounded_amount
                    )
    else:
        return None  # Вернуть None вместо вывода предупреждения
        # messages.warning(
        #     # request,
        #     _("Rate not found for %(currency)s")
        #     %
        #     {'currency': base_currency}
        # )


def get_user_folder(user_id: int) -> str:
    """
    Генерируем уникальный, но безопасный префикс для пользователя
    на основе его id, используя SHA256 и берем первые 8 символов.
    """
    hash_obj = hashlib.sha256(str(user_id).encode())
    return hash_obj.hexdigest()[:8]  # например: 'a1b2c3d4'


def receipt_upload_to(instance, filename):
    """
    Формирует путь с папкой по пользователю + подпапкой по Payment.id:
    receipts/<user_hash>/<payment_id>/filename.jpg
    """
    user_id = instance.payment.user.id
    user_folder = get_user_folder(user_id)

    payment_folder = str(instance.payment.id)

    return os.path.join(user_folder, payment_folder, filename)


class PaymentReceipt(models.Model):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="receipts"
    )
    image = models.ImageField(
        storage=ReceiptStorage(),
        upload_to=receipt_upload_to
        )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt for Payment {self.payment.id}"


@receiver(post_save, sender=PaymentReceipt)
def compress_payment_receipt(sender, instance, created, **kwargs):
    if created and instance.image:
        compress_receipt.delay(instance.image.name)


@receiver(post_delete, sender=PaymentReceipt)
def delete_receipt_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
