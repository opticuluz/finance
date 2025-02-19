from django.test import TestCase
from account.models import Account, Currency, CurrencyHistory
from payment.models import Payment
from report.models import Report
from django.contrib.auth import get_user_model
from report.tasks import create_report
from decimal import Decimal
from freezegun import freeze_time


class ReportTests(TestCase):
    def setUp(self):
        self.user_1 = get_user_model().objects.create_user(
            email='user_1@example.com',
            password='testpass123',
            name='Test User_1'
        )
        self.user_2 = get_user_model().objects.create_user(
            email='user_2@example.com',
            password='testpass123',
            name='Test User_2'
        )
        self.currency_usd = Currency.objects.create(
            title='USD',
            symbol='$'
            )
        self.currency_history_usd = CurrencyHistory.objects.create(
            date_and_time='2023-12-22 10:59:04+00:00',
            currency=self.currency_usd,
            rate_in_base=Decimal('1')
            )
        self.currency_gel = Currency.objects.create(
            title='GEL',
            symbol='₾',
            rate_in_base='2.79'
            )
        self.currency_history_gel = CurrencyHistory.objects.create(
            date_and_time='2023-08-16 10:59:04+00:00',
            currency=self.currency_gel,
            rate_in_base=Decimal('2.69')
            )
        self.account_A = Account.objects.create(
            account_name='A',
            currency=self.currency_usd,
            balance_in_base_currency='206502.58',
            user=self.user_1
            )
        self.account_B = Account.objects.create(
            account_name='B',
            currency=self.currency_usd,
            balance_in_base_currency='3748.42',
            credit_card_limit='5000',
            available_balance_in_base_currency='3746.72',
            user=self.user_1
            )
        self.account_C = Account.objects.create(
            account_name='C',
            currency=self.currency_gel,
            balance_in_base_currency='287.04',
            user=self.user_1
            )
        self.account_D = Account.objects.create(
            account_name='D',
            currency=self.currency_gel,
            balance_in_base_currency='1548.15',
            include_account_in_report=False,
            user=self.user_1
            )
        self.account_E = Account.objects.create(
            account_name='E',
            currency=self.currency_gel,
            balance_in_base_currency='887.73',
            user=self.user_2
            )

    @freeze_time("2024-12-31")
    def test_report(self):
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_A,
            amount='200500.86',
            date='2024-11-30',
            amount_in_base_currency='200500.86',
            user=self.user_1
        )
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_D,
            amount='80000.14',
            date='2024-12-01',
            amount_in_base_currency='28673.89',
            user=self.user_1
        )
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_E,
            amount='14000.27',
            date='2024-12-01',
            amount_in_base_currency='5018.02',
            user=self.user_2
        )
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_A,
            amount='3000.86',
            date='2024-12-01',
            amount_in_base_currency='3000.86',
            user=self.user_1
        )

        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='2000.85',
            date='2024-12-02',
            amount_in_base_currency='2000.85',
            user=self.user_1
        )

        Payment.objects.create(
            payment_type='expenses',
            charged_account=self.account_B,
            amount='254.13',
            date='2024-12-03',
            amount_in_base_currency='254.13',
            user=self.user_1
        )

        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='3000.85',
            date='2024-12-04',
            amount_in_base_currency='3000.85',
            user=self.user_1
        )

        Payment.objects.create(
            payment_type='transfer',
            charged_account=self.account_B,
            targed_account=self.account_A,
            amount='2054.11',
            date='2024-12-05',
            amount_in_base_currency='2054.11',
            user=self.user_1
        )

        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_C,
            amount='3000.85',
            date='2024-12-06',
            amount_in_base_currency='1075.57',
            include_payment_in_report=False,
            user=self.user_1
        )

        Payment.objects.create(
            payment_type='expenses',
            charged_account=self.account_C,
            amount='254.13',
            date='2024-12-07',
            amount_in_base_currency='91.09',
            include_payment_in_report=False,
            user=self.user_1
        )

        Payment.objects.create(
            payment_type='expenses',
            charged_account=self.account_B,
            amount='6000.85',
            date='2024-12-08',
            amount_in_base_currency='6000.85',
            user=self.user_1
        )

        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_C,
            amount='800.85',
            date='2024-12-09',
            amount_in_base_currency='287.04',
            user=self.user_1
        )

        create_report.apply(args=[self.user_1.id])

        self.report = Report.objects.filter(user=self.user_1).last()

        self.assertEqual(self.report.user, self.user_1)
        self.assertEqual(
            self.report.income_in_current_month,
            Decimal('8289.60')
            )
        self.assertEqual(
            self.report.expenses_in_current_month,
            Decimal('6254.98')
            )
        self.assertEqual(
            self.report.total_balance_in_base_currency,
            Decimal('210538.04')
            )
        self.assertEqual(
            self.report.total_available_balance_in_base_currency,
            Decimal('210536.34')
            )
