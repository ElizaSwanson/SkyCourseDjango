from django import forms
from .models import Recipient, Message, Mailing


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ["email", "full_name", "comment"]


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["subject", "body"]


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["end_at", "message", "recipients"]

    recipients = forms.ModelMultipleChoiceField(
        queryset=Recipient.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    message = forms.ModelChoiceField(queryset=Message.objects.none(), required=True)

    def __init__(self, user=None, *args, **kwargs):
        super(MailingForm, self).__init__(*args, **kwargs)

        if user is not None and user.groups.filter(name="manager").exists() is False:
            # Фильтруем получателей по текущему владельцу
            self.fields["recipients"].queryset = Recipient.objects.filter(owner=user)

            # Фильтруем сообщения по текущему владельцу
            self.fields["message"].queryset = Message.objects.filter(owner=user)
