from django.db import models
from django.conf import settings
from account.models import Account
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP


class Goal(models.Model):

    class Meta:
        verbose_name = 'Goal'
        verbose_name_plural = 'Goals'

    title = models.CharField(max_length=255)
    goal = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2
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

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.full_clean()
        self.calculate_goal_data()
        super().save(*args, **kwargs)

    def calculate_goal_data(self):
        total_balance = sum(
            account.balance_in_base_currency for account in self.accounts.all()
        ) if self.accounts.exists() else 0
        remaining_amount = self.goal - total_balance

        if self.calculation_method == 'amount':
            if self.amount_per_month > 0:
                months_to_goal = remaining_amount / self.amount_per_month
                calculated_date = (
                    date.today() + timedelta(
                        days=int(Decimal(months_to_goal) * 30)
                        )
                    )
                self.last_date = calculated_date

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
