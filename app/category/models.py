from django.db import models
from django.conf import settings


class Category(models.Model):

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    category_name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category_name
