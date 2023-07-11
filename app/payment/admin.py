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
from report.tasks import create_report


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
        # 'charged_account',
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
            # super().save_model(request, obj, form, change)

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
        charged_account.save()

        if charged_account.currency.title == config.BASE_CURRENCY:
            charged_account.balance_in_base_currency = charged_account.balance
        else:
            rate = (
                Decimal(base_currency_rate())
                /
                charged_account.currency.rate
                )
            if rate:
                charged_account.balance_in_base_currency = (
                    charged_account.balance * rate
                    )
            else:
                charged_account.balance_in_base_currency = None
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
            targed_account.save()

            if targed_account.currency.title == config.BASE_CURRENCY:
                targed_account.balance_in_base_currency = (
                    targed_account.balance
                    )
            else:
                rate = (
                    Decimal(base_currency_rate())
                    /
                    targed_account.currency.rate
                    )
                if rate:
                    targed_account.balance_in_base_currency = (
                        targed_account.balance * rate
                        )
                else:
                    targed_account.balance_in_base_currency = None
            targed_account.save()

    post_save.connect(update_account_balance, sender=Payment)
    post_delete.connect(update_account_balance, sender=Payment)


@receiver([post_save, post_delete], sender=Payment)
def create_report_on_payment_item_save(sender, instance, **kwargs):
    create_report.delay()


admin.site.register(Payment, PaymentAdmin)
