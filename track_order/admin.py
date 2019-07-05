# *- coding: utf-8 -*
from django.utils.translation import ugettext as _
from django.contrib import admin

from models import ParcelForceOrder

class ParceForceOrderAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'receiver_name', 'receiver_phone', 'dispatch_date', 'filename')
    search_fields = ('reference_number', 'receiver_name', 'receiver_phone')
    fields = ('reference_number', 'receiver_name', 'receiver_phone', 'dispatch_date')

admin.site.register(ParcelForceOrder, ParceForceOrderAdmin)

