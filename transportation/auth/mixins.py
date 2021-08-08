from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseRedirect


class DriverRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and self.request.user.is_driver:
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class ModeratorRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        proper_permissions = self.request.user.is_moderator or self.request.user.is_superuser
        if self.request.user.is_authenticated and proper_permissions:
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class SuperuserRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


def driver_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.is_driver or u.is_moderator or u.is_superuser),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def moderator_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.is_moderator or u.is_superuser),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def superuser_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
