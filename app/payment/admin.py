from django.contrib import admin, messages
from .models import Payment
from user.mixins import UserRestrictedAdminMixin
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP
from constance import config
from account.admin import base_currency_rate
from account.models import Account
from django.contrib.admin import SimpleListFilter


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
        js = ['js/change_form.js']

    ordering = ['-created_at']
    list_display = [
        'created_at',
        'payment_type',
        'charged_account',
        'targed_account',
        'amount',
        'amount_in_base_currency',
        'category',
        'date'
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
        if obj.payment_type == 'transfer' and not obj.targed_account:
            messages.error(
                request,
                'Target account must be specified for transfers.'
                )
        elif obj.payment_type == 'transfer' and (
            obj.charged_account == obj.targed_account
        ):
            messages.error(
                request,
                'Charged account and target account cannot be the same.'
                )
        elif obj.payment_type != 'transfer' and obj.targed_account:
            messages.error(
                request,
                'Target account must be empty for expenses and income.'
                )
        elif obj.date > timezone.localtime().date():
            messages.error(request, 'Date cannot be in the future.')
        else:
            obj.user = request.user

        if obj.charged_account.currency.title == config.BASE_CURRENCY:
            obj.amount_in_base_currency = obj.amount
        else:
            rate = Decimal(
                (base_currency_rate())
                /
                obj.charged_account.currency.rate
                )

            amount_in_base_currency = Decimal(obj.amount) * rate
            rounded_amount = amount_in_base_currency.quantize(
                Decimal('0.00'),
                rounding=ROUND_HALF_UP
                )
            obj.amount_in_base_currency = rounded_amount
        super().save_model(request, obj, form, change)


@receiver([post_save, post_delete], sender=Payment)
def update_account_balance(sender, instance, **kwargs):
    charged_account = instance.charged_account

    charged_balance = charged_account.charged_payments.filter(
        payment_type='income'
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

    charged_balance -= charged_account.charged_payments.filter(
        payment_type__in=['expenses', 'transfer']
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

    charged_account.balance = charged_balance

    if charged_account.currency.title == config.BASE_CURRENCY:
        charged_account.balance_in_base_currency = charged_account.balance
    else:
        rate = charged_account.currency.rate
        if rate is None:
            charged_account.balance_in_base_currency = Decimal('0.0')
        else:
            rate = Decimal(base_currency_rate()) / rate
            charged_account.balance_in_base_currency = Decimal(
                charged_account.balance
                ) * rate
    charged_account.save()

    if instance.payment_type == 'transfer':
        targed_account = instance.targed_account

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

        targed_account.balance = targed_balance

        if targed_account.currency.title == config.BASE_CURRENCY:
            targed_account.balance_in_base_currency = (
                targed_account.balance
                )
        else:
            rate = targed_account.currency.rate
            if rate is None:
                targed_account.balance_in_base_currency = Decimal('0.0')
            else:
                rate = Decimal(base_currency_rate()) / rate
                targed_account.balance_in_base_currency = Decimal(
                    targed_account.balance
                    ) * rate
        targed_account.save()


post_save.connect(update_account_balance, sender=Payment)
post_delete.connect(update_account_balance, sender=Payment)


admin.site.register(Payment, PaymentAdmin)
