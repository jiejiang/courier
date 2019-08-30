from __future__ import unicode_literals
import os
from django.core.validators import MinValueValidator

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from mezzanine.conf import settings

waybill_file_storage = FileSystemStorage(location=settings.WAYBILL_STORAGE_LOCATION)


class Profile(models.Model):
    user = models.OneToOneField("auth.User", related_name="_api_profile")
    can_use_api = models.BooleanField(null=False, blank=False, default=False)
    api_test_mode = models.BooleanField(null=False, blank=False, default=False)


class Route(models.Model):
    code = models.CharField(max_length=64, blank=False, null=False, unique=True, db_index=True)
    name = models.CharField(max_length=128, blank=False, null=False, unique=True)
    is_enabled = models.BooleanField(default=True, null=False, blank=False)

    def __unicode__(self):
        return self.name


class Request(models.Model):
    class StatusCode:
        CREATED = 0
        SUBMIT_RETRY = 50
        SUBMITTED = 100
        RETRIEVE_RETRY = 150
        RETRIEVE_FAILED = 175
        SUCCEEDED = 200
        FAILED = 300

    owner = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True)
    request_no = models.CharField(max_length=64, null=True, blank=True, unique=True, db_index=True)
    creation_date = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    status_code = models.IntegerField(blank=False, null=False, default=StatusCode.CREATED, db_index=True)
    message = models.TextField(null=True, blank=True)
    last_retry = models.DateTimeField(null=True, blank=True)

    uuid = models.CharField(_(u"UUID"), max_length=64, null=True, blank=True, unique=True, db_index=True)
    system = models.CharField(_("System Name"), max_length=32, db_index=True, null=True, blank=True)
    test_mode = models.BooleanField(null=False, blank=True, default=False)

    external_order_no = models.CharField(max_length=64, null=True, blank=True, default=None)

    @property
    def status(self):
        if self.status_code < Request.StatusCode.SUBMITTED:
            return "Created"
        elif Request.StatusCode.SUBMITTED <= self.status_code < Request.StatusCode.SUCCEEDED:
            return "Waiting"
        elif self.status_code == Request.StatusCode.SUCCEEDED:
            return "Succeeded"
        elif self.status_code == Request.StatusCode.FAILED:
            return "Failed"
        else:
            return "N/A"

    @property
    def error_msg(self):
        return self.message if self.status_code == Request.StatusCode.FAILED else None

    @property
    def total_cost(self):
        return self.packages.aggregate(models.Sum('cost'))['cost__sum']

    class Meta:
        ordering = ('-creation_date',)

class Product(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False, db_index=True, unique=True)
    internal_name = models.CharField(max_length=128, blank=True, null=True, unique=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_enabled = models.BooleanField(default=True, null=False, blank=False)
    barcode = models.CharField(max_length=128, blank=False, null=False, db_index=True, unique=True)

    @classmethod
    def find_product(cls, name):
        return Product.objects.filter(internal_name=name).first()


def waybill_upload_to(instance, filename):
    return "waybills/{}/{}/{}".format(instance.request.creation_date.strftime('%Y/%m/%d'), instance.request.request_no,
                                      filename)


class Package(models.Model):
    tracking_no = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    slug = models.CharField(max_length=128, null=True, blank=True, unique=True, db_index=True)
    items = models.ManyToManyField(Product, through='PackageItem')
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="packages")
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    sender_name = models.CharField(max_length=64, null=False, blank=False)
    sender_phone_number = models.CharField(max_length=64, null=False, blank=False)
    sender_address = models.CharField(max_length=256, null=False, blank=False)
    receiver_name = models.CharField(max_length=64, null=False, blank=False)
    receiver_phone_number = models.CharField(max_length=64, null=False, blank=False)
    receiver_address = models.CharField(max_length=256, null=False, blank=False)
    receiver_city = models.CharField(max_length=32, null=False, blank=False)
    receiver_post_code = models.CharField(max_length=32, null=False, blank=False)
    receiver_id_number = models.CharField(max_length=64, null=False, blank=False)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    length = models.IntegerField(validators=[MinValueValidator(1)])
    width = models.IntegerField(validators=[MinValueValidator(1)])
    height = models.IntegerField(validators=[MinValueValidator(1)])

    waybill_file = models.FileField(upload_to=waybill_upload_to, storage=waybill_file_storage, null=True, blank=True)

    external_package_no = models.CharField(max_length=64, null=True, blank=True, default=None)

    @property
    def request_no(self):
        return self.request.request_no

    def __getitem__(self, item):
        if item == 'total_count':
            return PackageItem.objects.filter(package=self).aggregate(models.Sum('count'))['count__sum']
        if item == 'package_items':
            return list(PackageItem.objects.filter(package=self))

    def __setattr__(self, key, value):
        if key == 'tracking_no' and value:
            super(Package, self).__setattr__('slug', "-".join((self.request.request_no, value)))
        super(Package, self).__setattr__(key, value)

    @property
    def items_detail(self):
        return " / ".join("%s x %d" % (package.product.name, package.count) for package in PackageItem.objects.filter(package=self))

    class Meta:
        ordering = ('id',)


class PackageItem(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    count = models.IntegerField(validators=[MinValueValidator(1)])

    def __getitem__(self, item):
        if item == 'count':
            return self.count
        if item == 'product':
            return self.product



