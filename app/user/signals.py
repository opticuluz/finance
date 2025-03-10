import logging
from django.utils.timezone import now
from user.models import LoginAttempt
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed
)

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_login(sender, request, user, **kwargs):
    LoginAttempt.objects.create(
        email=user.email,
        ip_address=get_client_ip(request),
        successful=True
    )
    logger.warning(f'✅ Successful login | User: {user.email} | '
                   f'IP: {get_client_ip(request)} | Time: {now()}')


def log_logout(sender, request, user, **kwargs):
    logger.warning(f'🚪 Logout | User: {user.email} | '
                   f'IP: {get_client_ip(request)} | Time: {now()}')


def log_login_failed(sender, credentials, request, **kwargs):
    auth_username = request.POST.get('auth-username', 'Unknown')
    LoginAttempt.objects.create(
        email=auth_username,
        ip_address=get_client_ip(request),
        successful=False
    )
    logger.warning(f'❌ Failed login attempt | email: {auth_username} | '
                   f'IP: {get_client_ip(request)} | Time: {now()}')


user_logged_in.connect(log_login)
user_logged_out.connect(log_logout)
user_login_failed.connect(log_login_failed)
