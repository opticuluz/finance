from finance.celery import app
from .models import Currency
import requests
from constance import config
from account.admin import base_currency_rate
from decimal import Decimal


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
            for currency_title, rate_value in rates.items():
                try:
                    currency = Currency.objects.get(title=currency_title)
                    currency.rate = rate_value
                    currency.save()
                    # currency.rate_in_base = rate_value
                    # currency.rate_in_base = base_currency_rate()
                    currency.rate_in_base = Decimal(currency.rate) / Decimal(base_currency_rate())
                    currency.save()
                except Currency.DoesNotExist:
                    pass
        else:
            pass
    else:
        return None
