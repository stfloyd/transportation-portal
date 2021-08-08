from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from phone_field import PhoneField

from .managers import (
    DriverManager
)


class User(AbstractUser):
    is_moderator = models.BooleanField(
        'moderator status',
        default=False,
        help_text='Designates whether the user can moderate the requests, vehicles & drivers.'
    )

    is_driver = models.BooleanField(
        'driver status',
        default=False,
        help_text='Designates whether the user is a driver.'
    )

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_created_requests(self, future_only=False):
        from .triprequests import TripRequest
        queryset = TripRequest.objects.filter(requestor=self)
        if future_only:
            return queryset.filter(submitted__gte=timezone.now())
        return queryset

    def get_managed_requests(self, future_only=False):
        from .triprequests import TripRequest
        queryset = TripRequest.objects.filter(manager=self)
        if future_only:
            return queryset.filter(submitted__gte=timezone.now())
        return queryset

    class Meta:
        db_table = 'auth_user'


class Driver(models.Model):
    STATUS_NONE = 0
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_RETIRED = 3
    STATUS_CHOICES = (
        (STATUS_NONE,       'None'),
        (STATUS_ACTIVE,     'Active'),
        (STATUS_INACTIVE,   'Inactive'),
        (STATUS_RETIRED,    'Retired')
    )

    objects = DriverManager()

    id = models.AutoField(primary_key=True)

    status = models.PositiveSmallIntegerField(
        default=STATUS_ACTIVE,
        choices=STATUS_CHOICES,
        verbose_name='Status'
    )

    orgs = models.ManyToManyField(
        'Organization',
        verbose_name='Organizations'
    )

    first_name = models.CharField(
        max_length=32,
        verbose_name='First Name'
    )

    last_name = models.CharField(
        max_length=32,
        verbose_name='Last Name'
    )

    license_num = models.CharField(
        max_length=10,
        verbose_name='License #',
        null=True, blank=True
    )

    expiration_date = models.DateField(
        verbose_name='License Expiration Date',
        null=True, blank=True
    )

    birth_date = models.DateField(
        verbose_name='Date of Birth',
        null=True, blank=True
    )

    state = models.CharField(
        max_length=2,
        verbose_name='State',
        null=True, blank=True
    )

    phone = PhoneField(
        blank=True, null=True,
        verbose_name='Phone #'
    )

    email = models.EmailField(
        blank=True, null=True,
        verbose_name='Email Address'
    )

    restrictions = models.CharField(
        null=True, blank=True,
        max_length=30,
        verbose_name='License Restrictions'
    )

    has_cdl = models.BooleanField(
        default=False,
        verbose_name='CDL Status'
    )

    notes = models.TextField(blank=True)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @full_name.setter
    def full_name(self, val):
        split_val = val.split(' ')
        if len(split_val) == 2:
            self.first_name = split_val[0]
            self.last_name = split_val[1]

    def __str__(self):
        return self.full_name

    def is_available(self, start, end):
        queryset = self.get_assigned_trips(future_only=True)
        range_count = queryset.filter(depart_est__gte=start, return_est__lte=end).count()
        return range_count == 0

    @property
    def has_future_trips(self):
        return self.get_assigned_trips(future_only=True).count() != 0

    def get_pending_trips(self):
        from .triprequests import TripRequest
        queryset = self.get_assigned_trips()
        return queryset.filter(status=TripRequest.STATUS_PENDING)

    def get_completed_trips(self):
        from .triprequests import TripRequest
        queryset = self.get_assigned_trips()
        return queryset.filter(status=TripRequest.STATUS_COMPLETED)

    def get_assigned_trips(self, future_only=False):
        from .triprequests import TripRequest
        queryset = TripRequest.objects.filter(driver=self)
        if future_only:
            return queryset.filter(depart_est__gte=timezone.now())
        return queryset
