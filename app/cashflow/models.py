from django.db import models
from django.conf import settings
from account.models import Account
from category.models import Category
from django.core.exceptions import ValidationError


PAYMENT_TYPE_CHOICES = [
        ('expenses', 'Expenses'),
        ('income', 'Income'),
        ('transfer', 'Transfer'),
    ]


class Cashflow(models.Model):

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
        related_name='charged_cashflows'
        )
    targed_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='targed_cashflows'
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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.payment_type)

    def clean(self):
        if self.charged_account == self.targed_account:
            raise ValidationError(
                "Charged and targed accounts cannot be the same"
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
