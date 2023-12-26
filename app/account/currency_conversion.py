from .models import Account, Currency
from constance import config

def base_currency_rate():
    base_currency = config.BASE_CURRENCY
    try:
        base_currency_obj = Currency.objects.get(title=base_currency)
        if base_currency_obj.rate:
            return base_currency_obj.rate
        else:
            return None  # Вернуть None вместо вывода предупреждения
            # messages.warning(
            #     # request,
            #     _("Rate not found for %(currency)s")
            #     %
            #     {'currency': base_currency}
            # )
    except Currency.DoesNotExist:
        return None  # Вернуть None вместо вывода предупреждения
        # messages.warning(
        #     # request,
        #     _("Base currency %(currency)s not found")
        #     %
        #     {'currency': base_currency}
        # )

    return None
