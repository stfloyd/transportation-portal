from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class Vehicle(models.Model):
    STATUS_NONE = 0
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_RETIRED = 3
    STATUS_GIFTED = 4
    STATUS_SOLD = 5
    STATUS_OTHER = 6
    STATUS_CHOICES = (
        (STATUS_NONE,       'None'),
        (STATUS_ACTIVE,     'Active'),
        (STATUS_INACTIVE,   'Inactive'),
        (STATUS_RETIRED,    'Retired'),
        (STATUS_GIFTED,     'Gifted'),
        (STATUS_SOLD,       'Sold'),
        (STATUS_OTHER,      'Other')
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

    id = models.AutoField(primary_key=True)

    org = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name='Organization'
    )

    num = models.PositiveIntegerField(
        verbose_name='Vehicle #'
    )

    type = models.PositiveSmallIntegerField(
        default=TYPE_UNKNOWN,
        choices=TYPE_CHOICES,
        verbose_name='Vehicle Type'
    )

    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES,
        verbose_name='Status'
    )

    year = models.PositiveSmallIntegerField(
        verbose_name='Year'
    )

    make = models.CharField(
        max_length=30,
        verbose_name='Make'
    )

    model = models.CharField(
        max_length=30,
        verbose_name='Model'
    )

    title_num = models.CharField(
        max_length=30,
        verbose_name='Title #'
    )

    vin = models.CharField(
        max_length=40,
        verbose_name='VIN #'
    )

    license_plate = models.CharField(
        max_length=10,
        verbose_name='Plate #'
    )

    reg_expire_date = models.DateField(
        verbose_name='Registration'
    )

    mileage = models.PositiveIntegerField(
        default=0,
        verbose_name='Mileage'
    )

    purchase_date = models.DateField(
        null=True, blank=True,
        verbose_name='Purchase Date'
    )

    purchase_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        null=True, blank=True,
        verbose_name='Purchase Price'
    )

    storage_location = models.CharField(
        max_length=128,
        null=True, blank=True,
        verbose_name='Storage Location'
    )

    notes = models.TextField(blank=True)

    @property
    def fullname(self):
        return f'{self.year} {self.make} {self.model}'

    def __str__(self):
        return f'#{self.num} - {self.fullname}'

    def save(self, *args, **kwargs):
        created = self.pk is None
        user = kwargs.pop('user', None)
        super().save(*args, **kwargs)
        activity = VehicleActivity()
        activity.user = user
        activity.vehicle = self
        if created:
            activity.type = VehicleActivity.TYPE_CREATED
        else:
            activity.type = VehicleActivity.TYPE_EDITED
        activity.save()

    def get_assigned_trips(self, future_only=False):
        from .triprequests import TripRequest
        queryset = TripRequest.objects.filter(driver=self)
        if future_only:
            return queryset.filter(submitted__gte=timezone.now())
        return queryset

    def get_assigned_drivers(self, future_only=False):
        from .triprequests import TripRequest
        queryset = TripRequest.objects.filter(vehicle=self)
        if future_only:
            return queryset.filter(submitted__gte=timezone.now()).values('driver')
        return queryset.values('driver')

    class Meta:
        ordering = ['num']


class VehicleActivity(models.Model):
    TYPE_CREATED = 0
    TYPE_EDITED = 1
    TYPE_DELETED = 2
    TYPE_CREATED_MAINTENANCE = 3
    TYPE_EDITED_MAINTENANCE = 4
    TYPE_DELETED_MAINTENANCE = 5
    TYPE_CHOICES = (
        (TYPE_CREATED, 'Created'),
        (TYPE_EDITED, 'Editted'),
        (TYPE_DELETED, 'Deleted'),
        (TYPE_CREATED_MAINTENANCE, 'Created Maintenance'),
        (TYPE_EDITED_MAINTENANCE, 'Editted Maintenance'),
        (TYPE_DELETED_MAINTENANCE, 'Deleted Maintenance')
    )

    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(get_user_model(),
                             null=True,
                             on_delete=models.PROTECT
                             )

    timestamp = models.DateTimeField(auto_now=True)

    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES)

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='Vehicle'
    )


class VehicleMaintenance(models.Model):
    CATEGORY_UNKNOWN = 0
    CATEGORY_GENERAL = 1
    CATEGORY_ENGINE = 2
    CATEGORY_BODY = 3
    CATEGORY_ELECTRICAL = 4
    CATEGORY_INSPECTION = 5
    CATEGORY_OTHER = 6
    CATEGORY_CHOICES = (
        (CATEGORY_UNKNOWN,      'Unknown'),
        (CATEGORY_GENERAL,      'General'),
        (CATEGORY_ENGINE,       'Engine'),
        (CATEGORY_BODY,         'Body'),
        (CATEGORY_ELECTRICAL,   'Electrical'),
        (CATEGORY_INSPECTION,   'Inspection'),
        (CATEGORY_OTHER,        'Other'),
    )

    id = models.AutoField(primary_key=True)

    date = models.DateField(
        verbose_name='Maintenance Date'
    )

    category = models.IntegerField(
        choices=CATEGORY_CHOICES,
        default=CATEGORY_UNKNOWN,
        verbose_name='Category'
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        verbose_name='Vehicle',
        related_name='maintenances'
    )

    cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name='Cost'
    )

    mileage = models.PositiveIntegerField(
        verbose_name='Mileage'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='Notes'
    )

    def save(self, *args, **kwargs):
        created = self.pk is None
        user = kwargs.pop('user', None)
        real_user = user is not None
        super().save(*args, **kwargs)
        activity = VehicleActivity()
        activity.user = user
        activity.vehicle = self.vehicle
        if created:
            activity.type = VehicleActivity.TYPE_CREATED_MAINTENANCE
        else:
            activity.type = VehicleActivity.TYPE_EDITED_MAINTENANCE
        activity.save()

        if self.mileage > self.vehicle.mileage:
            self.vehicle.mileage = self.mileage
            self.vehicle.save()
