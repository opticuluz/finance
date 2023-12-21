from django.test import TestCase
from account.models import Account, Currency 
from payment.models import Payment
from django.contrib.auth import get_user_model
from django.test import Client
from decimal import Decimal

class PaymentTests(TestCase):
    def setUp(self):
        # Создаем тестовые данные
        self.user = get_user_model().objects.create_user(
            email='user_1@example.com',
            password='testpass123',
            name='Test User_1'
        )
        self.currency_usd = Currency.objects.create(title='USD', symbol='$')
        self.currency_gel = Currency.objects.create(title='GEL', symbol='₾')
        self.account_A = Account.objects.create(account_name='A', currency=self.currency_usd, user=self.user)
        self.account_B = Account.objects.create(account_name='B', currency=self.currency_usd, user=self.user)
        self.account_C = Account.objects.create(account_name='C', currency=self.currency_usd, user=self.user)
        

    def test_payment_income(self):
        # Создаем трату на сумму $300 с аккаунта B
        payment = Payment.objects.create(
            payment_type='income',
            charged_account=self.account_B,
            amount='3000.85',
            date='2023-12-22',
            user=self.user
        )

        # Обновляем балансы счетов
        self.account_A.refresh_from_db()
        self.account_B.refresh_from_db()
        self.account_C.refresh_from_db()

        # Проверяем, что балансы правильно обновились
        self.assertEqual(self.account_A.balance, Decimal('0.00'))  # Ожидаемый баланс счета A
        self.assertEqual(self.account_B.balance, Decimal('3000.85'))  # Ожидаемый баланс счета B
        self.assertEqual(self.account_C.balance, Decimal('0.00'))  # Ожидаемый баланс счета C


    def test_payment_expenses(self):
        # Создаем трату на сумму $300 с аккаунта B
        payment = Payment.objects.create(
            payment_type='expenses',
            charged_account=self.account_B,
            amount='254.13',
            date='2023-12-23',
            user=self.user
        )

        # Обновляем балансы счетов
        self.account_A.refresh_from_db()
        self.account_B.refresh_from_db()
        self.account_C.refresh_from_db()

        # Проверяем, что балансы правильно обновились
        self.assertEqual(self.account_A.balance, Decimal('0.00'))  # Ожидаемый баланс счета A
        self.assertEqual(self.account_B.balance, Decimal('2755.72'))  # Ожидаемый баланс счета B
        self.assertEqual(self.account_C.balance, Decimal('0.00'))  # Ожидаемый баланс счета C
