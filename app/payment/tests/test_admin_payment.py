from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from account.models import Account, Currency, CurrencyHistory
from payment.models import Payment
from decimal import Decimal


class PaymentAdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='testpass123',
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='testpass123',
            name='Test User'
        )
        self.currency_gel = Currency.objects.create(title='GEL', symbol='₾')
        self.currency_history_gel = CurrencyHistory.objects.create(
            date_and_time='2023-08-16 10:59:04+00:00',
            currency=self.currency_gel,
            rate_in_base=Decimal('2.69')
            )
        self.account_A = Account.objects.create(
            account_name='A',
            currency=self.currency_gel,
            user=self.user
            )
        self.payment = Payment.objects.create(
            payment_type='income',
            charged_account=self.account_A,
            amount='3000.85',
            date='2023-12-22',
            user=self.user
        )

    def test_payments_list(self):
        url = reverse('admin:payment_payment_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.payment.payment_type)
        self.assertContains(res, self.payment.charged_account)
        self.assertContains(res, self.payment.amount)

    def test_edit_payment_page(self):
        url = reverse('admin:payment_payment_change', args=[self.payment.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_payment_page(self):
        url = reverse('admin:payment_payment_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
