"""finance URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.urls import path, include
from two_factor.urls import urlpatterns as tf_urls
from payment.autocomplete import TagAutocomplete
from django.views.generic.base import TemplateView


def is_admin(user):
    return user.is_staff


urlpatterns = [
    path('', include(tf_urls)),
    path('system-dashboard/', admin.site.urls),
    path('tag-autocomplete/',
         user_passes_test(is_admin)(TagAutocomplete.as_view()),
         name='tag-autocomplete'
         ),
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="robots.txt",
            content_type="text/plain"
        ),
    ),
]
