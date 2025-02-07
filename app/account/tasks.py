import json
from finance.celery import app
import celery
from .models import Account, Currency, CurrencyHistory
from crypto.models import CryptoCurrency
from goal.models import Goal
from payment.models import Payment
import requests
from constance import config
from account.currency_conversion import base_currency_rate
from decimal import Decimal, ROUND_HALF_UP
from logs.models import LogEntry, LogEntryCrypto
from payment.models import calculate_amount_in_base_currency
from datetime import datetime
from django.utils.timezone import make_aware
from report.tasks import create_report
from django.db import transaction


@app.task
def update_all_data():
    sync = celery.chain(
        get_currency_rates.s(),
        calculate_currency_rate_in_base.s(),
        recalculate_amount_in_base_currency.si(),
        recalculate_balance_in_base_currency.si(),
        create_report.si(),
        recalculate_goal_sum_in_base_currency.si(),
        recalculate_goal_data.si(),
        get_crypto_list.si(),
        fill_crypto_list.s(),
        get_crypto_rate.si(),
        fill_crypto_rate.s(),
    )
    sync.delay()


@app.task
def get_currency_rates(test=False):
    if test:
        rates_data = '''{"base": "EUR", "date": "2024-08-05",
        "rates": {"CAD": 1.518274, "EUR": 1, "GEL": 2.965777,
        "RSD": 117.024179, "RUB": 93.192269, "SEK": 11.529046,
        "USD": 1.096389}, "success": true, "timestamp": 1722859384}'''
        data = json.loads(rates_data)
    else:
        access_key = config.FIXER_ACCESS_KEY
        fixer_url = config.FIXER_URL
        currency_titles = Currency.objects.values_list('title', flat=True)
        currency_titles_str = ','.join(currency_titles)
        url = f'{fixer_url}?access_key={access_key
                                        }&symbols={currency_titles_str}'
        response = requests.get(url)
        data = response.json()
        LogEntry.objects.create(data=data)
    return data


@app.task
def recalculate_rates_in_history():
    data_list = LogEntry.objects.order_by('id').values_list('data', flat=True)
    for data in data_list:
        calculate_currency_rate_in_base(data)


@app.task
def calculate_currency_rate_in_base(data):
    if not data.get('success'):
        error_info = data.get('error', {}).get('info', 'Unknown error')
        print(f"API Error: {error_info}")
        return
    rates = data.get('rates')
    if not rates:
        print("No rates data available")
        return
    rate_for_base = rates.get(config.BASE_CURRENCY)
    if not rate_for_base:
        print("Base currency not found in rates")
        return
    timestamp = data.get('timestamp')
    for currency_title, rate_value in rates.items():
        rate_in_base = (
            Decimal(rate_value) / Decimal(rate_for_base)
        ).quantize(
            Decimal('0.00'),
            rounding=ROUND_HALF_UP
        )
        naive_datetime = datetime.fromtimestamp(timestamp)
        aware_datetime = make_aware(naive_datetime)
        currency_instance = Currency.objects.get(title=currency_title)
        CurrencyHistory.objects.update_or_create(
            currency=currency_instance,
            date_and_time=aware_datetime,
            defaults={
                'rate_in_base': rate_in_base,
                'base_currency': config.BASE_CURRENCY
            }
        )

# old task - delete in the future

# @app.task
# def update_all_rates(data):
#     rates = data.get('rates')
    # currency = Currency.objects.get(title=config.BASE_CURRENCY)
    # currency.rate = rate_for_base
    # currency.rate_in_base = 1
    # currency.save()
    # for currency_title, rate_value in rates.items():
    #     try:
        currency = Currency.objects.get(title=currency_title)
        currency.rate = rate_value
        currency.rate_in_base = rate_in_base
        currency.save()
        # except Currency.DoesNotExist:
        #     pass


@app.task
def recalculate_balance_in_base_currency():

    accounts = Account.objects.all()

    with transaction.atomic():
        for account in accounts:
            if account.currency.title == config.BASE_CURRENCY:
                # account.balance_in_base_currency = account.balance
                Account.objects.filter(id=account.id).update(
                    balance_in_base_currency=account.balance
                    )
            else:
                rate = account.currency.rate
                if rate is None:
                    # account.balance_in_base_currency = Decimal('0.0')
                    Account.objects.filter(id=account.id).update(
                        balance_in_base_currency=Decimal('0.0')
                        )
                else:
                    rate = Decimal(base_currency_rate()) / rate
                    # account.balance_in_base_currency = Decimal(
                    #     account.balance
                    #     ) * rate
                    Account.objects.filter(id=account.id).update(
                        balance_in_base_currency=Decimal(
                            account.balance
                        ) * rate
                    )

            if account.credit_card_limit != Decimal('0.0'):
                # account.available_balance = (
                #     Decimal(account.balance) + account.credit_card_limit
                #     )
                Account.objects.filter(id=account.id).update(
                    available_balance=(
                        Decimal(account.balance) + account.credit_card_limit
                    )
                )
                if account.currency.title == config.BASE_CURRENCY:
                    # account.credit_card_limit_in_base_currency = (
                    #     account.credit_card_limit
                    # )
                    Account.objects.filter(id=account.id).update(
                        credit_card_limit_in_base_currency=(
                            account.credit_card_limit
                        )
                    )
                    # account.available_balance_in_base_currency = (
                    #     account.available_balance
                    # )
                    Account.objects.filter(id=account.id).update(
                        available_balance_in_base_currency=(
                            account.available_balance
                        )
                    )
                else:
                    rate = account.currency.rate
                    if rate is None:
                        # account.credit_card_limit_in_base_currency = \
                        # Decimal('0.0')
                        Account.objects.filter(id=account.id).update(
                            credit_card_limit_in_base_currency=Decimal('0.0')
                            )
                        # account.available_balance_in_base_currency = \
                        # Decimal('0.0')
                        Account.objects.filter(id=account.id).update(
                            available_balance_in_base_currency=Decimal('0.0')
                            )
                    else:
                        rate = Decimal(base_currency_rate()) / rate
                        # account.credit_card_limit_in_base_currency = (
                        #     Decimal(account.credit_card_limit) * rate
                        #     )
                        Account.objects.filter(id=account.id).update(
                            credit_card_limit_in_base_currency=(
                                Decimal(account.credit_card_limit) * rate
                            )
                        )
                        # account.available_balance_in_base_currency = (
                        #     Decimal(account.available_balance) * rate
                        #     )
                        Account.objects.filter(id=account.id).update(
                            available_balance_in_base_currency=(
                                Decimal(account.available_balance) * rate
                            )
                        )
            else:
                # account.available_balance = 0
                Account.objects.filter(id=account.id).update(
                    available_balance=0
                    )
                # account.credit_card_limit_in_base_currency = 0
                Account.objects.filter(id=account.id).update(
                    credit_card_limit_in_base_currency=0
                    )
                # account.available_balance_in_base_currency = 0
                Account.objects.filter(id=account.id).update(
                    available_balance_in_base_currency=0
                    )


@app.task
def recalculate_amount_in_base_currency():

    payments = Payment.objects.all()

    with transaction.atomic():
        for payment in payments:
            calculate_amount_in_base_currency(payment)


@app.task
def recalculate_goal_data():

    goals = Goal.objects.all()

    with transaction.atomic():
        for goal in goals:
            goal.calculate_goal_data()


@app.task
def recalculate_goal_sum_in_base_currency():

    goals = Goal.objects.all()

    with transaction.atomic():
        for goal in goals:
            if goal.currency.title == config.BASE_CURRENCY:
                # account.balance_in_base_currency = account.balance
                Goal.objects.filter(id=goal.id).update(
                    sum_in_base=goal.sum
                    )
            else:
                rate = goal.currency.rate
                if rate is None:
                    # account.balance_in_base_currency = Decimal('0.0')
                    Goal.objects.filter(id=goal.id).update(
                        sum_in_base=Decimal('0.0')
                        )
                else:
                    rate = Decimal(base_currency_rate()) / rate
                    # account.balance_in_base_currency = Decimal(
                    #     account.balance
                    #     ) * rate
                    Goal.objects.filter(id=goal.id).update(
                        sum_in_base=Decimal(goal.sum) * rate
                    )


@app.task
def get_crypto_list():
    type = 'List'
    x_cmc_pro_url = config.X_CMC_PRO_URL
    x_cmc_pro_access_key = config.X_CMC_PRO_API_KEY
    url = f'{x_cmc_pro_url}/v1/cryptocurrency/map'
    headers = {
        "X-CMC_PRO_API_KEY": x_cmc_pro_access_key
    }
    params = {
        "listing_status": "active",
        "limit": 100,
        "sort": "cmc_rank"
    }
    response = requests.get(url, headers=headers, params=params)
    crypto_data_list = response.json()
    LogEntryCrypto.objects.create(data=crypto_data_list, type=type)
    return crypto_data_list


@app.task
def fill_crypto_list(crypto_data_list):
    if not crypto_data_list.get('data'):
        error_info = crypto_data_list.get('error', {}).get(
            'error_message',
            'Unknown error'
            )
        print(f"API Error: {error_info}")
        return
    crypto_list = crypto_data_list.get('data')
    if not crypto_list:
        print("No crypto list available")
        return
    for item in crypto_list:
        CryptoCurrency.objects.update_or_create(
            cmc_id=item.get('id'),
            defaults={
                "cmc_rank": item.get('rank'),
                "title": item.get('name'),
                "symbol": item.get('symbol')
            }
        )


@app.task
def get_crypto_rate():
    type = 'Rate'
    x_cmc_pro_url = config.X_CMC_PRO_URL
    x_cmc_pro_access_key = config.X_CMC_PRO_API_KEY
    active_currencies = CryptoCurrency.objects.filter(
        is_active=True
        ).values_list('cmc_id', flat=True)
    ids = ",".join(map(str, sorted(list(active_currencies))))
    url = f'{x_cmc_pro_url}/v2/cryptocurrency/quotes/latest'
    headers = {
        "X-CMC_PRO_API_KEY": x_cmc_pro_access_key
    }
    params = {
        "id": ids,
        "convert": config.BASE_CURRENCY
    }
    response = requests.get(url, headers=headers, params=params)
    crypto_data_rate = response.json()
    LogEntryCrypto.objects.create(data=crypto_data_rate, type=type)
    return crypto_data_rate


@app.task
def fill_crypto_rate(crypto_data_rate):
    if not crypto_data_rate.get('data'):
        error_info = crypto_data_rate.get('error', {}).get(
            'error_message',
            'Unknown error'
            )
        print(f"API Error: {error_info}")
        return
    crypto_rate = crypto_data_rate.get('data')
    if not crypto_rate:
        print("No crypto rate available")
        return
    for id, price_data in crypto_rate.items():
        rate = price_data['quote'][config.BASE_CURRENCY]['price']
        CryptoCurrency.objects.update_or_create(
            cmc_id=id,
            defaults={
                "rate_in_base": rate
            }
        )
