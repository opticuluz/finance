from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from report.models import Report


class ReportAdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='testpass123',
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='testpass123',
            name='Test User'
        )
        self.report = Report.objects.create(
            created_at='2023-07-20 16:24:45.13242+00',
            user=self.user,
            income_in_current_month='2020.00',
            expenses_in_current_month='1548.27',
            total_balance_in_base_currency='-4674.43',
            total_available_balance_in_base_currency='2857.64'
        )

    def test_report_list(self):
        url = reverse('admin:report_report_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.report.user)
        self.assertContains(res, self.report.income_in_current_month)
        self.assertContains(res, self.report.expenses_in_current_month)
        self.assertContains(res, self.report.total_balance_in_base_currency)
        self.assertContains(
            res,
            self.report.total_available_balance_in_base_currency
            )

    def test_edit_report_page(self):
        url = reverse('admin:report_report_change', args=[self.report.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_report_page(self):
        url = reverse('admin:payment_payment_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
