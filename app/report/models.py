from django.db import models, transaction, IntegrityError
from django.conf import settings
from constance import config
from category.models import Category
from django.utils import timezone


class Report(models.Model):

    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

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
    total_available_balance_in_base_currency = models.DecimalField(
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

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        year = self.created_at.year
        month = self.created_at.month

        try:
            with transaction.atomic():
                if Report.objects.select_for_update().filter(
                        user=self.user,
                        created_at__year=year,
                        created_at__month=month
                        ).exclude(id=self.id).exists():
                    raise IntegrityError('Duplicate entry detected.')
        except IntegrityError:
            # Логирование или просто игнорирование
            pass

        super().save(*args, **kwargs)


class Report_for_category(models.Model):

    class Meta:
        verbose_name = 'Report for category'
        verbose_name_plural = 'Reports for categories'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
        )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.CASCADE
        )
    changes_in_category_for_current_month = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    average_for_year = models.DecimalField(
        default=0.0,
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Report for category "{self.category}" for {self.user.email} \
in {config.BASE_CURRENCY}'

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        year = self.created_at.year
        month = self.created_at.month

        try:
            with transaction.atomic():
                if Report_for_category.objects.select_for_update().filter(
                        user=self.user,
                        category=self.category,
                        created_at__year=year,
                        created_at__month=month
                        ).exclude(id=self.id).exists():
                    raise IntegrityError('Duplicate entry detected.')
        except IntegrityError:
            # Логирование или просто игнорирование
            pass

        super().save(*args, **kwargs)
