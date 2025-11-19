import os
from django.contrib import admin  # , messages
# from django.utils.translation import gettext_lazy as _
from .models import Payment, PaymentReceipt
from category.models import Category
from tag.models import Tag
from user.mixins import UserRestrictedAdminMixin
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
import decimal
from decimal import Decimal, ROUND_HALF_UP
from constance import config
from account.currency_conversion import base_currency_rate
from account.models import Account  # CurrencyHistory
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import ValidationError
from rangefilter.filters import (DateRangeFilterBuilder,
                                 DateTimeRangeFilterBuilder)
from dal import autocomplete
from django import forms
# from django.db.models import Avg
# from django.db.models.functions import TruncDate
# from datetime import datetime
from django.utils.html import format_html
from payment.utils import get_presigned_url
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model


class UserChargedAccountFilter(SimpleListFilter):
    title = 'charged account'
    parameter_name = 'charged_account_user'

    def lookups(self, request, model_admin):
        if not request.user.is_superuser:
            charged_accounts = Account.objects.filter(
                user=request.user
                ).order_by('account_name')
            return [(account.id, str(account)) for account in charged_accounts]
        else:
            charged_accounts = Account.objects.all().order_by('account_name')
            return [(account.id, str(account)) for account in charged_accounts]

    def queryset(self, request, queryset):
        charged_account_id = self.value()
        if charged_account_id:
            return queryset.filter(charged_account_id=charged_account_id)
        return queryset


class UserCategoryFilter(SimpleListFilter):
    title = 'category'
    parameter_name = 'category_user'

    def lookups(self, request, model_admin):
        if not request.user.is_superuser:
            categories = Category.objects.filter(
                user=request.user
                ).order_by('category_name')
            return [(category.id, str(category)) for category in categories]
        else:
            categories = Category.objects.all().order_by('category_name')
            return [(category.id, str(category)) for category in categories]

    def queryset(self, request, queryset):
        category_id = self.value()
        if category_id:
            return queryset.filter(category_id=category_id)
        return queryset


class UserTagFilter(SimpleListFilter):
    title = 'Tags'
    parameter_name = 'tags'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            tags = Tag.objects.filter(active=True).order_by('tag_name')
        else:
            tags = Tag.objects.filter(
                user=request.user,
                active=True
                ).order_by('tag_name')

        return [(tag.id, tag.tag_name) for tag in tags]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tags__id=self.value())
        return queryset


class DecimalWithoutTrailingZeroesWidget(forms.TextInput):
    def format_value(self, value):
        if value is None:
            return ''
        if isinstance(value, float) or isinstance(value, decimal.Decimal):
            value = "{:.18f}".format(value).rstrip('0')
            if value.endswith('.'):
                value += '00'
        return super().format_value(value)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"
        widgets = {
            "tags": autocomplete.ModelSelect2Multiple(url='tag-autocomplete'),
        }


# Кастомный виджет для поля image
class PresignedImageWidget(forms.ClearableFileInput):
    template_name = "django/forms/widgets/clearable_file_input.html"

    def format_value(self, value):
        if value:
            url = get_presigned_url(value.name)
            filename = os.path.basename(value.name)  # <- только имя файла
            return mark_safe(f'<a href="{url}" target="_blank">{filename}</a>')
        return super().format_value(value)


# Кастомная форма для inline
class PaymentReceiptInlineForm(forms.ModelForm):
    class Meta:
        model = PaymentReceipt
        fields = "__all__"
        widgets = {
            'image': PresignedImageWidget,
        }


class PaymentReceiptInline(admin.TabularInline):
    model = PaymentReceipt
    form = PaymentReceiptInlineForm
    extra = 1
    readonly_fields = ["uploaded_at", "preview"]
    fields = ["image", "preview", "uploaded_at"]

    def preview(self, obj):
        if obj.image:
            url = get_presigned_url(obj.image.name)
            return format_html(
                '<a href="{0}" target="_blank">'
                '<img src="{0}" width="200"/>'
                '</a>',
                url
            )
        return "-"
    preview.short_description = "Preview"


class PaymentAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    form = PaymentForm

    class Media:
        js = ['js/change_payment_form.js']

    inlines = [PaymentReceiptInline]

    ordering = ['-created_at']
    list_display = [
        'created_at',
        'payment_type',
        'charged_account',
        'targed_account',
        'get_amount',
        'amount_in_base_currency',
        'category',
        'date',
        'include_payment_in_report'
        ]
    list_filter = [
        ("created_at", DateTimeRangeFilterBuilder()),
        ('date', DateRangeFilterBuilder()),
        'payment_type',
        UserChargedAccountFilter,
        UserCategoryFilter,
        'include_payment_in_report',
        UserTagFilter,
        'user'
        ]
    search_fields = ['amount']
    readonly_fields = [
        'amount_in_base_currency',
        'user',
        'created_at',
        'updated_at'
        ]

    def get_amount(self, obj):
        if obj.charged_account.currency.cryptocurrency is None:
            return "{:.2f}".format(obj.amount)
        formatted_amount = "{:.18f}".format(obj.amount).rstrip('0')
        if formatted_amount.endswith('.'):
            formatted_amount += '00'
        return formatted_amount

    get_amount.short_description = 'Amount'

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
        form.base_fields['amount'].widget = (
            DecimalWithoutTrailingZeroesWidget()
        )
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

        # post_save.send(
        #     sender=Payment,
        #     instance=obj,
        #     dispatch_uid="update_payment_amount_in_base_currency"
        #     )
        # calculate_amount_in_base_currency(obj)

        super().save_model(request, obj, form, change)


# def calculate_amount_in_base_currency(instance, **kwargs):
#     instance_datetime = datetime.combine(instance.date, datetime.min.time())
#     transaction_date = timezone.make_aware(instance_datetime)
#     currency_histories = CurrencyHistory.objects.annotate(
#         date_only=TruncDate('date_and_time')
#         ).filter(
#             currency__title=instance.charged_account.currency.title,
#             date_only=TruncDate(transaction_date)
#         )
#     if currency_histories.exists():
#         average_rate = (currency_histories.aggregate(Avg('rate_in_base'))
#                         ['rate_in_base__avg']).quantize(
#                 Decimal('0.00'),
#                 rounding=ROUND_HALF_UP
#                 )
#     else:
#         latest_currency_history = CurrencyHistory.objects.filter(
#             currency__title=instance.charged_account.currency.title,
#             date_and_time__lt=transaction_date
#         ).order_by('-date_and_time').first()
#         if latest_currency_history:
#             average_rate = latest_currency_history.rate_in_base
#         else:
#             first_currency_history = CurrencyHistory.objects.filter(
#                 currency__title=instance.charged_account.currency.title
#             ).order_by('date_and_time').first()
#             average_rate = first_currency_history.rate_in_base

#     rate = base_currency_rate()
#     base_currency = config.BASE_CURRENCY
#     if rate is not None:
#         if instance.charged_account.currency.title == base_currency:
#             instance.amount_in_base_currency = instance.amount
#         else:
#             amount_in_base_currency = Decimal(
#                 instance.amount
#                 /
#                 average_rate
#                 )
#             rounded_amount = amount_in_base_currency.quantize(
#                 Decimal('0.00'),
#                 rounding=ROUND_HALF_UP
#                 )
#             instance.amount_in_base_currency = rounded_amount
#     else:
#         return None  # Вернуть None вместо вывода предупреждения
#         # messages.warning(
#         #     # request,
#         #     _("Rate not found for %(currency)s")
#         #     %
#         #     {'currency': base_currency}
#         # )


def calculate_balance_in_base_currency(instance, **kwargs):
    rate = base_currency_rate()
    base_currency = config.BASE_CURRENCY
    if rate is not None:
        if instance.currency.title == base_currency:
            instance.balance_in_base_currency = instance.balance
        else:
            if instance.currency.cryptocurrency:
                balance_in_base_currency = Decimal(
                    Decimal(instance.balance)
                    *
                    Decimal(instance.currency.rate_in_base)
                    )
                rounded_amount = balance_in_base_currency.quantize(
                    Decimal('0.00'),
                    rounding=ROUND_HALF_UP
                    )
                instance.balance_in_base_currency = rounded_amount
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


# post_save.connect(update_account_balance, sender=Payment)
# post_delete.connect(update_account_balance, sender=Payment)


# @receiver(
#     [post_save],
#     sender=Payment,
#     dispatch_uid="update_payment_amount_in_base_currency"
#     )
# def update_payment_amount_in_base_currency(sender, instance, **kwargs):

#     calculate_amount_in_base_currency(instance=instance)


# post_save.connect(update_payment_amount_in_base_currency, sender=Payment)


admin.site.register(Payment, PaymentAdmin)


User = get_user_model()


# Кастомный фильтр по пользователям
class PaymentUserFilter(SimpleListFilter):
    title = "Payment User"
    parameter_name = "payment_user"

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            users = User.objects.all()
            return [(u.id, u.email) for u in users]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payment__user__id=self.value())
        return queryset


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(UserRestrictedAdminMixin, admin.ModelAdmin):

    # ОТКЛЮЧИТЬ действия в разделе
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    related_user_field = "payment__user"
    list_display = (
        "uploaded_at",
        "payment__id",
        "image_link",
        )
    readonly_fields = (
        "payment",
        "uploaded_at",
        "image_link",
        "payment_user_email",
        )
    search_fields = ("payment__id",)

    # Добавляем фильтр по юзерам только для суперюзеров
    def get_list_filter(self, request):
        filters = [
            ("uploaded_at", DateTimeRangeFilterBuilder()),
        ]
        if request.user.is_superuser:
            filters.append(PaymentUserFilter)
        return filters

    # Формируем поля формы: убираем 'image', оставляем только превью
    fields = ("payment", "image_link", "payment_user_email", "uploaded_at")

    def image_link(self, obj):
        """Показывает превью изображения через presigned URL."""
        if obj.image:
            url = get_presigned_url(obj.image.name)
            return format_html(
                '<a href="{0}" target="_blank">'
                '<img src="{0}" width="200"/>'
                '</a>',
                url
            )
        return "-"
    image_link.short_description = "Receipt Preview"

    def payment_user_email(self, obj):
        return obj.payment.user.email
    payment_user_email.short_description = "User"
