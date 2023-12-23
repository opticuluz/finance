from django.test import TestCase, override_settings
from account.models import Account, Currency
from payment.models import Payment
from django.contrib.auth import get_user_model
from decimal import Decimal
from constance import config


class PaymentCurrencyTests(TestCase):
    @override_settings(BASE_CURRENCY='USD')
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='user_1@example.com',
            password='testpass123',
            name='Test User_1'
        )
        # print(config.BASE_CURRENCY)
        self.currency_usd = Currency.objects.create(title='USD', symbol='$', rate=Decimal('1.091685'), rate_in_base=Decimal('1'))
        self.currency_gel = Currency.objects.create(title='GEL', symbol='₾', rate=Decimal('2.937159'), rate_in_base=Decimal('2.69'))
        self.currency_rub = Currency.objects.create(title='RUB', symbol='₽', rate=Decimal('98.824810'), rate_in_base=Decimal('90.53'))
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

    def test_payment_amount_in_base_currency_conversion(self):
        payment_1 = Payment(
            payment_type='income',
            charged_account=self.account_A,
            targed_account=None,
            amount='3000.85',
            date='2023-12-22',
            user=self.user
        )
        # admin_instance = PaymentAdmin(model=Payment, admin_site=admin.site)
        # admin_instance.save_model(request=None, obj=Payment, form=None, change=None)
        payment_1.save()
        saved_payment_1 = Payment.objects.get(pk=payment_1.pk)
        print(saved_payment_1.amount_in_base_currency)

        payment_2 = Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='400.15',
            date='2023-12-23',
            user=self.user
        )

        payment_3 = Payment(
            payment_type='income',
            charged_account=self.account_C,
            amount='400.15',
            date='2023-12-23',
            user=self.user
        )
        payment_3.save()
        saved_payment_3 = Payment.objects.get(pk=payment_3.pk)
        # print(saved_payment.amount)

        # self.payment_1.refresh_from_db()
        # self.payment_2.refresh_from_db()
        # self.payment_3.refresh_from_db()

        self.assertEqual(saved_payment_1.amount_in_base_currency, Decimal('3000.85'))
        self.assertEqual(payment_2.amount_in_base_currency, Decimal('0.00'))
        self.assertEqual(saved_payment_3.amount_in_base_currency, Decimal('160.06'))





    # def test_payment_income(self):
    #     Payment.objects.create(
    #         payment_type='income',
    #         charged_account=self.account_B,
    #         amount='3000.85',
    #         date='2023-12-22',
    #         user=self.user
    #     )

    #     self.account_A.refresh_from_db()
    #     self.account_B.refresh_from_db()
    #     self.account_C.refresh_from_db()

    #     self.assertEqual(self.account_A.balance, Decimal('0.00'))
    #     self.assertEqual(self.account_B.balance, Decimal('3000.85'))
    #     self.assertEqual(self.account_C.balance, Decimal('0.00'))

    # def test_payment_expenses(self):
    #     Payment.objects.create(
    #         payment_type='income',
    #         charged_account=self.account_B,
    #         amount='2000.85',
    #         date='2023-12-22',
    #         user=self.user
    #     )

    #     Payment.objects.create(
    #         payment_type='expenses',
    #         charged_account=self.account_B,
    #         amount='254.13',
    #         date='2023-12-23',
    #         user=self.user
    #     )

    #     self.account_A.refresh_from_db()
    #     self.account_B.refresh_from_db()
    #     self.account_C.refresh_from_db()

    #     self.assertEqual(self.account_A.balance, Decimal('0.00'))
    #     self.assertEqual(self.account_B.balance, Decimal('1746.72'))
    #     self.assertEqual(self.account_C.balance, Decimal('0.00'))