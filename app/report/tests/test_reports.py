from django.test import TestCase
from account.models import Account, Currency
from payment.models import Payment
from report.models import Report
from django.contrib.auth import get_user_model
from report.tasks import create_report
from decimal import Decimal
import time
from freezegun import freeze_time
from datetime import datetime


class ReportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='user_1@example.com',
            password='testpass123',
            name='Test User_1'
        )
        self.currency_usd = Currency.objects.create(title='USD', symbol='$')
        self.currency_gel = Currency.objects.create(title='GEL', symbol='₾', rate_in_base='2.79')
        self.account_A = Account.objects.create(
            account_name='A',
            currency=self.currency_usd,
            # balance_in_base_currency='150.00',
            user=self.user
            )
        self.account_B = Account.objects.create(
            account_name='B',
            currency=self.currency_usd,
            balance_in_base_currency='0.00',
            credit_card_limit='5000',
            user=self.user
            )
        self.account_C = Account.objects.create(
            account_name='C',
            currency=self.currency_gel,
            balance_in_base_currency='0.00',
            user=self.user
            )


    @freeze_time("2024-12-31")
    def test_report(self):
        self.payment_1 = Payment.objects.create(
            payment_type='income',
            charged_account=self.account_A,
            amount='200500.86',
            date='2024-11-30',
            amount_in_base_currency='200500.86',
            user=self.user
        )
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_A,
            amount='3000.86',
            date='2024-12-01',
            amount_in_base_currency='3000.86',
            user=self.user
        )

        # self.account_A.refresh_from_db()
        # self.account_B.refresh_from_db()
        # self.account_C.refresh_from_db()

        # self.assertEqual(self.account_A.balance, Decimal('0.00'))
        # self.assertEqual(self.account_B.balance, Decimal('3000.85'))
        # self.assertEqual(self.account_C.balance, Decimal('0.00'))

    # def test_payment_expenses(self):
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='2000.85',
            date='2024-12-02',
            amount_in_base_currency='2000.85',
            user=self.user
        )

        Payment.objects.create(
            payment_type='expenses',
            charged_account=self.account_B,
            amount='254.13',
            date='2024-12-03',
            amount_in_base_currency='254.13',
            user=self.user
        )

        # self.account_A.refresh_from_db()
        # self.account_B.refresh_from_db()
        # self.account_C.refresh_from_db()

        # self.assertEqual(self.account_A.balance, Decimal('0.00'))
        # self.assertEqual(self.account_B.balance, Decimal('1746.72'))
        # self.assertEqual(self.account_C.balance, Decimal('0.00'))

    # def test_payment_transfer(self):
        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='3000.85',
            date='2024-12-04',
            amount_in_base_currency='3000.85',
            user=self.user
        )

        Payment.objects.create(
            payment_type='transfer',
            charged_account=self.account_B,
            targed_account=self.account_A,
            amount='2054.11',
            date='2024-12-05',
            amount_in_base_currency='2054.11',
            user=self.user
        )

        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_C,
            amount='3000.85',
            date='2024-12-06',
            amount_in_base_currency='1075.57',
            include_payment_in_report=False,
            user=self.user
        )

        Payment.objects.create(
            payment_type='expenses',
            charged_account=self.account_C,
            amount='254.13',
            date='2024-12-07',
            amount_in_base_currency='91.09',
            include_payment_in_report=False,
            user=self.user
        )

        Payment.objects.create(
            payment_type='expenses',
            charged_account=self.account_B,
            amount='6000.85',
            date='2024-12-08',
            amount_in_base_currency='6000.85',
            user=self.user
        )

        Payment.objects.create(
            payment_type='income',
            charged_account=self.account_C,
            amount='800.85',
            date='2024-12-09',
            amount_in_base_currency='287.04',
            user=self.user
        )

        self.account_A.refresh_from_db()
        self.account_B.refresh_from_db()
        self.account_C.refresh_from_db()
        # self.payment_1.refresh_from_db()



        # result = create_report
        result = create_report.apply(args=[self.user.id])
        self.assertEqual(result.status, 'SUCCESS')

        self.report = Report.objects.first()


        self.assertEqual(self.report.user, self.user)
        self.assertEqual(self.report.income_in_current_month, Decimal('8289.60'))
        self.assertEqual(self.report.expenses_in_current_month, Decimal('6254.98'))
        self.assertEqual(self.report.total_balance_in_base_currency, Decimal('208574.93'))
        # self.assertEqual(self.report.total_available_balance_in_base_currency, Decimal('0.00'))
