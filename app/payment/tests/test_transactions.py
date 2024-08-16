from django.test import TestCase
from account.models import Account, Currency, CurrencyHistory
from payment.models import Payment
from django.contrib.auth import get_user_model
from decimal import Decimal


class PaymentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='user_1@example.com',
            password='testpass123',
            name='Test User_1'
        )
        self.currency_usd = Currency.objects.create(title='USD', symbol='$')
        self.currency_history_usd = CurrencyHistory.objects.create(
            date_and_time='2023-12-22 10:59:04+00:00',
            currency=self.currency_usd,
            rate_in_base=Decimal('1')
            )
        self.currency_gel = Currency.objects.create(title='GEL', symbol='₾')
        self.currency_history_gel = CurrencyHistory.objects.create(
            date_and_time='2023-08-16 10:59:04+00:00',
            currency=self.currency_gel,
            rate_in_base=Decimal('2.69')
            )
        self.account_A = Account.objects.create(
            account_name='A',
            currency=self.currency_usd,
            user=self.user
            )
        self.account_B = Account.objects.create(
            account_name='B',
            currency=self.currency_usd,
            user=self.user
            )
        self.account_C = Account.objects.create(
            account_name='C',
            currency=self.currency_gel,
            user=self.user
            )

    def test_payment_income(self):
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='3000.85',
            date='2023-12-22',
            user=self.user
        )

        self.account_A.refresh_from_db()
        self.account_B.refresh_from_db()
        self.account_C.refresh_from_db()

        self.assertEqual(self.account_A.balance, Decimal('0.00'))
        self.assertEqual(self.account_B.balance, Decimal('3000.85'))
        self.assertEqual(self.account_C.balance, Decimal('0.00'))

    def test_payment_expenses(self):
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='2000.85',
            date='2023-12-22',
            user=self.user
        )

        Payment.objects.create(
            payment_type='expenses',
            charged_account=self.account_B,
            amount='254.13',
            date='2023-12-23',
            user=self.user
        )

        self.account_A.refresh_from_db()
        self.account_B.refresh_from_db()
        self.account_C.refresh_from_db()

        self.assertEqual(self.account_A.balance, Decimal('0.00'))
        self.assertEqual(self.account_B.balance, Decimal('1746.72'))
        self.assertEqual(self.account_C.balance, Decimal('0.00'))

    def test_payment_transfer(self):
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='3000.85',
            date='2023-12-22',
            user=self.user
        )

        Payment.objects.create(
            payment_type='transfer',
            charged_account=self.account_B,
            targed_account=self.account_A,
            amount='2054.11',
            date='2023-12-23',
            user=self.user
        )

        self.account_A.refresh_from_db()
        self.account_B.refresh_from_db()
        self.account_C.refresh_from_db()

        self.assertEqual(self.account_A.balance, Decimal('2054.11'))
        self.assertEqual(self.account_B.balance, Decimal('946.74'))
        self.assertEqual(self.account_C.balance, Decimal('0.00'))
