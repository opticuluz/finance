from django.test import TestCase, override_settings
from account.models import Account, Currency
from payment.models import Payment
from django.contrib.auth import get_user_model
from decimal import Decimal
from constance import config
from constance.test import override_config


class PaymentCurrencyTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='user_1@example.com',
            password='testpass123',
            name='Test User_1'
        )
        self.currency_usd = Currency.objects.create(
            title='USD',
            symbol='$',
            rate=Decimal('1.091685'),
            rate_in_base=Decimal('1')
            )
        self.currency_gel = Currency.objects.create(
            title='GEL',
            symbol='₾',
            rate=Decimal('2.937159'),
            rate_in_base=Decimal('2.69')
            )
        self.currency_rub = Currency.objects.create(
            title='RUB',
            symbol='₽',
            rate=Decimal('98.824810'),
            rate_in_base=Decimal('90.53')
            )
        self.account_A = Account.objects.create(
            account_name='A',
            currency=self.currency_usd,
            user=self.user
            )
        self.account_B = Account.objects.create(
            account_name='B',
            currency=self.currency_gel,
            user=self.user
            )
        self.account_C = Account.objects.create(
            account_name='C',
            currency=self.currency_rub,
            user=self.user
            )

    @override_config(BASE_CURRENCY='USD')
    def test_payment_amount_in_base_currency_conversion(self):
        payment_1 = Payment.objects.create(
            payment_type='income',
            charged_account=self.account_A,
            targed_account=None,
            amount='2020.85',
            date='2023-12-22',
            user=self.user
        )

        payment_2 = Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='110.15',
            date='2023-12-23',
            user=self.user
        )

        payment_3 = Payment.objects.create(
            payment_type='income',
            charged_account=self.account_C,
            amount='46328.15',
            date='2023-12-23',
            user=self.user
        )

        self.assertEqual(payment_1.amount_in_base_currency, Decimal('2020.85'))
        self.assertEqual(payment_2.amount_in_base_currency, Decimal('40.95'))
        self.assertEqual(payment_3.amount_in_base_currency, Decimal('511.74'))
