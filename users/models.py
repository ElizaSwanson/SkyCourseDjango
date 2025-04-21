from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        unique=True, verbose_name="Email", help_text="Введите свой email"
    )
    username = models.CharField(
        max_length=100, verbose_name="Имя пользователя", blank=True, null=True
    )
    phone = models.CharField(
        max_length=20, verbose_name="Номер телефона", blank=True, null=True
    )
    avatar = models.ImageField(
        upload_to="users/avatars/", verbose_name="Аватар", null=True, blank=True
    )
    country = models.CharField(
        max_length=100, verbose_name="Страна", blank=True, null=True
    )
    is_blocked = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email
