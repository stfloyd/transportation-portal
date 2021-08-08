"""
Transportation Table Definitions

For more information regarding django-tables2, see:
    https://pypi.org/project/django-tables2/
"""

# region Module Imports

# Django
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.humanize.templatetags.humanize import intcomma

# Django Tables

from django_tables2 import (
    Column, Table,
    TemplateColumn, DateColumn,
    CheckBoxColumn, BooleanColumn,
    LinkColumn
)
from django_tables2.utils import A
from django_tables2.tables import Table

# Project
from .models import (
    Organization, Department, Budget,
    Driver, Vehicle, TripRequest, VehicleMaintenance
)

# endregion Module Imports


class SummingColumn(Column):
    """ Column for summing up all values in a bound column """

    def render_footer(self, bound_column, table):
        """Render a summation footer for table

        Arguments:
            bound_column {django_tables2.Column} -- The column to display the footer value for
            table {django_tables2.Table} -- The table in context
        """
        return sum(bound_column.accessor.resolve(row) for row in table.data)


class OrganizationTable(Table):
    orderable = False

    detail_template = '<button id="org-edit-{{ record.pk }}" type="button" data-org-id="{{ record.pk }}" class="button-org-detail btn btn-info btn-sm">View</button>'
    checkbox_template = '<input class="largerCheckbox" type="checkbox">'

    check = TemplateColumn(checkbox_template, accessor='id', attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')
    name = LinkColumn('org-detail', args=[A('pk')])
    detail = TemplateColumn(detail_template, attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')

    class Meta:
        model = Organization
        fields = ('check', 'detail', 'name')
        attrs = {'class': 'table table-striped table-bordered'}
        row_attrs = {"data-id": lambda record: record.pk}


class DepartmentsTable(Table):
    orderable = False

    checkbox_template = '<input class="largerCheckbox" type="checkbox">'

    check = TemplateColumn(checkbox_template, accessor='id', attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')

    class Meta:
        model = Department
        fields = ('check', 'num', 'name')
        attrs = {'class': 'table table-striped table-bordered'}
        row_attrs = {"data-id": lambda record: record.pk}


class BudgetsTable(Table):
    orderable = False

    checkbox_template = '<input class="largerCheckbox" type="checkbox">'

    check = TemplateColumn(checkbox_template, accessor='id', attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')

    class Meta:
        model = Budget
        fields = ('check', 'num', 'name')
        attrs = {'class': 'table table-striped table-bordered'}
        row_attrs = {"data-id": lambda record: record.pk}


class DriverTable(Table):
    orderable = False

    edit_template = '<button id="driver-edit-{{ record.pk }}" type="button" data-driver-id="{{ record.pk }}" class="button-driver-detail btn btn-info btn-sm">View</button>'
    checkbox_template = '<input class="largerCheckbox" type="checkbox">'

    check = TemplateColumn(checkbox_template, accessor='id', attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')
    edit = TemplateColumn(edit_template, attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')
    first_name = Column(attrs={'th': {'style': 'width:10%'}})
    last_name = Column(attrs={'th': {'style': 'width:10%'}})
    phone = Column(attrs={'th': {'style': 'width:15%'}})
    email = Column(attrs={'th': {'style': 'width:15%'}})

    class Meta:
        model = Driver
        fields = ('check', 'edit', 'first_name', 'last_name', 'phone', 'email')
        attrs = {'class': 'table table-striped table-bordered'}
        row_attrs = {"data-id": lambda record: record.pk}


class VehicleTable(Table):
    orderable = False

    mntc_template = '<button id="vehicle-edit-{{ record.pk }}" type="button" data-vehicle-id="{{ record.pk }}" class="button-vehicle-detail btn btn-info btn-sm">View</button>'
    checkbox_template = '<input class="largerCheckbox" type="checkbox">'

    check = TemplateColumn(checkbox_template, accessor='id', attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')
    mntc = TemplateColumn(mntc_template, attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')
    num = LinkColumn('vehicle-detail', verbose_name='#',
                     attrs={'th': {'style': 'width:5%'}}, args=[A('pk')])
    year = Column(attrs={'th': {'style': 'width:5%'}})
    make = Column(attrs={'th': {'style': 'width:10%'}})
    model = Column(attrs={'th': {'style': 'width:10%'}})
    license_plate = Column(attrs={'th': {'style': 'width:10%'}})
    reg_expire_date = Column(attrs={'th': {'style': 'width:10%'}})
    type = Column(verbose_name='Type', attrs={'th': {'style': 'width:5%'}})

    class Meta:
        model = Vehicle
        fields = ('check', 'mntc', 'num', 'year', 'make', 'model',
                  'license_plate', 'reg_expire_date', 'type', 'notes')
        attrs = {'class': 'table table-striped table-bordered'}
        row_attrs = {"data-id": lambda record: record.pk}


class TripRequestTable(Table):
    orderable = False

    edit_template = '<button id="triprequest-edit-{{ record.pk }}" type="button" data-request-id="{{ record.pk }}" class="button-request-detail btn btn-info btn-sm">View</button>'
    checkbox_template = '<input class="largerCheckbox" type="checkbox">'
    contact_fullname_template = '<a href="mailto:{{ record.contact_email }}">{{ record.contact_fullname }}</a>'
    submitted_date_template = '{{ record.depart_est.date }}'

    check = TemplateColumn(checkbox_template, accessor='id', attrs={
        'th': {'style': 'width:1%'}}, verbose_name='')
    edit = TemplateColumn(edit_template, attrs={
        'th': {'style': 'width:1%'}}, verbose_name='')
    contact_fullname = TemplateColumn(
        contact_fullname_template, verbose_name='Originator')
    depart_est = TemplateColumn(
        submitted_date_template, verbose_name='Departure Date')
    org_department = Column(verbose_name='Department', orderable=False)

    def render_status(self, record):
        color = 'black'
        if record.is_approved or record.is_completed:
            color = 'green'
        elif record.is_denied or record.is_cancelled:
            color = 'red'
        elif record.is_pending:
            color = 'blue'
        return format_html(f'<p style="color: {color}; font-weight: bold">{record.get_status_display()}</p>')

    def render_submitted(self, record):
        return record.submitted.strftime('%Y-%m-%d (%I:%M%p)')

    def render_depart_est(self, record):
        return record.depart_est.strftime('%Y-%m-%d')

    class Meta:
        """ TripRequestTable Meta """
        model = TripRequest
        fields = ('check', 'edit', 'status', 'submitted', 'depart_est',
                  'contact_fullname', 'org_department', 'vehicle_type')
        attrs = {'class': 'table table-striped table-bordered'}
        row_attrs = {"data-id": lambda record: record.pk}


class VehicleMaintenanceTable(Table):
    date = Column(footer="Total:")
    cost = SummingColumn()

    edit_template = '<button id="{{ vehicle_maintenance.id }}" type="button" class="button-edit-vehicle-maintenance btn btn-info btn-sm"><i class="far fa-edit"></i></button>'
    checkbox_template = '<input type="checkbox">'

    check = TemplateColumn(checkbox_template, accessor='id', attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')
    edit = TemplateColumn(edit_template, attrs={
        'th': {'style': 'width:1%'}}, orderable=False, verbose_name='')

    class Meta:
        model = VehicleMaintenance
        fields = [
            'check', 'date', 'mileage', 'category',
            'cost', 'notes', 'edit'
        ]
        attrs = {'class': 'table table-striped table-bordered'}
        row_attrs = {"data-id": lambda record: record.pk}
