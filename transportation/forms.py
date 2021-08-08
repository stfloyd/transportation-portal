"""
Transportation Form Definitions

For more information regarding Django forms, see:
    https://docs.djangoproject.com/en/2.2/topics/forms/
"""

from datetime import datetime
from functools import partial
from itertools import groupby
from operator import attrgetter

from django import forms
from django.conf import settings
from django.forms.models import ModelChoiceIterator, ModelChoiceField, ModelMultipleChoiceField
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper

from tempus_dominus.widgets import DatePicker, TimePicker, DateTimePicker

from phone_field.forms import PhoneFormField, PhoneWidget

from transportation import models

from .validators import validate_future


class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __init__(self, field, groupby):
        self.groupby = groupby
        super().__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for group, objs in groupby(queryset, self.groupby):
            yield (group, [self.choice(obj) for obj in objs])


class GroupedModelChoiceField(ModelChoiceField):
    def __init__(self, *args, choices_groupby, **kwargs):
        if isinstance(choices_groupby, str):
            choices_groupby = attrgetter(choices_groupby)
        elif not callable(choices_groupby):
            raise TypeError(
                'choices_groupby must either be a str or a callable accepting a single argument')
        self.iterator = partial(GroupedModelChoiceIterator, groupby=choices_groupby)
        super().__init__(*args, **kwargs)


class GroupedModelMultipleChoiceField(ModelMultipleChoiceField):
    def __init__(self, *args, choices_groupby, **kwargs):
        if isinstance(choices_groupby, str):
            choices_groupby = attrgetter(choices_groupby)
        elif not callable(choices_groupby):
            raise TypeError(
                'choices_groupby must either be a str or a callable accepting a single argument')
        self.iterator = partial(GroupedModelChoiceIterator, groupby=choices_groupby)
        super().__init__(*args, **kwargs)


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = models.Organization
        fields = [
            'name'
        ]


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = models.Department
        fields = [
            'num', 'org', 'name'
        ]


class BudgetForm(forms.ModelForm):
    class Meta:
        model = models.Budget
        fields = [
            'num', 'org', 'name'
        ]


class DriverForm(forms.ModelForm):
    birth_date = forms.DateField(widget=DatePicker(), required=False)
    expiration_date = forms.DateField(required=False)
    phone = PhoneFormField(required=False)

    phone.widget = widget = PhoneWidget(
        phone_attrs={'class': 'form-control'}, ext_attrs={'class': 'form-control', 'style': 'width:70px'}
    )

    class Meta:
        model = models.Driver
        fields = [
            'status',
            'orgs',
            'first_name', 'last_name',
            'birth_date', 'state', 'email', 'phone',
            'license_num', 'expiration_date', 'restrictions', 'has_cdl',
            'notes'
        ]
        widgets = {
            'status': forms.HiddenInput()
        }


class VehicleForm(forms.ModelForm):
    reg_expire_date = forms.DateField(widget=DatePicker())
    purchase_date = forms.DateField(widget=DatePicker())

    class Meta:
        model = models.Vehicle
        fields = [
            'org',
            'status', 'num', 'type',
            'year', 'make', 'model',
            'title_num', 'vin', 'license_plate',
            'reg_expire_date', 'mileage',
            'purchase_date', 'purchase_cost',
            'storage_location', 'notes'
        ]


class VehicleMaintenanceForm(forms.ModelForm):
    vehicle_url_kwarg = 'vehicle_pk'
    vehicle_pk = None
    vehicle = None

    date = forms.DateField(widget=DatePicker())

    def __init__(self, *args, **kwargs):
        self.vehicle_pk = kwargs.pop(self.vehicle_url_kwarg)
        self.vehicle = models.Vehicle.objects.get(pk=self.vehicle_pk)
        super().__init__(*args, **kwargs)

    class Meta:
        model = models.VehicleMaintenance
        fields = [
            'date',
            'category',
            'cost', 'mileage', 'notes'
        ]


class TripRequestForm(forms.ModelForm):
    AGREEMENT = '''
    <p>1. Under no circumstance is any ministry-owned, leased, or rented vehicle to be used for personal use.</p>
    <p>2. Must be an approved driver on our insurance policy.</p>
    <p>3. Must be 21 years of age.</p>
    <p>4. Must have a valid Virginia driver’s license with the proper class and endorsements for the type of vehicle used.</p>
    <p>5. In the event of an accident or a breakdown of the vehicle you are driving, please contact the Security Office at (434) 582-7605 or (434) 582-7641. Please leave your name, the group you are with, your exact location, and the phone number where you can be reached. Security will contact the Transportation employee on call at that time. Furthermore, the driver must go to the Transportation Office to fill out an accident form within 24 hours. Accidents occurring on a weekend must be reported on Monday.</p>
    <p>6. All vehicles, when returned, must have all windows and doors closed.</p>
    <p>7. All vehicles must be clean inside when returned.</p>
    <p>8. Return all keys, this form, and maintenance request form (if necessary) to the Bus Office. Return all vehicles to the same area that you picked them up from unless instructed otherwise.</p>
    <p>9. If you were given a gas card, it must be returned to the office where you received it with all gas receipts.</p>
    '''

    status = forms.ChoiceField(choices=models.TripRequest.STATUS_CHOICES, required=True,
                               initial=models.TripRequest.STATUS_PENDING, widget=forms.HiddenInput())

    manager = forms.ModelChoiceField(
        queryset=models.User.objects.filter(is_moderator=True),
        required=False,
        initial=None,
        widget=forms.HiddenInput()
    )

    contact_phone = PhoneFormField()

    contact_phone.widget = widget = PhoneWidget(
        phone_attrs={'class': 'form-control'}, ext_attrs={'class': 'form-control', 'style': 'width:70px'}
    )

    department = GroupedModelChoiceField(
        queryset=models.Department.objects,
        choices_groupby='org'
    )

    budget = GroupedModelChoiceField(
        queryset=models.Budget.objects,
        choices_groupby='org'
    )

    depart_est = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget(
            attrs={'class': 'input-group'},
            date_attrs={'class': 'datetimepicker form-control datetimepicker-input',
                        'style': 'position:relative!important;', 'data-target': '#id_depart_est_0', 'data-toggle': 'datetimepicker'},
            time_attrs={'class': 'datetimepicker form-control datetimepicker-input', 'style': 'position:relative!important;', 'data-target': '#id_depart_est_1', 'data-toggle': 'datetimepicker'})
    )

    return_est = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget(
            attrs={'class': 'input-group'},
            date_attrs={'class': 'datetimepicker form-control datetimepicker-input',
                        'style': 'position:relative!important;', 'data-target': '#id_return_est_0', 'data-toggle': 'datetimepicker'},
            time_attrs={'class': 'datetimepicker form-control datetimepicker-input', 'style': 'position:relative!important;', 'data-target': '#id_return_est_1', 'data-toggle': 'datetimepicker'})
    )

    requested_driver = forms.CharField(label='Requested Driver', required=False,
                                       help_text='Leave blank or put \'TBA\' if will be available later.')

    trailer = forms.BooleanField(label='Trailer addon', required=False,
                                 help_text='Check if a trailer is required with the vehicle.')

    agreement_accepted = forms.BooleanField(label='Accept', help_text=AGREEMENT)

    purpose = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs.pop('maxlength', None)
        self.fields['purpose'].widget.attrs.update({'class': 'form-control'})
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_labels = False

    class Meta:
        model = models.TripRequest
        fields = [
            'org',
            'status',
            'manager',
            'contact_fn', 'contact_ln', 'contact_phone', 'contact_email',
            'department', 'budget',
            'party_count',
            'destination',
            'vehicle_type',
            'trailer',
            'requested_driver',
            'depart_est', 'return_est', 'mileage_est',
            'purpose',
            'agreement_accepted'
        ]


class TripRequestAdminForm(forms.ModelForm):
    status = forms.ChoiceField(choices=models.TripRequest.STATUS_CHOICES,
                               required=True, widget=forms.HiddenInput())

    manager = forms.ModelChoiceField(
        queryset=models.User.objects.filter(is_moderator=True),
        required=False,
        widget=forms.HiddenInput()
    )

    contact_phone = PhoneFormField()

    contact_phone.widget = widget = PhoneWidget(
        phone_attrs={'class': 'form-control'}, ext_attrs={'class': 'form-control', 'style': 'width:70px'}
    )

    department = GroupedModelChoiceField(
        queryset=models.Department.objects,
        choices_groupby='org'
    )

    budget = GroupedModelChoiceField(
        queryset=models.Budget.objects,
        choices_groupby='org'
    )

    depart_est = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget(
            attrs={'class': 'input-group'},
            date_attrs={'class': 'datetimepicker form-control datetimepicker-input',
                        'style': 'position:relative!important;', 'data-target': '#id_depart_est_0', 'data-toggle': 'datetimepicker'},
            time_attrs={'class': 'datetimepicker form-control datetimepicker-input', 'style': 'position:relative!important;', 'data-target': '#id_depart_est_1', 'data-toggle': 'datetimepicker'})
    )

    return_est = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget(
            attrs={'class': 'input-group'},
            date_attrs={'class': 'datetimepicker form-control datetimepicker-input',
                        'style': 'position:relative!important;', 'data-target': '#id_return_est_0', 'data-toggle': 'datetimepicker'},
            time_attrs={'class': 'datetimepicker form-control datetimepicker-input', 'style': 'position:relative!important;', 'data-target': '#id_return_est_1', 'data-toggle': 'datetimepicker'})
    )

    requested_driver = forms.CharField(label='Requested Driver', required=False,
                                       help_text='Leave blank or put \'TBA\' if will be available later.')

    trailer = forms.BooleanField(label='Trailer addon', required=False,
                                 help_text='Check if a trailer is required with the vehicle.')

    depart_act = forms.SplitDateTimeField(
        required=False,
        widget=forms.SplitDateTimeWidget(
            attrs={'class': 'input-group'},
            date_attrs={'class': 'datetimepicker form-control datetimepicker-input',
                        'style': 'position:relative!important;', 'data-target': '#id_depart_act_0', 'data-toggle': 'datetimepicker'},
            time_attrs={'class': 'datetimepicker form-control datetimepicker-input', 'style': 'position:relative!important;', 'data-target': '#id_depart_act_1', 'data-toggle': 'datetimepicker'})
    )

    return_act = forms.SplitDateTimeField(
        required=False,
        widget=forms.SplitDateTimeWidget(
            attrs={'class': 'input-group'},
            date_attrs={'class': 'datetimepicker form-control datetimepicker-input',
                        'style': 'position:relative!important;', 'data-target': '#id_return_act_0', 'data-toggle': 'datetimepicker'},
            time_attrs={'class': 'datetimepicker form-control datetimepicker-input', 'style': 'position:relative!important;', 'data-target': '#id_return_act_1', 'data-toggle': 'datetimepicker'})
    )

    signed_off = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={'class': 'datetimepicker form-control datetimepicker-input',
                   'style': 'position:relative!important;', 'data-target': '#id_signed_off', 'data-toggle': 'datetimepicker'}
        )
    )

    purpose = forms.CharField(
        required=False,
        widget=forms.Textarea
    )

    vehicle_problems = forms.CharField(
        widget=forms.Textarea,
        required=False
    )

    card_num = forms.CharField(
        required=False
    )

    agreement_accepted = forms.BooleanField(label='Accept', help_text=TripRequestForm.AGREEMENT)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            #visible.field.widget.attrs['class'] = 'form-control form-control-sm'
            visible.field.widget.attrs.pop('maxlength', None)
        self.fields['purpose'].widget.attrs.update({'class': 'form-control'})
        self.fields['is_vehicle_clean'].widget.attrs.update({'class': 'largerCheckbox'})
        self.fields['is_vehicle_parked_proper'].widget.attrs.update({'class': 'largerCheckbox'})
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_show_labels = False

    class Meta:
        model = models.TripRequest
        fields = [
            'org',
            'status',
            'contact_fn', 'contact_ln', 'contact_phone', 'contact_email',
            'department', 'budget',
            'party_count',
            'destination',
            'vehicle_type',
            'trailer',
            'requested_driver',
            'driver', 'vehicle',
            'depart_est', 'return_est', 'mileage_est',
            'depart_act', 'return_act', 'mileage_act',
            'card_num', 'key_color', 'fuel_cost',
            'manager', 'signed_off',
            'purpose',
            'agreement_accepted',
            'is_vehicle_clean', 'is_vehicle_parked_proper',
            'vehicle_problems'
        ]
