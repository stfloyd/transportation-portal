from django.core.mail import send_mail
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

from .models import TripRequest


logger = logging.getLogger(__name__)


class TripRequestEmail:
    def __init__(self, triprequest, requestor_subject, requestor_body, manager_notify=False, manager_subject=None, manager_body=None):
        self.triprequest = triprequest
        self.from_email = self.contact_email
        self.requestor_subject = requestor_subject
        self.requestor_body = requestor_body
        self.manager_notify = manager_notify and manager_subject is not None and manager_body is not None
        self.manager_subject = manager_subject
        self.manager_body = manager_body

    @property
    def contact_email(self):
        return settings.TP_DEFAULT_FROM_EMAIL

    def _recipients(self, manager_only=False, extra_emails=None):
        recipients = extra_emails if extra_emails is not None else []
        recipients.append(self.triprequest.contact_email)
        return recipients

    def send_manager(self, emails=None):
        if self.manager_subject is None or self.manager_body is None:
            raise ValidationError(
                _(f'Unable to email manager with no subject or body provided to {self.__className__} object'),
                params={'triprequest': self.triprequest,
                        'requestor_subject': self.requestor_subject, 'requestor_body': self.requestor_body}
            )
        mail = send_mail(
            self.manager_subject,
            self.manager_body,
            self.from_email,
            self._recipients(manager_only=True)
        )

    def send_requestor(self, emails=None):
        mail = send_mail(
            self.requestor_subject,
            self.requestor_body,
            self.from_email,
            self._recipients(extra_emails=emails)
        )

    def send(self, emails=None):
        if self.manager_notify:
            try:
                self.send_manager(emails)
            except ValidationError as ve:
                pass
        self.send_requestor(emails)


class TripRequestCreatedEmail(TripRequestEmail):
    def __init__(self, triprequest):
        requestor_subject = f'Vehicle Request {triprequest.submitted}'
        requestor_body = f"{triprequest.requestor.first_name},\r\nYour vehicle request ID no. {triprequest.pk} has been submitted and will be processed in due time. When your request has been processed you will be notified. You can click on the link or copy it into the address bar of your Internet browser to verify this for youself: transportation.trbc.org{reverse('request-detail', kwargs={ 'pk': triprequest.pk })}. If you have questions or problems with your request contact the transportation office at ext. 3155 or email {triprequest.manager_fullname}, {self.contact_email}"

        manager_subject = f'New Vehicle Request {triprequest.pk}'
        manager_body = f'New vehicle request from {triprequest.requestor_fullname}'

        super().__init__(triprequest, requestor_subject, requestor_body, True, manager_subject, manager_body)


class TripRequestCanceledEmail(TripRequestEmail):
    def __init__(self, triprequest):
        requestor_subject = f'Vehicle Request {triprequest.pk} has been canceled'
        requestor_body = f"{triprequest.requestor.first_name},\r\nYour vehicle request ID no. {triprequest.pk} has been canceled and no longer processed. If you believe there is an error please contact our office. You can click on the link or copy it into the address bar of your Internet browser to verify this for youself: transportation.trbc.org{reverse('request-detail', kwargs={ 'pk': triprequest.pk })}. If you have questions or problems with your request contact the transportation office at ext. 3155 or email {triprequest.manager_fullname}, {self.contact_email}"

        manager_subject = f'Vehicle Request {triprequest.pk} canceled by user'
        manager_body = f"Vehicle request from {triprequest.requestor_fullname} has been canceled by the user. You can verify this for yourself: transportation.trbc.org{reverse('request-detail', kwargs={ 'pk': triprequest.pk })}"

        super().__init__(triprequest, requestor_subject, requestor_body, True, manager_subject, manager_body)


class TripRequestApprovedEmail(TripRequestEmail):
    def __init__(self, triprequest):
        subject = f'Your vehicle request has been APPROVED for request {triprequest.pk}'
        body = f"{triprequest.requestor.first_name},\r\nYour vehicle request ID no. {triprequest.pk} has been approved. You can click on the link or copy it into the address bar of your Internet browser to verify this for youself: transportation.trbc.org{reverse('request-detail', kwargs={ 'pk': triprequest.pk })}. If you have questions or problems with your request contact the transportation office at ext. 3155 or email {triprequest.manager_fullname}, {self.contact_email}"

        super().__init__(triprequest, subject, body)


class TripRequestDeniedEmail(TripRequestEmail):
    def __init__(self, triprequest):
        subject = f'Your vehicle request has been DENIED for request {triprequest.pk}'
        body = f"{triprequest.requestor.first_name},\r\nYour vehicle request ID no. {triprequest.pk} has been denied. You can click on the link or copy it into the address bar of your Internet browser to verify this for youself: transportation.trbc.org{reverse('request-detail', kwargs={ 'pk': triprequest.pk })}. If you have questions or problems with your request contact the transportation office at ext. 3155 or email {triprequest.manager_fullname}, {self.contact_email}"

        super().__init__(triprequest, subject, body)


class TripRequestStatusEmail(TripRequestEmail):
    def __init__(self, triprequest, old_status, new_status):
        if triprequest.status != new_status:
            raise ValidationError(
                _(f'{triprequest.status} does not equal {new_status}'),
                params={'triprequest': triprequest,
                        'old_status': old_status, 'new_status': new_status}
            )
        self.old_status = old_status
        self.new_status = new_status
        old_status_text = self._get_status_display(self.old_status)
        new_status_text = self._get_status_display(self.new_status)
        subject = f'Your vehicle request\'s status has updated to \'{new_status_text}\' for request {triprequest.pk}'
        body = f"{triprequest.requestor.first_name},\r\nYour vehicle request ID no. {triprequest.pk} has had it's status changed from '{old_status_text}' to '{new_status_text}'. You can click on the link or copy it into the address bar of your Internet browser to verify this for youself and see if you need to provide more information: transportation.trbc.org{reverse('request-detail', kwargs={ 'pk': triprequest.pk })}. If you have questions or problems with your request contact the transportation office at ext. 3155 or email {triprequest.manager_fullname}, {self.contact_email}"

        super().__init__(triprequest, subject, body)

    def _get_status_display(self, status):
        return TripRequest.STATUS_CHOICES[status][1]
