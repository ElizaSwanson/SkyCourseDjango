from django.contrib.auth.forms import UserCreationForm
from users.models import User
from django import forms


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "password1", "password2"]


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "phone", "avatar", "country"]
