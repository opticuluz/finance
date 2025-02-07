from django.db import models


class CryptoCurrency(models.Model):

    class Meta:
        verbose_name = 'Cryptocurrency'
        verbose_name_plural = 'Cryptocurrencies'

    cmc_id = models.IntegerField(unique=True)
    cmc_rank = models.IntegerField()
    title = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    is_active = models.BooleanField(default=False)
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
