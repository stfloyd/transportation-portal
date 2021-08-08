from django import forms

import django_filters

from transportation import models


class OrganizationFilter(django_filters.FilterSet):
    class Meta:
        model = models.Organization
        fields = ['name']


class DriverFilter(django_filters.FilterSet):
    class Meta:
        model = models.Driver
        fields = ['first_name', 'last_name', 'status', 'has_cdl']


class VehicleFilter(django_filters.FilterSet):
    class Meta:
        model = models.Vehicle
        fields = ['org', 'status', 'year', 'make', 'model', 'type']


class VehicleMaintenanceFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(choices=models.VehicleMaintenance.CATEGORY_CHOICES)

    class Meta:
        model = models.VehicleMaintenance
        fields = ['category']


class TripRequestFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=(
        (models.TripRequest.STATUS_PENDING,        'Pending'),
        (models.TripRequest.STATUS_APPROVED,       'Approved'),
        (models.TripRequest.STATUS_DENIED,         'Denied'),
        (models.TripRequest.STATUS_RETURNED,       'Returned'),
        (models.TripRequest.STATUS_COMPLETED,      'Completed'),
        (models.TripRequest.STATUS_CANCELLED,      'Cancelled'),
    ))
    start = django_filters.DateTimeFilter(
        field_name='depart_est', label='Start', lookup_expr='date__gte')
    end = django_filters.DateTimeFilter(
        field_name='depart_est', label='End', lookup_expr='date__lte')
    fn = django_filters.CharFilter(field_name='contact_fn',
                                   label='First Name', lookup_expr='icontains')
    ln = django_filters.CharFilter(field_name='contact_ln',
                                   label='Last Name', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='contact_email',
                                      label='Email Address', lookup_expr='icontains')
    deptname = django_filters.CharFilter(
        field_name='department', label='Department Name', lookup_expr='name__icontains')
    deptnum = django_filters.NumberFilter(
        field_name='department', label='Department #', lookup_expr='num')
    budgetname = django_filters.CharFilter(
        field_name='budget', label='Budget Name', lookup_expr='name__icontains')
    budgetnum = django_filters.NumberFilter(
        field_name='budget', label='Budget #', lookup_expr='num')

    @property
    def qs(self):
        queryset = super().qs
        if self.request.user.is_staff or self.request.user.is_moderator:
            return queryset
        return queryset.filter(requestor=self.request.user)

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['id'].field.widget.attrs.update(
            {'class': 'form-control input-sm', 'type': 'text'})
        self.filters['status'].field.widget.attrs.update({'class': 'form-control'})
        self.filters['start'].field.widget.attrs.update(
            {'class': 'datetimepicker form-control datetimepicker-input text-center', 'data-toggle': 'datetimepicker', 'data-target': '#id_start'})
        self.filters['end'].field.widget.attrs.update(
            {'class': 'datetimepicker form-control datetimepicker-input text-center', 'data-toggle': 'datetimepicker', 'data-target': '#id_end'})

    class Meta:
        model = models.TripRequest
        fields = ['id', 'status', 'org', 'start', 'end', 'fn', 'ln',
                  'email', 'deptname', 'deptnum', 'budgetname', 'budgetnum']
