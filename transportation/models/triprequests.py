from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from phone_field import PhoneField

from transportation import validators


class TripRequest(models.Model):
    STATUS_NONE = 0
    STATUS_PENDING = 1
    STATUS_APPROVED = 2
    STATUS_DENIED = 3
    STATUS_COMPLETED = 4
    STATUS_CANCELLED = 5
    STATUS_OTHER = 6
    STATUS_RETURNED = 7
    STATUS_CHOICES = (
        (STATUS_NONE,           'None'),
        (STATUS_PENDING,        'Pending'),
        (STATUS_APPROVED,       'Approved'),
        (STATUS_DENIED,         'Denied'),
        (STATUS_COMPLETED,      'Completed'),
        (STATUS_CANCELLED,      'Cancelled'),
        (STATUS_OTHER,          'Other'),
        (STATUS_RETURNED,       'Returned'),
    )

    TYPE_UNKNOWN = 0
    TYPE_CAR = 1
    TYPE_PVAN = 2
    TYPE_CVAN = 3
    TYPE_BUS = 4
    TYPE_CBUS = 5
    TYPE_RBUS = 6
    TYPE_TRUCK = 7
    TYPE_NOCDL_BUS = 8
    TYPE_GOLFCART = 9
    TYPE_CHOICES = (
        (TYPE_UNKNOWN,   'Unknown'),
        (TYPE_CAR,       'Car'),
        (TYPE_PVAN,      'Passenger Van'),
        (TYPE_CVAN,      'Cargo Van'),
        (TYPE_BUS,       'Bus'),
        (TYPE_CBUS,      'Coach Bus'),
        (TYPE_RBUS,      'Road Bus'),
        (TYPE_TRUCK,     'Truck'),
        (TYPE_NOCDL_BUS, 'Non-CDL Bus'),
        (TYPE_GOLFCART,  'Golf Cart')
    )

    KEY_NONE = 0
    KEY_RED = 1
    KEY_BLUE = 2
    KEY_GREEN = 3
    KEY_YELLOW = 4
    KEY_WHITE = 5
    KEY_CHOICES = (
        (KEY_NONE,   'None'),
        (KEY_RED,    'Red'),
        (KEY_BLUE,   'Blue'),
        (KEY_GREEN,  'Green'),
        (KEY_YELLOW, 'Yellow'),
        (KEY_WHITE,  'White')
    )

    id = models.AutoField(primary_key=True)

    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Status'
    )

    org = models.ForeignKey(
        'Organization',
        on_delete=models.PROTECT,
        verbose_name='Organization'
    )

    submitted = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Submitted'
    )

    updated = models.DateTimeField(auto_now=True, verbose_name='Updated')

    manager = models.ForeignKey(
        get_user_model(),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='manager',
        verbose_name='Manager'
    )

    signed_off = models.DateField(
        null=True, blank=True,
        verbose_name='Signed Off On'
    )

    requestor = models.ForeignKey(
        get_user_model(),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='requestor',
        verbose_name='Requestor'
    )

    contact_fn = models.CharField(
        max_length=32,
        verbose_name='First Name'
    )

    contact_ln = models.CharField(
        max_length=32,
        verbose_name='Last Name'
    )

    contact_phone = PhoneField(
        verbose_name='Phone #'
    )

    contact_email = models.EmailField(
        verbose_name='Email Address'
    )

    department = models.ForeignKey(
        'Department',
        on_delete=models.PROTECT,
        verbose_name='Department'
    )

    budget = models.ForeignKey(
        'Budget',
        on_delete=models.PROTECT,
        verbose_name='Budget'
    )

    requested_driver = models.CharField(
        max_length=255,
        null=True, blank=True
    )

    driver = models.ForeignKey(
        'Driver',
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='trips',
        verbose_name='Driver'
    )

    vehicle_type = models.PositiveSmallIntegerField(
        default=TYPE_UNKNOWN,
        choices=TYPE_CHOICES,
        verbose_name='Vehicle Type'
    )

    vehicle = models.ForeignKey(
        'Vehicle',
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='trips',
        verbose_name='Vehicle'
    )

    party_count = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Party Count'
    )

    depart_est = models.DateTimeField(
        verbose_name='Depart Time (Estimate)'
    )

    return_est = models.DateTimeField(
        verbose_name='Return Time (Estimate)'
    )

    depart_act = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Depart Time (Actual)'
    )

    return_act = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Return Time (Actual)'
    )

    destination = models.CharField(
        max_length=255,
        verbose_name='Destination'
    )

    purpose = models.TextField(
        verbose_name='Purpose'
    )

    trailer = models.BooleanField(
        default=False,
        verbose_name='Trailer'
    )

    agreement_accepted = models.BooleanField(
        default=False,
        verbose_name='Accept Agreement'
    )

    mileage_est = models.PositiveIntegerField(
        verbose_name='Mileage (Estimate)'
    )

    mileage_act = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Mileage (Actual)'
    )

    card_num = models.CharField(
        null=True, blank=True,
        max_length=32,
        verbose_name='Card #'
    )

    key_color = models.PositiveSmallIntegerField(
        verbose_name='Key Tag Color',
        choices=KEY_CHOICES,
        default=KEY_NONE
    )

    fuel_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        null=True, blank=True,
        verbose_name='Fuel Cost'
    )

    is_vehicle_clean = models.BooleanField(
        default=False,
        verbose_name='Vehicle Cleanliness'
    )

    is_vehicle_parked_proper = models.BooleanField(
        default=False,
        verbose_name='Vehicle Parked Correctly'
    )

    vehicle_problems = models.CharField(
        max_length=256,
        null=True, blank=True
    )

    @property
    def is_modifiable(self):
        return self.status != 3 and self.status != 4 and self.status != 5

    @property
    def last_updator(self):
        last_activity = TripRequestActivity.objects.filter(request=self).latest()
        return last_activity.user

    @property
    def fuel_cost_display(self):
        return f'${self.fuel_cost}'

    @property
    def org_department(self):
        return f'{self.org} - {self.department}'

    @property
    def title(self):
        return f"{self.requestor_fullname}'s Trip Request"

    @property
    def daterange(self):
        return f"{self.depart_est.strftime('%b %d, %Y')} - {self.return_est.strftime('%b %d, %Y')}"

    @property
    def manager_fullname(self):
        if self.manager is None:
            return f'{self.manager}'
        return f'{self.manager.first_name} {self.manager.last_name}'

    @property
    def requestor_fullname(self):
        if self.requestor is None:
            return f'{self.contact_fullname}'
        return f"{self.requestor.first_name} {self.requestor.last_name}"

    @property
    def driver_fullname(self):
        if self.driver is None:
            return None
        return f'{self.driver.first_name} {self.driver.last_name}'

    @property
    def contact_fullname(self):
        return f'{self.contact_fn} {self.contact_ln}'

    @property
    def is_pending(self):
        return self.status == TripRequest.STATUS_PENDING

    @property
    def is_approved(self):
        return self.status == TripRequest.STATUS_APPROVED

    @property
    def is_denied(self):
        return self.status == TripRequest.STATUS_DENIED

    @property
    def is_completed(self):
        return self.status == TripRequest.STATUS_COMPLETED

    @property
    def is_cancelled(self):
        return self.status == TripRequest.STATUS_CANCELLED

    @property
    def is_returned(self):
        return self.status == TripRequest.STATUS_RETURNED

    @property
    def is_valid(self):
        return self.manager is not None and \
            self.driver is not None and \
            self.vehicle is not None and \
            self.card_num is not None
        # not self.is_departure_estimate_late and
        # not self.is_return_estimate_late and

    @property
    def is_departure_estimate_late(self):
        if self.is_pending:
            return self.depart_est < timezone.now()
        else:
            return False

    @property
    def is_return_estimate_late(self):
        if self.is_pending:
            return self.return_est < timezone.now()
        else:
            return False

    @property
    def can_finalize(self):
        return self.is_returned  # self.depart_act is not None and self.return_act is not None and self.is_returned

    @property
    def can_return(self):
        return True  # self.depart_act is not None and self.return_act is not None

    @property
    def is_missing_requirements(self):
        return self.manager is None or self.vehicle is None or self.driver is None or self.card_num is None or self.key_color is None

    @property
    def vehicle_type_display(self):
        return self.TYPE_CHOICES[self.vehicle_type][1]

    @property
    def missing_requirements(self):
        missing_str = ''

        if self.manager is None:
            missing_str += 'manager'

        if self.vehicle is None:
            if missing_str != '':
                missing_str += ', '
            missing_str += 'vehicle'

        if self.driver is None:
            if missing_str != '':
                missing_str += ', '
            missing_str += 'driver'

        if self.key_color is None:
            if missing_str != '':
                missing_str += ', '
            missing_str += 'key-tag color'

        if self.card_num is None:
            if missing_str != '':
                missing_str += ', '
            missing_str += 'card #'

        if self.status == 7 or self.status == 2:
            if self.mileage_act is None:
                if missing_str != '':
                    missing_str += ', '
                missing_str += 'actual mileage'

        return f'Missing requirements: {missing_str}'

    def __str__(self):
        return f"{self.requestor_fullname}'s request between {self.daterange}"

    def get_absolute_url(self):
        return reverse('request-detail', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)

        activity = TripRequestActivity()
        activity.type = TripRequestActivity.TYPE_CREATED if self.pk is None else TripRequestActivity.TYPE_EDITED
        activity.user = user

        if self.pk is None:
            # Make sure we don't try to create any request with a status other than pending.
            if activity.user is None:
                activity.user = self.requestor
            try:
                validators.validate_triprequest_status(self, TripRequest.STATUS_PENDING)
            except ValidationError as ve:
                raise ValidationError(
                    _(f'Unable to create new request with status != {TripRequest.STATUS_PENDING}'),
                    params={'raised': ve, 'triprequest': self}
                )

        super().save(*args, **kwargs)
        activity.request = self
        activity.save()

    def assign_moderator(self, commit=False, *args, **kwargs):
        self.manager = kwargs.get('user', None)
        if commit and self.manager is not None:
            self.save()
        else:
            raise ValidationError(_(f'Manager already assigned'))

    def approve(self, commit=False, *args, **kwargs):
        if self.vehicle is not None and self.driver is not None:
            self.status = TripRequest.STATUS_APPROVED
            if commit:
                self.save()
                user = kwargs.pop('user', None)
                real_user = user is not None
                activity = TripRequestActivity()
                activity.user = user
                activity.request = self
                activity.type = TripRequestActivity.TYPE_APPROVED
                activity.save()
        else:
            raise ValidationError(_(f'Must meet requirements'))

    def deny(self, commit=False, *args, **kwargs):
        self.status = TripRequest.STATUS_DENIED
        if commit:
            self.save()
            user = kwargs.pop('user', None)
            real_user = user is not None
            activity = TripRequestActivity()
            activity.user = user
            activity.request = self
            activity.type = TripRequestActivity.TYPE_DENIED
            activity.save()

    def return_vehicle(self, commit=False, *args, **kwargs):
        if self.vehicle is not None and self.driver is not None:
            self.status = TripRequest.STATUS_RETURNED
            if commit:
                self.save()
                user = kwargs.pop('user', None)
                real_user = user is not None
                activity = TripRequestActivity()
                activity.user = user
                activity.request = self
                activity.type = TripRequestActivity.TYPE_FINISHED
                activity.save()
        else:
            raise ValidationError(_(f'Must meet requirements'))

    def finalize(self, commit=False, *args, **kwargs):
        if self.vehicle is not None and self.driver is not None:
            self.status = TripRequest.STATUS_COMPLETED
            if commit:
                self.save()
                user = kwargs.pop('user', None)
                real_user = user is not None
                activity = TripRequestActivity()
                activity.user = user
                activity.request = self
                activity.type = TripRequestActivity.TYPE_FINISHED
                activity.save()
        else:
            raise ValidationError(_(f'Must meet requirements'))

    def cancel(self, commit=False, *args, **kwargs):
        self.status = TripRequest.STATUS_CANCELLED
        if commit:
            self.save()
            user = kwargs.pop('user', None)
            real_user = user is not None
            activity = TripRequestActivity()
            activity.user = user
            activity.request = self
            activity.type = TripRequestActivity.TYPE_CANCELLED
            activity.save()

    class Meta:
        get_latest_by = 'updated'
        ordering = ['updated']


class TripRequestActivity(models.Model):
    TYPE_CREATED = 0
    TYPE_EDITED = 1
    TYPE_DELETED = 2
    TYPE_PENDING = 3
    TYPE_APPROVED = 4
    TYPE_DENIED = 5
    TYPE_FINISHED = 6
    TYPE_CANCELLED = 7
    TYPE_ARCHIVED = 8
    TYPE_CHOICES = (
        (TYPE_CREATED, 'Created'),
        (TYPE_EDITED, 'Editted'),
        (TYPE_DELETED, 'Deleted'),
        (TYPE_PENDING, 'Pending'),
        (TYPE_APPROVED, 'Approved'),
        (TYPE_DENIED, 'Denied'),
        (TYPE_FINISHED, 'Finished'),
        (TYPE_CANCELLED, 'Cancelled'),
        (TYPE_ARCHIVED, 'Archived')
    )

    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(get_user_model(),
                             null=True,
                             on_delete=models.PROTECT
                             )

    timestamp = models.DateTimeField(auto_now=True)

    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES)

    request = models.ForeignKey(
        TripRequest,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='Trip Request'
    )

    class Meta:
        get_latest_by = 'timestamp'
