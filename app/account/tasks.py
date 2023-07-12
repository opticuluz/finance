from finance.celery import app
import celery
from .models import Account, Currency
import requests
from constance import config
from account.admin import base_currency_rate
from decimal import Decimal
from report.tasks import create_report


@app.task
def update_all_data():
    sync = celery.chain(
        update_all_rates.si(),
        recalculate_balance_in_base_currency.si(),
        create_report.si()
    )
    sync.delay()


@app.task
def update_all_rates():
    currency_titles = Currency.objects.values_list('title', flat=True)
    currency_titles_str = ','.join(currency_titles)

    access_key = config.FIXER_ACCESS_KEY
    fixer_url = config.FIXER_URL
    url = f'{fixer_url}?access_key={access_key}&symbols={currency_titles_str}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        rates = data.get('rates')
        if rates:
            rate_for_base = rates.pop(config.BASE_CURRENCY)
            currency = Currency.objects.get(title=config.BASE_CURRENCY)
            currency.rate = rate_for_base
            currency.rate_in_base = 1
            currency.save()
            for currency_title, rate_value in rates.items():
                try:
                    currency = Currency.objects.get(title=currency_title)
                    currency.rate = rate_value
                    currency.rate_in_base = (
                        Decimal(currency.rate) / Decimal(base_currency_rate())
                        )
                    currency.save()
                except Currency.DoesNotExist:
                    pass
        else:
            pass
    else:
        return None


@app.task
def recalculate_balance_in_base_currency():

    queryset = Account.objects.all()

    for account in queryset:
        if account.currency.title == config.BASE_CURRENCY:
            account.balance_in_base_currency = account.balance
        else:
            rate = account.currency.rate
            if rate is None:
                account.balance_in_base_currency = Decimal('0.0')
            else:
                rate = Decimal(base_currency_rate()) / rate
                account.balance_in_base_currency = Decimal(
                    account.balance
                    ) * rate

        if account.credit_card_limit != Decimal('0.0'):
            account.available_balance = (
                Decimal(account.balance) + account.credit_card_limit
                )
            if account.currency.title == config.BASE_CURRENCY:
                account.credit_card_limit_in_base_currency = (
                    account.credit_card_limit
                )
                account.available_balance_in_base_currency = (
                    account.available_balance
                )
            else:
                rate = account.currency.rate
                if rate is None:
                    account.credit_card_limit_in_base_currency = Decimal('0.0')
                    account.available_balance_in_base_currency = Decimal('0.0')
                else:
                    rate = Decimal(base_currency_rate()) / rate
                    account.credit_card_limit_in_base_currency = (
                        Decimal(account.credit_card_limit) * rate
                        )
                    account.available_balance_in_base_currency = (
                        Decimal(account.available_balance) * rate
                        )
        else:
            account.available_balance = 0
            account.credit_card_limit_in_base_currency = 0
            account.available_balance_in_base_currency = 0

        account.save()
