from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Participants)
admin.site.register(ParticipantCard)
admin.site.register(UserAccount)
admin.site.register(QRcode)
admin.site.register(Certificates)


