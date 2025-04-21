from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.views.generic import UpdateView
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render

from users.forms import UserRegistrationForm, UserProfileForm
from users.models import User


class UserCreateView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = "register_form.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        token = default_token_generator.make_token(user)
        self.send_confirmation_email(user, token)

        messages.success(
            self.request,
            "Регистрация прошла успешно! Пожалуйста,"
            " проверьте свою электронную почту для активации учетной записи.",
        )
        return HttpResponseRedirect(self.success_url)

    def send_confirmation_email(self, user, token):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        current_site = get_current_site(self.request)
        mail_subject = "Активируйте свой аккаунт"

        activation_link = (
            f"http://{current_site.domain}"
            f"{reverse('activate', kwargs={'uidb64': uid, 'token': token})}"
        )

        message = render_to_string(
            "activation_email.html",
            {
                "user": user,
                "activation_link": activation_link,
            },
        )
        email = EmailMultiAlternatives(mail_subject, message, to=[user.email])
        email.send()


class ActivateView(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return render(request, "activation_complete.html")
            else:
                return render(request, "activation_invalid.html")
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return render(request, "activation_invalid.html")


class CustomLoginView(LoginView):
    template_name = "login.html"

    def get_success_url(self):
        return reverse("service:home")


class UserProfileUpdateView(UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "profile_form.html"
    success_url = reverse_lazy("service:home")

    def get_object(self, queryset=None):
        return self.request.user

