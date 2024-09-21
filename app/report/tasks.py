from finance.celery import app
from datetime import datetime
from django.db.models import Sum, Q, Case, When, Value
from django.db import models
from report.models import Report, Report_for_category
from account.models import Account, CurrencyHistory
from payment.models import Payment
from category.models import Category
from user.models import User
from django.db import transaction
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.utils import timezone


@app.task
def create_report(user_id=None):

    if user_id:
        with transaction.atomic():
            User.objects.select_for_update().get(id=user_id)
            create_report_for_user(user_id)
            create_report_for_category_for_user(user_id)
    else:
        user_ids = User.objects.values_list('id', flat=True)
        for user_id in user_ids:
            with transaction.atomic():
                User.objects.select_for_update().get(id=user_id)
                create_report_for_user(user_id)
                create_report_for_category_for_user(user_id)


def create_report_for_user(user_id):
    queryset = Account.objects.filter(
        include_account_in_report=True,
        user=user_id
        )

    user = User.objects.get(id=user_id)

    first_payment = Payment.objects.filter(
        user=user_id
        ).order_by('date').first()
    if first_payment:
        first_payment_date = first_payment.date
    else:
        return

    current_month_start = datetime.now().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
        )

    month_to_process = first_payment_date.replace(day=1)

    while month_to_process <= current_month_start.date():
        current_year_start = month_to_process.replace(month=1)

        if not queryset:
            report = Report.objects.filter(
                user=user,
                created_at__year=month_to_process.year,
                created_at__month=month_to_process.month
            ).last()

            if report:
                report.total_balance_in_base_currency = 0
                report.total_available_balance_in_base_currency = 0
                report.income_in_current_month = 0
                report.expenses_in_current_month = 0
                report.income_in_current_year = 0
                report.expenses_in_current_year = 0
                report.save()

        income = queryset.annotate(
            total_income=Sum(
                'charged_payments__amount_in_base_currency',
                filter=Q(
                    charged_payments__payment_type='income',
                    charged_payments__include_payment_in_report=True,
                    charged_payments__date__gte=month_to_process,
                    charged_payments__date__lt=(
                        month_to_process + relativedelta(months=1)
                        )
                    )
                )
        ).values('total_income').aggregate(
            Sum('total_income')
            )['total_income__sum'] or 0.0
        expenses = queryset.annotate(
            total_expenses=Sum(
                'charged_payments__amount_in_base_currency',
                filter=Q(
                    charged_payments__payment_type='expenses',
                    charged_payments__include_payment_in_report=True,
                    charged_payments__date__gte=month_to_process,
                    charged_payments__date__lt=(
                        month_to_process + relativedelta(months=1)
                        )
                    )
                )
        ).values('total_expenses').aggregate(
            Sum('total_expenses')
            )['total_expenses__sum'] or 0.0

        income_year = queryset.annotate(
            total_income=Sum(
                'charged_payments__amount_in_base_currency',
                filter=Q(
                    charged_payments__payment_type='income',
                    charged_payments__include_payment_in_report=True,
                    charged_payments__date__gte=current_year_start,
                    charged_payments__date__lt=(
                        month_to_process + relativedelta(months=1)
                        )
                    )
                )
        ).values('total_income').aggregate(
            Sum('total_income')
            )['total_income__sum'] or 0.0
        expenses_year = queryset.annotate(
            total_expenses=Sum(
                'charged_payments__amount_in_base_currency',
                filter=Q(
                    charged_payments__payment_type='expenses',
                    charged_payments__include_payment_in_report=True,
                    charged_payments__date__gte=current_year_start,
                    charged_payments__date__lt=(
                        month_to_process + relativedelta(months=1)
                        )
                    )
                )
        ).values('total_expenses').aggregate(
            Sum('total_expenses')
            )['total_expenses__sum'] or 0.0

        total_balance = Decimal('0.0')
        total_available_balance = Decimal('0.0')

        if month_to_process < current_month_start.date():
            end_date = month_to_process + relativedelta(months=1)
            accounts = Account.objects.filter(
                user=user_id
            )
            for account in accounts:

                charged_balance = account.charged_payments.filter(
                    payment_type='income',
                    date__lt=end_date,
                    user=user_id
                    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

                targed_balance = account.targed_payments.filter(
                    payment_type='transfer',
                    date__lt=end_date,
                    user=user_id
                    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

                charged_balance = charged_balance + targed_balance

                charged_balance -= account.charged_payments.filter(
                    payment_type__in=['expenses', 'transfer'],
                    date__lt=end_date,
                    user=user_id
                    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0')

                end_date_with_time = datetime.combine(
                    end_date,
                    datetime.min.time()
                    )
                end_date_with_time = timezone.make_aware(
                    end_date_with_time,
                    timezone.get_current_timezone()
                    )
                currency_rate = CurrencyHistory.objects.filter(
                    currency__id=account.currency.id,
                    date_and_time__lt=end_date_with_time
                ).order_by('-date_and_time').first()

                available_balance = Decimal(
                    charged_balance + account.credit_card_limit
                    )

                if currency_rate:
                    total_balance_in_base_currency = Decimal(
                        charged_balance / currency_rate.rate_in_base
                        )
                    available_balance_in_base = Decimal(
                        available_balance / currency_rate.rate_in_base
                        )
                else:
                    total_balance_in_base_currency = Decimal('0.0')
                    available_balance_in_base = Decimal('0.0')

                total_balance += total_balance_in_base_currency
                total_available_balance += available_balance_in_base

        else:
            total_balance = queryset.aggregate(
                total_balance=Sum('balance_in_base_currency')
                )['total_balance'] or 0.0

            total_available_balance = queryset.aggregate(
                total_balance=Sum(
                    Case(
                        When(
                            credit_card_limit=0,
                            then='balance_in_base_currency'
                            ),
                        default=Value(0),
                        output_field=models.DecimalField(),
                    )
                ) + Sum(
                    'available_balance_in_base_currency')
                )['total_balance'] or 0.0

        report = Report.objects.filter(
            user=user,
            created_at__year=month_to_process.year,
            created_at__month=month_to_process.month
        ).last()

        if report:
            report.income_in_current_month = income
            report.expenses_in_current_month = expenses
            report.income_in_current_year = income_year
            report.expenses_in_current_year = expenses_year
            report.total_balance_in_base_currency = total_balance
            report.total_available_balance_in_base_currency = (
                total_available_balance
                )
            report.save()
        else:
            report = Report.objects.create(
                user=user,
                total_balance_in_base_currency=total_balance,
                total_available_balance_in_base_currency=(
                    total_available_balance
                    ),
                income_in_current_month=income,
                expenses_in_current_month=expenses,
                income_in_current_year=income_year,
                expenses_in_current_year=expenses_year
            )
            report.save()
        month_to_process += relativedelta(months=1)


def create_report_for_category_for_user(user_id):

    user = User.objects.get(id=user_id)

    first_payment = Payment.objects.filter(
        user=user_id
        ).order_by('date').first()
    if first_payment:
        first_payment_date = first_payment.date
    else:
        return

    current_month_start = datetime.now().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
        )

    month_to_process = first_payment_date.replace(day=1)

    while month_to_process <= current_month_start.date():

        one_year_start = (
            month_to_process - relativedelta(years=1)
            ).replace(day=1)

        categories = Category.objects.filter(user=user_id)

        for category in categories:
            report_for_category = Report_for_category.objects.filter(
                user=user,
                category=category,
                created_at__year=month_to_process.year,
                created_at__month=month_to_process.month
            ).last()

            if not report_for_category:
                report_for_category = Report_for_category.objects.create(
                    user=user,
                    category=category,
                    changes_in_category_for_current_month=0,
                    average_for_year=0
                )
                report_for_category.save()
            else:
                pass

        report_for_None_category = Report_for_category.objects.filter(
                user=user,
                category=None,
                created_at__year=month_to_process.year,
                created_at__month=month_to_process.month
            ).last()

        if not report_for_None_category:
            report_for_None_category = Report_for_category.objects.create(
                user=user,
                category=None,
                changes_in_category_for_current_month=0,
                average_for_year=0
            )
            report_for_None_category.save()
        else:
            pass

        category_reports = Report_for_category.objects.filter(
                user=user,
                created_at__year=month_to_process.year,
                created_at__month=month_to_process.month
            )

        for category_report in category_reports:
            payments_for_month = Payment.objects.filter(
                include_payment_in_report=True,
                user=user,
                date__gte=month_to_process,
                date__lt=month_to_process + relativedelta(months=1),
                category=category_report.category
            ).exclude(payment_type='transfer')

            payments_for_year = Payment.objects.filter(
                include_payment_in_report=True,
                user=user,
                date__gte=one_year_start,
                date__lt=one_year_start + relativedelta(months=13),
                category=category_report.category
            ).exclude(payment_type='transfer')

            sum_payments = payments_for_month.aggregate(
                total_amount=Sum('amount_in_base_currency')
            )['total_amount'] or 0.0

            average_for_year = payments_for_year.aggregate(
                total_amount=Sum('amount_in_base_currency')
            )['total_amount'] or 0.0

            category_report.changes_in_category_for_current_month = (
                sum_payments
                )
            category_report.average_for_year = average_for_year / 12
            category_report.save()

        month_to_process += relativedelta(months=1)
