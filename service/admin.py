from django.contrib import admin

from .models import Recipient, Message, Mailing, SendAttempt

admin.site.register(Recipient)
admin.site.register(Mailing)
admin.site.register(SendAttempt)
admin.site.register(Message)
