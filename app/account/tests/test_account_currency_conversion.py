from django.test import TestCase
from account.models import Account, Currency
from payment.models import Payment
from django.contrib.auth import get_user_model
from decimal import Decimal
from constance.test import override_config


class AccountCurrencyTests(TestCase):
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
            credit_card_limit=Decimal('5000.00'),
            user=self.user
            )
        self.account_B = Account.objects.create(
            account_name='B',
            currency=self.currency_gel,
            credit_card_limit=Decimal('500.00'),
            user=self.user
            )
        self.account_C = Account.objects.create(
            account_name='C',
            currency=self.currency_rub,
            credit_card_limit=Decimal('50000.00'),
            user=self.user
            )
        self.account_D = Account.objects.create(
            account_name='D',
            currency=self.currency_rub,
            user=self.user
            )

    @override_config(BASE_CURRENCY='USD')
    def test_account_amount_in_base_currency_conversion(self):
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_A,
            targed_account=None,
            amount='2020.85',
            date='2023-12-22',
            user=self.user
        )

        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='110.15',
            date='2023-12-23',
            user=self.user
        )

        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_C,
            amount='46328.15',
            date='2023-12-23',
            user=self.user
        )

        Payment.objects.create(
            payment_type='transfer',
            charged_account=self.account_C,
            targed_account=self.account_D,
            amount='13328.19',
            date='2023-12-23',
            user=self.user
        )

        self.account_A.refresh_from_db()
        self.account_B.refresh_from_db()
        self.account_C.refresh_from_db()
        self.account_D.refresh_from_db()

        self.assertEqual(self.account_A.balance, Decimal('2020.85'))
        self.assertEqual(self.account_B.balance, Decimal('110.15'))
        self.assertEqual(self.account_C.balance, Decimal('32999.96'))
        self.assertEqual(self.account_D.balance, Decimal('13328.19'))

        self.assertEqual(
            self.account_A.balance_in_base_currency,
            Decimal('2020.85')
            )
        self.assertEqual(
            self.account_B.balance_in_base_currency,
            Decimal('40.95')
            )
        self.assertEqual(
            self.account_C.balance_in_base_currency,
            Decimal('364.52')
            )
        self.assertEqual(
            self.account_D.balance_in_base_currency,
            Decimal('147.22')
            )

        self.assertEqual(self.account_A.available_balance, Decimal('7020.85'))
        self.assertEqual(self.account_B.available_balance, Decimal('610.15'))
        self.assertEqual(self.account_C.available_balance, Decimal('82999.96'))
        self.assertEqual(self.account_D.available_balance, Decimal('0.00'))

        self.assertEqual(
            self.account_A.available_balance_in_base_currency,
            Decimal('7020.85')
            )
        self.assertEqual(
            self.account_B.available_balance_in_base_currency,
            Decimal('226.82')
            )
        self.assertEqual(
            self.account_C.available_balance_in_base_currency,
            Decimal('916.82')
            )
        self.assertEqual(
            self.account_D.available_balance_in_base_currency,
            Decimal('0.00')
            )
