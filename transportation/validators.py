import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def validate_triprequest_status(triprequest, status):
    if not isinstance(status, int):
        raise ValidationError(
            _(f'{type(status)} is not a {type(int)} object'),
            params={'triprequest': triprequest, 'status': status}
        )
    if triprequest.status != status:
        raise ValidationError(
            _(f'{triprequest.status} does not equal {status}'),
            params={'triprequest': triprequest, 'status': status}
        )


def validate_past(value):
    is_date = isinstance(value, datetime.date)
    is_datetime = isinstance(value, datetime.datetime)
    if not is_date or not is_datetime:
        raise ValidationError(
            _(f'{type(value)} is not a {type(datetime.date)} or {type(datetime.datetime)} object'),
            params={'value': value}
        )
    try:
        is_past = value > timezone.now().date()
    except TypeError:
        is_past = value.date() > timezone.now().date()
    if is_past:
        raise ValidationError(
            _(f'Date cannot be in the future'),
            params={'value': value}
        )


def validate_future(value):
    is_date = isinstance(value, datetime.date)
    is_datetime = isinstance(value, datetime.datetime)
    if not is_date or not is_datetime:
        raise ValidationError(
            _(f'{type(value)} is not a {type(datetime.date)} or {type(datetime.datetime)} object'),
            params={'value': value}
        )
    try:
        is_past = value < timezone.now().date()
    except TypeError:
        is_past = value.date() < timezone.now().date()
    if is_past:
        raise ValidationError(
            _(f'Date cannot be in the past'),
            params={'value': value}
        )
