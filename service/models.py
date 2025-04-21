from django.conf import settings
from django.db import models


class Recipient(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        ordering = ["email"]


class Message(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["subject"]


class Mailing(models.Model):
    STATUS_CHOICES = [
        ("Создана", "Создана"),
        ("Запущена", "Запущена"),
        ("Завершена", "Завершена"),
    ]

    first_sent_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Создана")
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    recipients = models.ManyToManyField(Recipient)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    total_sent = models.PositiveIntegerField(default=0)
    successful_sends = models.PositiveIntegerField(default=0)
    failed_sends = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.message.subject} - {self.status}"

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"


class SendAttempt(models.Model):
    STATUS_CHOICES = [("Успешно", "Успешно"), ("Не успешно", "Не успешно")]

    attempt_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    server_response = models.TextField(blank=True)
    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="send_attempts"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, null=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Attempt: {self.attempt_time} - {self.status}"
