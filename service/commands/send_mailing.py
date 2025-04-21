import os
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from service.models import Mailing, SendAttempt


class Command(BaseCommand):
    help = "Send a mailing by ID"

    def add_arguments(self, parser):
        parser.add_argument("mailing_id", type=int)

    def handle(self, *args, **kwargs):
        mailing_id = kwargs["mailing_id"]

        try:
            mailing = Mailing.objects.get(id=mailing_id)
        except Mailing.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Рассылка с ID {mailing_id} не найдена.")
            )
            return

        if mailing.status != "Запущена":
            self.stdout.write(
                self.style.ERROR(
                    f"Рассылка с ID {mailing_id} не запущена. Текущий статус: {mailing.status}."
                )
            )
            return

        recipients = mailing.recipients.all()
        total_sent = 0
        successful_sends = 0
        failed_sends = 0

        for recipient in recipients:
            try:
                send_mail(
                    mailing.message.subject,
                    mailing.message.body,
                    os.getenv("EMAIL_HOST_USER"),
                    [recipient.email],
                    fail_silently=False,
                )
                status = "Успешно"
                server_response = "Письмо отправлено успешно."
                successful_sends += 1
            except Exception as e:
                status = "Не успешно"
                server_response = str(e)
                failed_sends += 1

            total_sent += 1

            SendAttempt.objects.create(
                mailing=mailing,
                status=status,
                server_response=server_response,
                recipient=recipient,
                owner=None,
                message=mailing.message,
            )

        mailing.total_sent += total_sent
        mailing.successful_sends += successful_sends
        mailing.failed_sends += failed_sends

        if mailing.first_sent_at is None:
            mailing.first_sent_at = timezone.now()

        mailing.save()
        mailing.update_status()

        self.stdout.write(
            self.style.SUCCESS(f"Рассылка с ID {mailing_id} успешно отправлена.")
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Всего отправлено: {total_sent}, успешных отправок: {successful_sends}, неуспешных: {failed_sends}."
            )
        )
