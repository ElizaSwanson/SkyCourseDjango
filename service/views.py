import os

from django.shortcuts import redirect, get_object_or_404, render
from django.views import generic
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.utils import timezone

from users.models import User
from .models import Recipient, Message, Mailing, SendAttempt
from .forms import RecipientForm, MessageForm, MailingForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import ListView


@method_decorator(cache_page(0), name="dispatch")
class RecipientListView(LoginRequiredMixin, generic.ListView):
    model = Recipient
    template_name = "recipient_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


class RecipientCreateView(generic.CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "recipient_form.html"
    success_url = reverse_lazy("service:recipient_list")

    def form_valid(self, form):
        recipient = form.save(commit=False)
        recipient.owner = self.request.user
        recipient.save()
        return super().form_valid(form)


class RecipientUpdateView(generic.UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "recipient_form.html"
    success_url = reverse_lazy("service:recipient_list")


class RecipientDeleteView(generic.DeleteView):
    model = Recipient
    template_name = "recipient_confirm_delete.html"
    success_url = reverse_lazy("service:recipient_list")


@method_decorator(cache_page(0), name="dispatch")
class MessageListView(LoginRequiredMixin, generic.ListView):
    model = Message
    template_name = "message_list.html"
    context_object_name = "messages"

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MessageCreateView(generic.CreateView):
    model = Message
    form_class = MessageForm
    template_name = "message_form.html"
    success_url = reverse_lazy("service:message_list")

    def form_valid(self, form):
        message = form.save(commit=False)
        message.owner = self.request.user
        message.save()
        return super().form_valid(form)


class MessageUpdateView(generic.UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "message_form.html"
    success_url = reverse_lazy("service:message_list")


class MessageDeleteView(generic.DeleteView):
    model = Message
    template_name = "servicemessage_confirm_delete.html"
    success_url = reverse_lazy("service:message_list")


@method_decorator(cache_page(0), name="dispatch")
class MailingListView(LoginRequiredMixin, generic.ListView):
    model = Mailing
    template_name = "mailing_list.html"
    context_object_name = "service"

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="manager").exists():
            return Mailing.objects.all()
        else:
            return Mailing.objects.filter(owner=user)


class MailingCreateView(generic.CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_form.html"
    success_url = reverse_lazy("service:mailing_list")

    def get_form_kwargs(self):
        kwargs = super(MailingCreateView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        mailing = form.save(commit=False)
        mailing.owner = self.request.user
        mailing.save()
        return super().form_valid(form)


class MailingUpdateView(generic.UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_form.html"
    success_url = reverse_lazy("service:mailing_list")

    def get_form_kwargs(self):
        kwargs = super(MailingUpdateView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        mailing = form.save(commit=False)
        mailing.owner = self.request.user
        existing_end_at = self.get_object().end_at
        new_end_at = form.cleaned_data.get("end_at")

        if existing_end_at != new_end_at:
            mailing.status = "Запущена"

        mailing.save()
        return super().form_valid(form)


class MailingDeleteView(generic.DeleteView):
    model = Mailing
    template_name = "mailing_confirm_delete.html"
    success_url = reverse_lazy("service:mailing_list")


class SendMailingView(generic.View):
    def get_object(self, mailing_id):
        return get_object_or_404(Mailing, id=mailing_id)

    def post(self, request, mailing_id):
        mailing = self.get_object(mailing_id)
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
                owner=request.user,
                message=mailing.message,
            )

        mailing.total_sent += total_sent
        mailing.successful_sends += successful_sends
        mailing.failed_sends += failed_sends
        mailing.save()

        if mailing.status == "Создана":
            mailing.status = "Запущена"
            mailing.first_sent_at = timezone.now()
            mailing.save()

        if mailing.end_at and timezone.now() > mailing.end_at:
            mailing.status = "Завершена"
            mailing.save()

        return render(request, "mailing_status.html", {"service": mailing})


class HomeView(generic.TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not user.is_authenticated or user.groups.filter(name="manager").exists():
            context["total_mailings"] = Mailing.objects.count()
            context["active_mailings"] = Mailing.objects.filter(
                status="Запущена"
            ).count()
            context["unique_recipients"] = (
                Recipient.objects.values("email").distinct().count()
            )
        else:
            context["successful_attempts"] = SendAttempt.objects.filter(
                owner=user, status="Успешно"
            ).count()
            context["failed_attempts"] = SendAttempt.objects.filter(
                owner=user, status="Не успешно"
            ).count()
            context["sent_messages"] = SendAttempt.objects.filter(owner=user).count()

        return context


class UsersView(generic.TemplateView):
    template_name = "list_users.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = User.objects.exclude(groups__name="manager")
        return context


class UserActionView(generic.View):

    def post(self, request, user_id, action):
        user = get_object_or_404(User, id=user_id)
        if action == "block":
            user.is_blocked = True
        elif action == "unblock":
            user.is_blocked = False
        user.save()
        return redirect("service:list_users")

class MailListViewStatus(LoginRequiredMixin,generic.ListView):
    model = Mailing
    template_name = "attempts.html"
    context_object_name = "mailing"

    def get_queryset(self):
        if self.request.user.has_perm("mailing.can_view_all_mailing_lists"):
            return Mailing.objects.all()
        return Mailing.objects.filter(created_by=self.request.user)