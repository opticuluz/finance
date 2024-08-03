from django.test import TestCase
from account.models import Account, Currency
# from django.contrib.auth import get_user_model
from account.tasks import update_all_rates
# from decimal import Decimal
# from constance import config
from constance.test import override_config


class CurrencyConversionTests(TestCase):
    def setUp(self):
        # self.user = get_user_model().objects.create_user(
        #     email='user_1@example.com',
        #     password='testpass123',
        #     name='Test User_1'
        # )
        self.currency_usd = Currency.objects.create(
            title='USD',
            symbol='$'
            )
        self.currency_usd = Currency.objects.create(
            title='RUB',
            symbol='₽'
            )
        self.currency_usd = Currency.objects.create(
            title='GEL',
            symbol='₾'
            )
        
    @override_config(BASE_CURRENCY='USD')
    def test_currency_conversion(self):
        result = update_all_rates.apply()
        assert result.result == 10




