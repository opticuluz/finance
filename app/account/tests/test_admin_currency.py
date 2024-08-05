from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from account.models import Currency


class CurrencyAdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='testpass123',
        )
        self.client.force_login(self.admin_user)
        self.currency_usd = Currency.objects.create(
            title='USD',
            symbol='$',
            rate='1.081427',
            rate_in_base='1.00',
            created_at='2023-07-11 16:46:13.300617+00',
            updated_at='2024-06-08 15:49:42.866557+00'
            )

    def test_currency_list(self):
        url = reverse('admin:account_currency_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.currency_usd.title)
        self.assertContains(res, self.currency_usd.symbol)
        self.assertContains(res, self.currency_usd.rate_in_base)

    def test_edit_currency_page(self):
        url = reverse(
            'admin:account_currency_change', args=[self.currency_usd.id]
            )
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_currency_page(self):
        url = reverse('admin:account_currency_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
