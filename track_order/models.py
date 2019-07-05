# *- coding: utf-8 -*
from __future__ import unicode_literals
from django.contrib.postgres.fields import JSONField
import os
from django.utils.translation import ugettext_lazy as _
from django.db import models

from validators import validate_file_extension

class ParcelForceImportJob(models.Model):
    STATUS = (
        (0, _(u"等待")),
        (1, _(u"成功")),
        (2, _(u"失败")),
    )
    user = models.ForeignKey("auth.User", related_name="parcel_force_import_jobs")
    creation_time = models.DateTimeField(_("Creation Time"), auto_now_add=True, null=True, blank=True)
    percentage = models.DecimalField(_("Percentage"), null=True, blank=True, max_digits=5, decimal_places=2, default=0)
    state = models.IntegerField(_("State"), null=False, blank=False, db_index=True, choices=STATUS, default=STATUS[0][0])
    input_file = models.FileField(_("Import File"), upload_to="uploads/parcel_force_imports/%Y/%m/%d",
                                  validators=[validate_file_extension,])
    pages = models.IntegerField(_("Num of Pages"), null=True, blank=True)
    message = models.TextField(_("Message"), null=True, blank=True)
    filename = models.CharField(_("Input File Name"), null=True, blank=True, max_length=100)

    @property
    def status(self):
        return ParcelForceImportJob.STATUS[self.state][1]


class ParcelForceOrder(models.Model):
    reference_number = models.CharField(_(u"Reference Number"), max_length=64, null=False, blank=False, unique=True,
                                        db_index=True)
    receiver_name = models.CharField(_(u"Receiver Name"), max_length=32, null=False, blank=False, db_index=True)
    receiver_phone = models.CharField(_(u"Receiver Phone"), max_length=32, null=False, blank=False, db_index=True)
    dispatch_date = models.DateTimeField(_("Dispatch Date"), auto_now_add=False, null=False, blank=False)
    import_job = models.ForeignKey(ParcelForceImportJob, related_name="orders", null=True, blank=True)

    @property
    def filename(self):
        return self.import_job.filename if self.import_job else ''


class ShippingRecord(models.Model):
    class Status:
        CREATED = 0
        FAKE_DEPARTURE = 10
        DEPARTURE = 100
        ARRIVED = 200

    order_number = models.CharField(max_length=128, unique=True, null=False, blank=False, db_index=True)
    status = models.IntegerField(db_index=True, null=False, blank=False, default=Status.CREATED)
    route = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    creation_time = models.DateTimeField(null=True, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    landed_time = models.DateTimeField(null=True, blank=True)
    custom_clearance_time = models.DateTimeField(null=True, blank=True)
    agent_query_time = models.DateTimeField(null=True, blank=True)
    agent_query_fault_time = models.DateTimeField(null=True, blank=True)
    agent_query_count = models.IntegerField(default=0)
    agent_query_result = JSONField(null=True, blank=True)



