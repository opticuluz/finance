from finance.celery import app
from datetime import datetime
from django.db.models import Sum, Q, Case, When, Value
from django.db import models
from report.models import Report, Report_for_category
from account.models import Account
from payment.models import Payment
from category.models import Category
from user.models import User
from django.db import transaction
from dateutil.relativedelta import relativedelta


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

    first_payment_date = Payment.objects.filter(
        user=user_id
    ).order_by('date').first().date

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
            if month_to_process == current_month_start.date():
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

    first_payment_date = Payment.objects.filter(
        user=user_id
    ).order_by('date').first().date

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

        payments = Payment.objects.filter(
            include_payment_in_report=True,
            user=user_id,
            date__gte=month_to_process,
            date__lt=month_to_process + relativedelta(months=1)
            ).exclude(payment_type='transfer')

        # if not payments:
        #     report_for_category = Report_for_category.objects.filter(
        #         user=user,
        #         created_at__year=current_month_start.year,
        #         created_at__month=current_month_start.month
        #     ).last()

        #     if report_for_category:
        #         report_for_category.changes_in_category_for_current_month = 0
        #         payments_for_year = Payment.objects.filter(
        #             include_payment_in_report=True,
        #             user=user_id,
        #             date__gte=one_year_start,
        #             category_id=category_id
        #         ).exclude(payment_type='transfer')
        #         sum_payments = payments_for_year.aggregate(
        #             total_amount=Sum('amount_in_base_currency')
        #         )['total_amount'] or 0.0
        #         report_for_category.save()
        #     else:
        #         return

        categories_report = payments.values('category').annotate(
            total_amount=Sum('amount_in_base_currency')
        )

        for category_report in categories_report:
            category_id = category_report['category']
            total_amount = category_report['total_amount']

            if category_id is not None:
                category = Category.objects.get(id=category_id)
                payments_for_year = Payment.objects.filter(
                    include_payment_in_report=True,
                    user=user_id,
                    date__gte=one_year_start,
                    date__lt=one_year_start + relativedelta(months=13),
                    category_id=category_id
                ).exclude(payment_type='transfer')
                sum_payments = payments_for_year.aggregate(
                    total_amount=Sum('amount_in_base_currency')
                )['total_amount'] or 0.0
            else:
                category = None
                payments_for_year = Payment.objects.filter(
                    include_payment_in_report=True,
                    user=user_id,
                    date__gte=one_year_start,
                    date__lt=one_year_start + relativedelta(months=13),
                    category_id=None
                ).exclude(payment_type='transfer')
                sum_payments = payments_for_year.aggregate(
                    total_amount=Sum('amount_in_base_currency')
                )['total_amount'] or 0.0
            report_for_category = Report_for_category.objects.filter(
                user=user,
                category=category,
                created_at__year=month_to_process.year,
                created_at__month=month_to_process.month
            ).last()

            if report_for_category:
                report_for_category.changes_in_category_for_current_month \
                    = total_amount
                report_for_category.average_for_year = sum_payments / 12
                report_for_category.save()
            else:
                report_for_category = Report_for_category.objects.create(
                    user=user,
                    category=category,
                    changes_in_category_for_current_month=total_amount,
                    average_for_year=sum_payments / 12
                )
                report_for_category.save()
        month_to_process += relativedelta(months=1)
