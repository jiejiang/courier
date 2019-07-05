from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from mezzanine.core.admin import TabularDynamicInlineAdmin

from order_api.models import Product, Request, Profile, Package, PackageItem

def api_profile(self):
    if not hasattr(self, '_api_profile'):
        self._api_profile = Profile.objects.create(user=self)
        self._api_profile.save()
    return self._api_profile

User.api_profile = property(lambda self: api_profile(self))

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'internal_name', 'unit_price', 'is_enabled')


class PackageAdmin(TabularDynamicInlineAdmin):
    model = Package
    ordering = ('id',)
    fields = ('tracking_no', 'cost', 'sender_name', 'sender_phone_number', 'sender_address', 'receiver_name',
              'receiver_phone_number', 'receiver_address', 'receiver_city', 'receiver_post_code', 'receiver_id_number',
              'items_detail')

    def get_readonly_fields(self, request, obj=None):
        return self.fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RequestAdmin(admin.ModelAdmin):
    inlines = (PackageAdmin, )

    list_display = ('request_no', 'creation_date', 'owner', 'status', 'system', 'test_mode', 'total_cost')

    readonly_fields = ['total_cost', 'status']

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + \
               [field.name for field in obj._meta.fields] + \
               [field.name for field in obj._meta.many_to_many]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Product, ProductAdmin)
admin.site.register(Request, RequestAdmin)
