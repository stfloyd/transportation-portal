"""
Transportation View Definitions
"""

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q, Value, CharField
from django.db.models.functions import Concat
from django.utils import timezone

from django_tables2 import SingleTableMixin, LazyPaginator, MultiTableMixin
from django_filters.views import FilterView

from transportation import models, forms, tables, filters, emails
from transportation.auth.mixins import (
    ModeratorRequiredMixin, superuser_required, moderator_required
)


logger = logging.getLogger(__name__)


def sign_out(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('sign-in'))


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'transportation/home.html'
    login_url = reverse_lazy('sign-in')


class LoginView(DjangoLoginView):
    login_url = reverse_lazy('login')
    template_name = 'transportation/auth/login.html'

    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse('home')
        return super().get_success_url()


@moderator_required
def delete_org(request, pk, *args, **kwargs):
    """ Delete org given the ID. """
    try:
        org = models.Organization.objects.get(pk=pk)
        if not models.TripRequest.objects.filter(org=org):
            raise Exception('Organization cannot be deleted as it is in use in trip requests.')
        org.delete()
        logger.info(f'Organization {pk} deleted by {request.user} ({request.user.pk})')
    except models.Organization.DoesNotExist as dne:
        message = f'Failed to delete org with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})
    return JsonResponse({'success': f'Successfully removed org with ID: {pk}'})


@moderator_required
def delete_orgs(request, *args, **kwargs):
    pk_list = kwargs.get('pk_list', [])

    for obj in models.Organization.objects.filter(pk__in=pk_list):
        if not models.TripRequest.objects.filter(org=obj):
            raise Exception('Organization cannot be deleted as it is in use in trip requests.')
        obj.delete()

    return JsonResponse({'success': 'Deleted'})


@moderator_required
def delete_department(request, org_pk, pk, *args, **kwargs):
    """ Delete department given the ID. """
    try:
        department = models.Department.objects.get(pk=pk)
        if not models.TripRequest.objects.filter(department=department):
            raise Exception('Department cannot be deleted as it is in use in trip requests.')
        department.delete()
        logger.info(
            f'Department {pk} in Organization {org_pk} deleted by {request.user} ({request.user.pk})')
    except models.Department.DoesNotExist as dne:
        message = f'Failed to delete department with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})
    return JsonResponse({'success': f'Successfully removed department with ID: {pk}'})


@moderator_required
def delete_departments(request, *args, **kwargs):
    pk_list = kwargs.get('pk_list', [])

    for obj in models.Department.objects.filter(pk__in=pk_list):
        if not models.TripRequest.objects.filter(department=obj):
            raise Exception('Department cannot be deleted as it is in use in trip requests.')
        obj.delete()

    return JsonResponse({'success': 'Deleted'})


@moderator_required
def delete_budget(request, org_pk, pk, *args, **kwargs):
    """ Delete budget given the ID. """
    try:
        budget = models.Budget.objects.get(pk=pk)
        if not models.TripRequest.objects.filter(budget=budget):
            raise Exception('Budget cannot be deleted as it is in use in trip requests.')
        budget.delete()
        logger.info(
            f'Budget {pk} in Organization {org_pk} deleted by {request.user} ({request.user.pk})')
    except models.Budget.DoesNotExist as dne:
        message = f'Failed to delete budget with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})
    return JsonResponse({'success': f'Successfully removed budget with ID: {pk}'})


@moderator_required
def delete_budgets(request, *args, **kwargs):
    pk_list = kwargs.get('pk_list', [])

    for obj in models.Budget.objects.filter(pk__in=pk_list):
        if not models.TripRequest.objects.filter(budget=obj):
            raise Exception('Budget cannot be deleted as it is in use in trip requests.')
        obj.delete()

    return JsonResponse({'success': 'Deleted'})


@moderator_required
def delete_driver(request, pk, *args, **kwargs):
    """ Delete driver given the ID. """
    try:
        driver = models.Driver.objects.get(pk=pk)
        if not models.TripRequest.objects.filter(driver=driver):
            raise Exception('Driver cannot be deleted as it is in use in trip requests.')
        driver.delete()
        logger.info(f'Driver {pk} deleted by {request.user} ({request.user.pk})')
    except models.Driver.DoesNotExist as dne:
        message = f'Failed to delete driver with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})
    return JsonResponse({'success': f'Successfully removed driver with ID: {pk}'})


@moderator_required
def deactivate_driver(request, pk, *args, **kwargs):
    """ Delete driver given the ID. """
    try:
        driver = models.Driver.objects.get(pk=pk)
        driver.status = models.Driver.STATUS_INACTIVE
        driver.save()
        logger.info(f'Driver {pk} deactivated by {request.user} ({request.user.pk})')
    except models.Driver.DoesNotExist as dne:
        message = f'Failed to deactivate driver with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})
    return JsonResponse({'success': f'Successfully deactivated driver with ID: {pk}'})


@moderator_required
def reactivate_driver(request, pk, *args, **kwargs):
    """ Delete driver given the ID. """
    try:
        driver = models.Driver.objects.get(pk=pk)
        driver.status = models.Driver.STATUS_ACTIVE
        driver.save()
        logger.info(f'Driver {pk} activated by {request.user} ({request.user.pk})')
    except models.Driver.DoesNotExist as dne:
        message = f'Failed to activate driver with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})
    return JsonResponse({'status': 'success', 'message': f'Successfully activated driver with ID: {pk}'})


@moderator_required
def update_request(request, pk, *args, **kwargs):
    """ Assign driver to a trip request. """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST is allowed on this endpoint'
        }, status=400)
    try:
        triprequest = models.TripRequest.objects.get(pk=pk)
    except models.TripRequest.DoesNotExist as dne:
        message = f'Request {pk} does not exist'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'status': 'error', 'message': message})

    driver_pk = request.POST.get('driver', None)

    if driver_pk is not None:
        try:
            driver = models.Driver.objects.get(pk=driver_pk)
        except models.Driver.DoesNotExist as dne:
            message = f'Failed to find driver {driver_pk}. Failed to update request {pk}'
            logger.error(message)
            logger.error(dne)
            return JsonResponse({'status': 'error', 'message': message})

        original_driver = triprequest.driver
        triprequest.driver = driver
        triprequest.save(kwargs={'user': request.user})

        logger.info(
            f"Trip request {pk}'s driver updated from {original_driver} to {driver} by {request.user} ({request.user.pk})")

        return JsonResponse({'status': 'success', 'message': f'Successfully assigned driver {driver_pk} to request {pk}'})

    return JsonResponse({
        'status': 'error',
        'message': f'No queryable parameters provided. Failed to update request {pk}'
    })


@moderator_required
def delete_drivers(request, *args, **kwargs):
    pk_list = kwargs.get('pk_list', [])

    for obj in models.Drivers.objects.filter(pk__in=pk_list):
        obj.delete()
        logger.info(f"Driver {obj.pk}'s deleted by {request.user} ({request.user.pk})")

    return JsonResponse({'success': 'Deleted'})


@moderator_required
def delete_vehicle(request, pk, *args, **kwargs):
    """ Delete vehicle given the ID. """
    try:
        vehicle = models.Vehicle.objects.get(pk=pk)
        if models.TripRequest.objects.filter(vehicle=vehicle).count() > 0:
            raise Exception('Vehicle cannot be deleted as it is in use in trip requests.')
        vehicle.delete()
        logger.info(f'Vehicle {pk} deleted by {request.user} ({request.user.pk})')
    except models.Vehicle.DoesNotExist as dne:
        message = f'Failed to delete vehicle with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})
    return JsonResponse({'success': f'Successfully removed vehicle with ID: {pk}'})


@moderator_required
def delete_trip_request(request, pk, *args, **kwargs):
    """ Delete trip request given the ID. """
    try:
        triprequest = models.TripRequest.objects.get(pk=pk)
        triprequest.delete()
        logger.info(f'Trip request {pk} deleted by {request.user} ({request.user.pk})')
    except models.TripRequest.DoesNotExist as dne:
        message = f'Failed to delete trip request with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})
    return JsonResponse({'success': f'Successfully removed trip request with ID: {pk}'})


def cancel_trip_request(request, pk, *args, **kwargs):
    """ Delete trip request given the ID. """
    try:
        triprequest = models.TripRequest.objects.get(pk=pk)
        triprequest.cancel(commit=True, kwargs={'user': request.user, 'request': triprequest})
        logger.info(f'Trip request {pk} cancelled by {request.user} ({request.user.pk})')
    except models.TripRequest.DoesNotExist as dne:
        message = f'Failed to cancel trip request with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})

    email = emails.TripRequestCanceledEmail(triprequest)
    email.send()

    return JsonResponse({'success': f'Successfully canceled trip request with ID: {pk}'})


@moderator_required
def assign_request_moderator(request, pk, *args, **kwargs):
    """ Assign current moderator to a TripRequest ID. """
    try:
        triprequest = models.TripRequest.objects.get(pk=pk)
        kwargs.update({'user': request.user, 'request': triprequest})
        triprequest.assign_moderator(commit=True, *args, **kwargs)
        logger.info(
            f'Trip request {pk} assigned moderator of {request.user} ({request.user.pk}) by {request.user} ({request.user.pk})')
    except models.Driver.DoesNotExist as dne:
        message = f'Failed to assign moderator for TripRequest, ID: {pk}'
        return JsonResponse({'error': message})
    except ValueError as ve:
        message = f'Failed to assign moderator for TripRequest, ID: {pk}'
        return JsonResponse({'error': message})
    return JsonResponse({'success': f'Successfully assigned moderator for TripRequest, ID: {pk}'})


@moderator_required
def approve_request(request, pk, *args, **kwargs):
    """ Set a trip request to approved. """
    try:
        triprequest = models.TripRequest.objects.get(pk=pk)
        original_status = triprequest.status
        if original_status == models.TripRequest.STATUS_APPROVED:
            return JsonResponse({'error': 'This trip request is already approved'})
        triprequest.approve(commit=True, user=request.user)
        logger.info(f'Trip request {pk} approved by {request.user} ({request.user.pk})')
    except models.TripRequest.DoesNotExist as dne:
        message = f'Failed to approve TripRequest, ID: {pk}'
        logger.info(message)
        return JsonResponse({'status': 'error', 'message': message})
    except ValueError as ve:
        message = f'Failed to approve TripRequest, ID: {pk}'
        logger.error(message)
        return JsonResponse({'status': 'error', 'message': message})
    except ValidationError as ve:
        message = f'Failed to approve TripRequest, ID: {pk}. Did not meet all requirements.'
        logger.error(message)
        return JsonResponse({'status': 'error', 'message': message})

    if original_status != models.TripRequest.STATUS_APPROVED:
        email = emails.TripRequestApprovedEmail(triprequest)
        email.send()

    return JsonResponse({'status': 'success', 'message': f'Successfully approved TripRequest, ID: {pk}'})


@moderator_required
def pending_request(request, pk, *args, **kwargs):
    """ Set a trip request to pending. """
    try:
        triprequest = models.TripRequest.objects.get(pk=pk)
        original_status = triprequest.status
        if original_status == models.TripRequest.STATUS_PENDING:
            return JsonResponse({'error': 'This trip request is already pending'})
        triprequest.status = models.TripRequest.STATUS_PENDING
        triprequest.save(user=request.user)
        logger.info(f'Trip request {pk} set to pending by {request.user} ({request.user.pk})')
    except models.TripRequest.DoesNotExist as dne:
        message = f'Failed to change status of TripRequest, ID: {pk}'
        return JsonResponse({'error': message})
    except ValueError as ve:
        message = f'Failed to change status of TripRequest, ID: {pk}'
        return JsonResponse({'error': message})

    if original_status != models.TripRequest.STATUS_PENDING:
        email = emails.TripRequestStatusEmail(
            triprequest, original_status, models.TripRequest.STATUS_PENDING)
        email.send()

    return JsonResponse({'success': f'Successfully changed status of TripRequest, ID: {pk} to pending'})


@moderator_required
def deny_request(request, pk, *args, **kwargs):
    """ Deny a trip request. """
    try:
        triprequest = models.TripRequest.objects.get(pk=pk)
        original_status = triprequest.status
        if original_status == models.TripRequest.STATUS_DENIED:
            return JsonResponse({'error': 'This trip request is already denied'})
        triprequest.deny(commit=True, user=request.user)
        logger.info(f'Trip request {pk} denied by {request.user} ({request.user.pk})')
    except models.TripRequest.DoesNotExist as dne:
        message = f'Failed to deny TripRequest, ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})

    if original_status != models.TripRequest.STATUS_DENIED:
        email = emails.TripRequestDeniedEmail(triprequest)
        email.send()

    return JsonResponse({'success': f'Successfully denied TripRequest, ID: {pk}'})


@moderator_required
def return_request_vehicle(request, pk, *args, **kwargs):
    """ Mark a request as having the vehicle returned """
    try:
        triprequest = models.TripRequest.objects.get(pk=pk)
        old_status = triprequest.status
        triprequest.return_vehicle(commit=True, user=request.user)
        new_status = triprequest.status
        logger.info(f'Trip request {pk} marked returned by {request.user} ({request.user.pk})')
    except models.TripRequest.DoesNotExist as dne:
        message = f'Failed to change status to returned for TripRequest, ID: {pk}'
        return JsonResponse({'error': message})
    except ValueError as ve:
        message = f'Failed to change status to returned for TripRequest, ID: {pk}'
        return JsonResponse({'error': message})

    email = emails.TripRequestStatusEmail(triprequest, old_status, new_status)
    email.send()

    return JsonResponse({'success': f'Successfully updated status for TripRequest, ID: {pk}'})


@moderator_required
def finalize_request(request, pk, *args, **kwargs):
    """ Finalize request """
    try:
        triprequest = models.TripRequest.objects.get(pk=pk)
        old_status = triprequest.status
        triprequest.finalize(commit=True, user=request.user)
        new_status = triprequest.status
        logger.info(f'Trip request {pk} finalized by {request.user} ({request.user.pk})')
    except models.Driver.DoesNotExist as dne:
        message = f'Failed to approve TripRequest, ID: {pk}'
        return JsonResponse({'error': message})
    except ValueError as ve:
        message = f'Failed to approve TripRequest, ID: {pk}'
        return JsonResponse({'error': message})

    email = emails.TripRequestStatusEmail(triprequest, old_status, new_status)
    email.send()

    return JsonResponse({'success': f'Successfully approved TripRequest, ID: {pk}'})


@moderator_required
def delete_vehicle_maintenance(request, vehicle_pk, pk, *args, **kwargs):
    """ Delete vehicle maintenance given the ID. """
    try:
        maintenance = models.VehicleMaintenance.objects.get(pk=pk)
        maintenance.delete()
        logger.info(
            f"Vehicle {vehicle_pk}'s maintenance {pk} deleted by {request.user} ({request.user.pk})")
    except models.VehicleMaintenance.DoesNotExist as dne:
        message = f'Failed to delete vehicle maintenance with ID: {pk}'
        logger.error(message)
        logger.error(dne)
        return JsonResponse({'error': message})
    return JsonResponse({'success': f'Successfully removed vehicle maintenance with ID: {pk}'})


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


@moderator_required
def print_labels(request, *args, **kwargs):
    """ Delete vehicle maintenance given the ID. """
    pk_list = request.GET.get('pk_list', None)
    trip_requests = []
    for pk in pk_list.split(','):
        tr = models.TripRequest.objects.get(pk=int(pk))
        trip_requests.append(tr)
    context = {
        'triprequests': chunks(trip_requests, 3)
    }
    return render(request, 'transportation/labels.html', context)


@moderator_required
def print_tickets(request, *args, **kwargs):
    """ Delete vehicle maintenance given the ID. """
    pk_list = request.GET.get('pk_list', None)
    context = {'triprequests': []}
    for pk in pk_list.split(','):
        tr = models.TripRequest.objects.get(pk=int(pk))
        context['triprequests'].append(tr)
    return render(request, 'transportation/print-tickets.html', context)


@moderator_required
def run_org_report(request, *args, **kwargs):
    pk_list = request.GET.get('pk_list', None)
    context = {'orgs': []}
    for pk in pk_list.split(','):
        org = models.Organization.objects.get(pk=int(pk))
        context['orgs'].append(org)
    return render(request, 'transportation/reports/soon.html', context)


@moderator_required
def run_vehicle_report(request, *args, **kwargs):
    """ Delete vehicle maintenance given the ID. """
    pk_list = request.GET.get('pk_list', None)
    context = {'vehicles': []}
    for pk in pk_list.split(','):
        vehicle = models.Vehicle.objects.get(pk=int(pk))
        context['vehicles'].append(vehicle)
    return render(request, 'transportation/reports/soon.html', context)


@moderator_required
def run_triprequest_report(request, *args, **kwargs):
    """ Delete vehicle maintenance given the ID. """
    pk_list = request.GET.get('pk_list', None)
    context = {'vehicles': []}
    for pk in pk_list.split(','):
        vehicle = models.TripRequest.objects.get(pk=int(pk))
        context['vehicles'].append(vehicle)
    return render(request, 'transportation/reports/soon.html', context)


@moderator_required
def run_driver_report(request, *args, **kwargs):
    """ Delete vehicle maintenance given the ID. """
    pk_list = request.GET.get('pk_list', None)
    context = {'drivers': []}
    for pk in pk_list.split(','):
        driver = models.Driver.objects.get(pk=int(pk))
        context['drivers'].append(driver)
    return render(request, 'transportation/reports/soon.html', context)


def load_departments(request, *args, **kwargs):
    org_ids = request.GET.get('orgs', None)

    context = {
        'orgs': [],
        'departments': []
    }

    if org_ids is not None:
        org_ids_list = map(int, org_ids.split(','))
        orgs = models.Organization.objects.filter(pk__in=org_ids_list)
        departments = models.Department.objects.filter(org_id__in=org_ids_list).order_by('name')
        context['orgs'] = [o for o in orgs]
    else:
        departments = models.Department.objects.none()

    context['departments'] = departments
    return render(request, 'transportation/partial/departments-dropdown.html', context)


def load_budgets(request, *args, **kwargs):
    org_ids = request.GET.get('orgs', None)

    context = {
        'orgs': [],
        'budgets': []
    }

    if org_ids is not None:
        org_ids_list = map(int, org_ids.split(','))
        orgs = models.Organization.objects.filter(pk__in=org_ids_list)
        budgets = models.Budget.objects.filter(org_id__in=org_ids_list).order_by('name')
        context['orgs'] = [o for o in orgs]
    else:
        budgets = models.Budget.objects.none()

    context['budgets'] = budgets
    return render(request, 'transportation/partial/budgets-dropdown.html', context)


def load_drivers(request, *args, **kwargs):
    query = request.GET.get('q', None)

    if query is None:
        return JsonResponse([], safe=False)

    qs = models.Driver.objects.filter(Q(first_name__istartswith=query) | Q(last_name__istartswith=query)).annotate(
        full_name=Concat(
            'first_name', Value(' '), 'last_name',
            output_field=CharField()
        )
    )

    data = list(qs.values('id', 'full_name'))

    return JsonResponse(data, safe=False)


class BudgetsView(ModeratorRequiredMixin, SingleTableMixin, FilterView):
    pass


class BudgetDetailView(ModeratorRequiredMixin, FilterView):
    """ Budget detail view. """

    template_name = 'transportation/budget-detail.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('org-detail')

    model = models.Budget
    budget_url_kwarg = 'pk'
    budget_pk = None
    budget = None
    org_url_kwarg = 'org_pk'
    org_pk = None
    org = None

    def dispatch(self, request, *args, **kwargs):
        self.org_pk = kwargs[self.org_url_kwarg]
        kwargs.pop(self.org_url_kwarg, None)
        self.budget_pk = kwargs[self.budget_url_kwarg]
        kwargs.pop(self.budget_url_kwarg, None)
        self.org = models.Organization.objects.get(pk=self.org_pk)
        self.budget = self.model.objects.get(pk=self.budget_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['org'] = self.org
        data['department'] = self.department
        return data


class CreateBudgetView(ModeratorRequiredMixin, CreateView):
    """ Budget form (create) view. """

    template_name = 'transportation/budget-form.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('org-list')
    model = models.Budget
    form_class = forms.BudgetForm

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        org_pk = kwargs.get('org_pk', None)
        if 'cancel' in request.POST:
            if org_pk is None:
                return HttpResponseRedirect(self.success_url)
            else:
                return HttpResponseRedirect(reverse('org-detail', kwargs={'pk': org_pk}))
        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'New Budget'
        context['org'] = None
        return context


class UpdateBudgetView(ModeratorRequiredMixin, UpdateView):
    """ Budget form (update) view. """

    template_name = 'transportation/budget-form.html'
    login_url = reverse_lazy('sign-in')
    pk_url_kwarg = 'pk'
    model = models.Budget
    form_class = forms.BudgetForm

    def get_success_url(self):
        return reverse('budget-detail', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        self.object = self.get_object()

        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())

        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'Edit Budget'
        context['org'] = self.object
        return context


class DepartmentsView(ModeratorRequiredMixin, SingleTableMixin, FilterView):
    pass


class DepartmentDetailView(ModeratorRequiredMixin, FilterView):
    """ Department detail view. """

    template_name = 'transportation/department-detail.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('org-detail')

    model = models.Department
    department_url_kwarg = 'pk'
    department_pk = None
    department = None
    org_url_kwarg = 'org_pk'
    org_pk = None
    org = None

    def dispatch(self, request, *args, **kwargs):
        self.org_pk = kwargs[self.org_url_kwarg]
        kwargs.pop(self.org_url_kwarg, None)
        self.department_pk = kwargs[self.department_url_kwarg]
        kwargs.pop(self.department_url_kwarg, None)
        self.org = models.Organization.objects.get(pk=self.org_pk)
        self.department = self.model.objects.get(pk=self.department_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['org'] = self.org
        data['department'] = self.department
        return data


class CreateDepartmentView(ModeratorRequiredMixin, CreateView):
    """ Department form (create) view. """

    template_name = 'transportation/department-form.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('org-list')
    model = models.Department
    form_class = forms.DepartmentForm

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        org_pk = kwargs.get('org_pk', None)
        if 'cancel' in request.POST:
            if org_pk is None:
                return HttpResponseRedirect(self.success_url)
            else:
                return HttpResponseRedirect(reverse('org-detail', kwargs={'pk': org_pk}))
        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'New Department'
        context['org'] = None
        return context


class UpdateDepartmentView(ModeratorRequiredMixin, UpdateView):
    """ Department form (update) view. """

    template_name = 'transportation/department-form.html'
    login_url = reverse_lazy('sign-in')
    pk_url_kwarg = 'pk'
    model = models.Department
    form_class = forms.DepartmentForm

    def get_success_url(self):
        return reverse('department-detail', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        self.object = self.get_object()

        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())

        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'Edit Department'
        context['org'] = self.object
        return context


class OrganizationsView(ModeratorRequiredMixin, SingleTableMixin, FilterView):
    """ Organization table view. """

    template_name = 'transportation/orgs.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('org-list')

    model = models.Organization
    table_class = tables.OrganizationTable
    table_data = models.Organization.objects.all()
    filterset_class = filters.OrganizationFilter
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter = context['filter']
        table = self.table_class(filter.qs)
        context['table'] = table
        return context


class OrganizationDetailView(ModeratorRequiredMixin, FilterView):
    """ Driver detail view. """

    template_name = 'transportation/org-detail.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('org-list')

    departments_table_class = tables.DepartmentsTable
    budgets_table_class = tables.BudgetsTable
    paginate_by = 25

    model = models.Organization
    org_url_kwarg = 'pk'
    org_pk = None
    org = None

    def get_departments_table_data(self):
        return models.Department.objects.filter(org=self.org)

    def get_budgets_table_data(self):
        return models.Budget.objects.filter(org=self.org)

    def dispatch(self, request, *args, **kwargs):
        self.org_pk = kwargs[self.org_url_kwarg]
        kwargs.pop(self.org_url_kwarg, None)
        self.org = self.model.objects.get(pk=self.org_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['org'] = self.org
        data['departments_table'] = self.departments_table_class(self.get_departments_table_data())
        data['budgets_table'] = self.budgets_table_class(self.get_budgets_table_data())
        return data


class CreateOrganizationView(ModeratorRequiredMixin, CreateView):
    """ Organization form (update) view. """

    template_name = 'transportation/org-form.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('org-list')
    model = models.Organization
    form_class = forms.OrganizationForm

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'New Organization'
        context['org'] = None
        return context


class UpdateOrganizationView(ModeratorRequiredMixin, UpdateView):
    """ Organization form (update) view. """

    template_name = 'transportation/org-form.html'
    login_url = reverse_lazy('sign-in')
    pk_url_kwarg = 'pk'
    model = models.Organization
    form_class = forms.OrganizationForm

    def get_success_url(self):
        return reverse('org-detail', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        self.object = self.get_object()

        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())

        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'Edit Organization'
        context['org'] = self.object
        return context


class DriversView(ModeratorRequiredMixin, SingleTableMixin, FilterView):
    """ Driver table view. """

    template_name = 'transportation/drivers.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('driver-list')

    model = models.Driver
    table_class = tables.DriverTable
    table_data = models.Driver.objects.all()
    filterset_class = filters.DriverFilter
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter = context['filter']
        table = self.table_class(filter.qs)
        context['table'] = table
        return context

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        if kwargs['data'] is None:
            filter_values = {}
        else:
            filter_values = kwargs['data'].copy()

        if not filter_values:
            filter_values['status'] = 1

        kwargs['data'] = filter_values
        return kwargs


class DriverDetailView(ModeratorRequiredMixin, FilterView):
    """ Driver detail view. """

    template_name = 'transportation/driver-detail.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('driver-list')

    table_class = tables.TripRequestTable
    #table_data = models.TripRequest.objects.all()
    filterset_class = filters.TripRequestFilter
    paginate_by = 25

    model = models.Driver
    driver_url_kwarg = 'pk'
    driver_pk = None
    driver = None

    def get_table_data(self):
        return self.driver.get_assigned_trips()

    def dispatch(self, request, *args, **kwargs):
        self.driver_pk = kwargs[self.driver_url_kwarg]
        kwargs.pop(self.driver_url_kwarg, None)
        self.driver = self.model.objects.get(pk=self.driver_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['driver'] = self.driver
        data['table'] = self.table_class(self.get_table_data())
        return data


class CreateDriverView(ModeratorRequiredMixin, CreateView):
    """ Driver form (update) view. """

    template_name = 'transportation/driver-form.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('driver-list')
    model = models.Driver
    form_class = forms.DriverForm

    def form_valid(self, form):
        form.instance.status = 1  # Active
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'New Driver'
        context['driver'] = None
        return context


class UpdateDriverView(ModeratorRequiredMixin, UpdateView):
    """ Driver form (update) view. """

    template_name = 'transportation/driver-form.html'
    login_url = reverse_lazy('sign-in')
    pk_url_kwarg = 'pk'
    model = models.Driver
    form_class = forms.DriverForm

    def get_success_url(self):
        return reverse('driver-detail', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        self.object = self.get_object()

        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())

        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'Edit Driver'
        context['driver'] = self.object
        return context


class VehiclesView(ModeratorRequiredMixin, SingleTableMixin, FilterView):
    """ Vehicles table view. """

    template_name = 'transportation/vehicles.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('vehicle-list')

    model = models.Vehicle
    table_class = tables.VehicleTable
    table_data = models.Vehicle.objects.all()
    filterset_class = filters.VehicleFilter
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter = context['filter']
        context['table'] = self.table_class(filter.qs)
        return context

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        if kwargs['data'] is None:
            filter_values = {}
        else:
            filter_values = kwargs['data'].copy()

        if not filter_values:
            filter_values['status'] = 1
            filter_values['sort'] = '-num'

        kwargs['data'] = filter_values

        return kwargs


class CreateVehicleView(ModeratorRequiredMixin, CreateView):
    """ Vehicle form (update) view. """

    template_name = 'transportation/vehicle-form.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('vehicle-list')
    model = models.Vehicle
    form_class = forms.VehicleForm

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'New Vehicle'
        context['vehicle'] = None
        return context


class UpdateVehicleView(ModeratorRequiredMixin, UpdateView):
    """ Vehicle form (update) view. """

    template_name = 'transportation/vehicle-form.html'
    login_url = reverse_lazy('sign-in')
    pk_url_kwarg = 'pk'
    model = models.Vehicle
    form_class = forms.VehicleForm

    def get_success_url(self):
        return reverse('vehicle-detail', kwargs={'vehicle_pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        self.object = self.get_object()

        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())

        return super().post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pagetitle'] = 'Edit Vehicle'
        context['vehicle'] = self.object
        return context


class VehicleDetailView(ModeratorRequiredMixin, SingleTableMixin, FilterView):
    """ Vehicle detail view. """

    template_name = 'transportation/vehicle-detail.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('vehicle-list')

    model = models.Vehicle
    table_class = tables.VehicleMaintenanceTable
    table_data = models.VehicleMaintenance.objects.all()
    filterset_class = filters.VehicleMaintenanceFilter
    paginate_by = 25

    table2_class = tables.TripRequestTable
    table2_data = models.TripRequest.objects.all()
    table2_filterset_class = filters.TripRequestFilter

    vehicle_url_kwarg = 'vehicle_pk'
    vehicle_pk = None
    vehicle = None

    def get_table_data(self):
        table_data = super().get_table_data()
        return table_data.filter(vehicle=self.vehicle)

    def get_table2_data(self):
        queryset = self.table2_data
        return queryset.filter(vehicle=self.vehicle)

    def dispatch(self, request, *args, **kwargs):
        self.vehicle_pk = kwargs[self.vehicle_url_kwarg]
        kwargs.pop(self.vehicle_url_kwarg, None)
        self.vehicle = self.model.objects.get(pk=self.vehicle_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['vehicle'] = self.vehicle
        data['table'] = self.table_class(self.get_table_data().order_by('date'))
        data['tripstable'] = self.table2_class(self.get_table2_data().order_by('depart_est'))
        return data


class CreateVehicleMaintenanceView(ModeratorRequiredMixin, CreateView):
    model = models.VehicleMaintenance
    form_class = forms.VehicleMaintenanceForm
    template_name = 'transportation/vehicle-maintenance-form.html'

    vehicle_url_kwarg = 'vehicle_pk'
    vehicle_pk = None
    vehicle = None

    def get_success_url(self):
        return reverse('vehicle-detail', kwargs={'vehicle_pk': self.vehicle_pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({self.vehicle_url_kwarg: self.vehicle_pk})
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.vehicle_pk = kwargs.pop(self.vehicle_url_kwarg)
        self.vehicle = models.Vehicle.objects.get(pk=self.vehicle_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['vehicle'] = self.vehicle
        context['pagetitle'] = 'New Vehicle Maintenance'
        return context

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            return HttpResponseRedirect(self.get_success_url())
        elif "submit" in request.POST:
            form = forms.VehicleMaintenanceForm(
                request.POST,
                vehicle_pk=self.vehicle_pk
            )
            if form.is_valid():
                maintenance = models.VehicleMaintenance()
                maintenance.vehicle = self.vehicle
                maintenance.date = form.cleaned_data['date']
                maintenance.mileage = form.cleaned_data['mileage']
                maintenance.category = form.cleaned_data['category']
                maintenance.cost = form.cleaned_data['cost']
                maintenance.notes = form.cleaned_data['notes']
                maintenance.save(user=request.user)
                return HttpResponseRedirect(self.get_success_url())
        return super().post(request, *args, **kwargs)


class UpdateVehicleMaintenanceView(ModeratorRequiredMixin, UpdateView):
    model = models.VehicleMaintenance
    form_class = forms.VehicleMaintenanceForm
    template_name = 'transportation/vehicle-maintenance-form.html'
    pk_url_kwarg = 'pk'

    vehicle_url_kwarg = 'vehicle_pk'
    vehicle_pk = None
    vehicle = None

    def get_success_url(self):
        return reverse('vehicle-detail', kwargs={'vehicle_pk': self.vehicle_pk})

    def dispatch(self, request, *args, **kwargs):
        self.vehicle_pk = kwargs.pop(self.vehicle_url_kwarg)
        self.vehicle = models.Vehicle.objects.get(pk=self.vehicle_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({self.vehicle_url_kwarg: self.vehicle_pk})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())

        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicle'] = self.vehicle
        context['pagetitle'] = 'Edit Vehicle Maintenance'
        return context


class TripRequestsView(LoginRequiredMixin, SingleTableMixin, FilterView):
    """ Trip request table view. """

    template_name = 'transportation/requests.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('request-list')

    model = models.TripRequest
    table_class = tables.TripRequestTable
    queryset = models.TripRequest.objects.order_by('submitted')
    filterset_class = filters.TripRequestFilter
    paginate_by = 25


class CreateTripRequestView(LoginRequiredMixin, CreateView):
    """ Trip request form create view. """

    template_name = 'transportation/request-form.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('request-list')
    model = models.TripRequest
    form_class = forms.TripRequestForm

    def get_success_url(self):
        return reverse('request-detail', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.requestor = self.request.user

        if self.object.requested_driver is not None and self.object.requested_driver:
            existing_driver = models.Driver.objects.annotate(
                full_name=Concat(
                    'first_name', Value(' '), 'last_name',
                    output_field=CharField()
                )
            ).filter(
                Q(first_name__icontains=self.object.requested_driver) |
                Q(last_name__icontains=self.object.requested_driver) |
                Q(full_name__icontains=self.object.requested_driver)
            ).first()

            if existing_driver is not None:
                self.object.driver = existing_driver
            else:
                try:
                    split_fullname = self.object.requested_driver.split(' ')
                    new_driver = models.Driver.objects.create(
                        first_name=split_fullname[0],
                        last_name=split_fullname[1]
                    )
                    self.object.driver = new_driver
                except:
                    self.object.driver = None

        self.object.save(user=self.request.user)

        email = emails.TripRequestCreatedEmail(self.object)
        email.send()

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pagetitle'] = 'Create Trip Request'
        context['triprequest'] = None
        return context


class TripRequestDetailView(LoginRequiredMixin, TemplateView):
    """ TripRequest detail view. """

    template_name = 'transportation/request-detail.html'
    login_url = reverse_lazy('sign-in')
    success_url = reverse_lazy('request-list')

    model = models.TripRequest
    request_url_kwarg = 'pk'
    request_pk = None
    triprequest = None

    def dispatch(self, request, *args, **kwargs):
        self.request_pk = kwargs[self.request_url_kwarg]
        kwargs.pop(self.request_url_kwarg, None)
        self.triprequest = self.model.objects.get(pk=self.request_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['triprequest'] = self.triprequest

        existing_driver = None

        if self.triprequest.requested_driver is not None and self.triprequest.requested_driver:
            existing_driver = models.Driver.objects.annotate(
                full_name=Concat(
                    'first_name', Value(' '), 'last_name',
                    output_field=CharField()
                )
            ).filter(
                Q(first_name__icontains=self.triprequest.requested_driver) |
                Q(last_name__icontains=self.triprequest.requested_driver) |
                Q(full_name__icontains=self.triprequest.requested_driver)
            ).first()

        data['recommended_driver'] = existing_driver

        return data


class UpdateTripRequestView(LoginRequiredMixin, UpdateView):
    """ Trip request form (update) view. """

    template_name = 'transportation/request-form.html'
    login_url = reverse_lazy('sign-in')
    pk_url_kwarg = 'pk'
    model = models.TripRequest
    form_class = forms.TripRequestForm

    def get_success_url(self):
        return reverse('request-detail', kwargs={'pk': self.object.pk})

    def get(self, request, *args, **kwargs):
        if self.request.user.is_moderator or self.request.user.is_staff:
            self.form_class = forms.TripRequestAdminForm
            return super().get(request, *args, **kwargs)

        self.object = self.get_object()

        if self.object.is_pending:
            return super().get(request, *args, **kwargs)

        return self.handle_no_permission()

    def post(self, request, *args, **kwargs):
        """ Post data to the view. """
        if self.request.user.is_moderator or self.request.user.is_staff:
            self.form_class = forms.TripRequestAdminForm

        self.object = self.get_object()

        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())

        if self.request.user.is_moderator or self.request.user.is_staff or self.object.is_pending:
            response = super().post(request, *args, **kwargs)
            if 'approve' in request.POST:
                original_status = self.object.status
                self.object.approve(commit=True, user=self.request.user)
                if original_status != models.TripRequest.STATUS_APPROVED:
                    email = emails.TripRequestApprovedEmail(self.object)
                    email.send()
            return response

        return self.handle_no_permission()

    def form_valid(self, form):
        old_status = self.object.status
        triprequest = form.save(commit=False)
        triprequest.save(user=self.request.user)
        self.object = triprequest
        new_status = self.object.status

        if old_status != new_status:
            email = emails.TripRequestStatusEmail(triprequest, old_status, new_status)
            email.send()

        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': self.get_object()})
        return kwargs

    def get_context_data(self, **kwargs):
        if self.request.user.is_moderator or self.request.user.is_staff:
            self.form_class = forms.TripRequestAdminForm
        context = super().get_context_data(**kwargs)
        context['pagetitle'] = 'Edit Trip Request'
        context['triprequest'] = self.object
        return context
