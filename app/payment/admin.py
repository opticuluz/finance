from django.contrib import admin  # , messages
# from django.utils.translation import gettext_lazy as _
from .models import Payment
from user.mixins import UserRestrictedAdminMixin
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP
from constance import config
from account.currency_conversion import base_currency_rate
from account.models import Account
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import ValidationError


class UserChargedAccountFilter(SimpleListFilter):
    title = 'charged account'
    parameter_name = 'charged_account_user'

    def lookups(self, request, model_admin):
        # Return the choices for the filter
        if not request.user.is_superuser:
            charged_accounts = Account.objects.filter(
                user=request.user
                ).order_by('account_name')
            return [(account.id, str(account)) for account in charged_accounts]
        else:
            charged_accounts = Account.objects.all().order_by('account_name')
            return [(account.id, str(account)) for account in charged_accounts]

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected filter value
        charged_account_id = self.value()
        if charged_account_id:
            return queryset.filter(charged_account_id=charged_account_id)
        return queryset

    def label_from_instance(self, obj):
        if obj.currency.title == 'USD':
            return f'{obj.account_name}: ${obj.balance}'
        else:
            sign = obj.currency.symbol
            return f'{obj.account_name}: {obj.balance} {sign}'


class PaymentAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    class Media:
        js = ['js/change_payment_form.js']

    ordering = ['-created_at']
    list_display = [
        'created_at',
        'payment_type',
        'charged_account',
        'targed_account',
        'amount',
        'amount_in_base_currency',
        'category',
        'date',
        'include_payment_in_report'
        ]
    list_filter = [
        'created_at',
        'date',
        'payment_type',
        UserChargedAccountFilter,
        'include_payment_in_report',
        'user'
        ]
    search_fields = ['amount']
    readonly_fields = [
        'amount_in_base_currency',
        'user',
        'created_at',
        'updated_at'
        ]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields['charged_account'].queryset = form.base_fields[
                'charged_account'
                ].queryset.filter(user=request.user)
            form.base_fields['targed_account'].queryset = form.base_fields[
                'targed_account'
                ].queryset.filter(user=request.user)
            form.base_fields['category'].queryset = form.base_fields[
                'category'
                ].queryset.filter(user=request.user, active=True)
        return form

    def save_model(self, request, obj, form, change):
        if obj.payment_type == 'transfer' and (obj.targed_account is None):
            raise ValidationError(
                'Target account must be specified for transfers.'
                )
        elif obj.payment_type == 'transfer' and (
            obj.charged_account == obj.targed_account
        ):
            raise ValidationError(
                'Charged account and target account cannot be the same.'
                )
        elif obj.payment_type != 'transfer' and obj.targed_account:
            raise ValidationError(
                'Target account must be empty for expenses and income.'
                )
        elif obj.date > timezone.localtime().date():
            raise ValidationError('Date cannot be in the future.')
        elif obj.amount == 0:
            raise ValidationError('Amount cannot be 0.')
        else:
            obj.user = request.user

        post_save.send(
            sender=Payment,
            instance=obj,
            dispatch_uid="update_payment_amount_in_base_currency"
            )

        super().save_model(request, obj, form, change)


def calculate_amount_in_base_currency(instance, **kwargs):
    rate = base_currency_rate()
    base_currency = config.BASE_CURRENCY
    if rate is not None:
        if instance.charged_account.currency.title == base_currency:
            instance.amount_in_base_currency = instance.amount
        else:
            amount_in_base_currency = Decimal(
                instance.amount
                /
                instance.charged_account.currency.rate_in_base
                )
            rounded_amount = amount_in_base_currency.quantize(
                Decimal('0.00'),
                rounding=ROUND_HALF_UP
                )
            instance.amount_in_base_currency = rounded_amount
    else:
        return None  # Вернуть None вместо вывода предупреждения
        # messages.warning(
        #     # request,
        #     _("Rate not found for %(currency)s")
        #     %
        #     {'currency': base_currency}
        # )


def calculate_balance_in_base_currency(instance, **kwargs):
    rate = base_currency_rate()
    base_currency = config.BASE_CURRENCY
    if rate is not None:
        if instance.currency.title == base_currency:
            instance.balance_in_base_currency = instance.balance
        else:
            balance_in_base_currency = Decimal(
                Decimal(instance.balance)
                /
                Decimal(instance.currency.rate_in_base)
                )
            rounded_amount = balance_in_base_currency.quantize(
                Decimal('0.00'),
                rounding=ROUND_HALF_UP
                )
            instance.balance_in_base_currency = rounded_amount
    else:
        return None  # Вернуть None вместо вывода предупреждения
        # messages.warning(
        #     # request,
        #     _("Rate not found for %(currency)s")
        #     %
        #     {'currency': base_currency}
        # )

    if instance.credit_card_limit != Decimal('0.0'):
        instance.available_balance = (
            Decimal(instance.balance) + instance.credit_card_limit
            )
        if instance.currency.title == config.BASE_CURRENCY:
            instance.credit_card_limit_in_base_currency = (
                instance.credit_card_limit
                )
            instance.available_balance_in_base_currency = (
                instance.available_balance
                )
        else:
            rate = instance.currency.rate
            if rate is None:
                instance.credit_card_limit_in_base_currency = Decimal('0.0')
                instance.available_balance_in_base_currency = Decimal('0.0')
            else:
                instance.credit_card_limit_in_base_currency = Decimal(
                    instance.credit_card_limit
                    /
                    instance.currency.rate_in_base
                    )
                rounded_amount_1 = (
                    instance.credit_card_limit_in_base_currency.quantize(
                        Decimal('0.00'),
                        rounding=ROUND_HALF_UP
                    )
                )
                instance.credit_card_limit_in_base_currency = rounded_amount_1
                instance.available_balance_in_base_currency = Decimal(
                    instance.available_balance
                    /
                    instance.currency.rate_in_base
                    )
                rounded_amount_2 = (
                    instance.available_balance_in_base_currency.quantize(
                        Decimal('0.00'),
                        rounding=ROUND_HALF_UP
                    )
                )
                instance.available_balance_in_base_currency = rounded_amount_2

    else:
        instance.available_balance = 0
        instance.credit_card_limit_in_base_currency = 0
        instance.available_balance_in_base_currency = 0


@receiver(
    [post_save, post_delete],
    sender=Payment,
    dispatch_uid="update_account_balance"
    )
def update_account_balance(sender, instance, **kwargs):
    charged_account = instance.charged_account

    charged_balance = charged_account.charged_payments.filter(
        payment_type='income'
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

    targed_balance = charged_account.targed_payments.filter(
            payment_type='transfer'
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

    charged_balance = charged_balance + targed_balance

    charged_balance -= charged_account.charged_payments.filter(
        payment_type__in=['expenses', 'transfer']
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

    charged_account.balance = charged_balance

    calculate_balance_in_base_currency(instance=charged_account)

    # if charged_account.currency.title == config.BASE_CURRENCY:
    #     charged_account.balance_in_base_currency = charged_account.balance
    # else:
    #     rate = charged_account.currency.rate
    #     if rate is None:
    #         charged_account.balance_in_base_currency = Decimal('0.0')
    #     else:
    #         rate = Decimal(base_currency_rate()) / rate
    #         charged_account.balance_in_base_currency = Decimal(
    #             charged_account.balance
    #             ) * rate
    charged_account.save()

    if instance.payment_type == 'transfer':
        targed_account = instance.targed_account
        if targed_account is not None:
            targed_balance1 = targed_account.targed_payments.filter(
                payment_type='transfer'
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

            targed_balance2 = targed_account.charged_payments.filter(
                payment_type='income'
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

            targed_balance = targed_balance1 + targed_balance2

            targed_balance -= targed_account.charged_payments.filter(
                payment_type='expenses'
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

            targed_balance -= targed_account.charged_payments.filter(
                payment_type='transfer'
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

            charged_balance -= charged_account.targed_payments.filter(
                payment_type='transfer'
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

            targed_account.balance = targed_balance

            # if targed_account.currency.title == config.BASE_CURRENCY:
            #     targed_account.balance_in_base_currency = (
            #         targed_account.balance
            #         )
            # else:
            #     rate = targed_account.currency.rate
            #     if rate is None:
            #         targed_account.balance_in_base_currency = Decimal('0.0')
            #     else:
            #         rate = Decimal(base_currency_rate()) / rate
            #         targed_account.balance_in_base_currency = Decimal(
            #             targed_account.balance
            #             ) * rate

            calculate_balance_in_base_currency(instance=targed_account)

            targed_account.save()


post_save.connect(update_account_balance, sender=Payment)
post_delete.connect(update_account_balance, sender=Payment)


@receiver(
    [post_save],
    sender=Payment,
    dispatch_uid="update_payment_amount_in_base_currency"
    )
def update_payment_amount_in_base_currency(sender, instance, **kwargs):

    calculate_amount_in_base_currency(instance=instance)


post_save.connect(update_payment_amount_in_base_currency, sender=Payment)


admin.site.register(Payment, PaymentAdmin)
