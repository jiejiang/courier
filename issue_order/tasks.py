# *- coding: utf-8 -*
from __future__ import absolute_import
from django.utils.translation import ugettext as _
import datetime, sys
from celery import shared_task
from django.db import transaction
from mezzanine.conf import settings

from .models import CourierBatch, Profile
from .courier_systems import query_courier_batch

@shared_task
def sample_task():
    print settings.COURIER_SYSTEMS
    print CourierBatch.objects.filter(state=CourierBatch.STATUS[0][0]).all()


@shared_task
def sync_waiting_courier_batches():
    for courier_batch in CourierBatch.objects.filter(state=CourierBatch.STATUS[0][0]):
        try:
            if not courier_batch.system in settings.COURIER_SYSTEMS:
                raise Exception, "System not configured: %s" % courier_batch.system
            system_config = settings.COURIER_SYSTEMS[courier_batch.system]
            if not 'url_base' in system_config or not 'user_name' in system_config or not 'password' in system_config:
                raise Exception, "Invalid system_config: %s" % str(system_config)

            batch_obj = query_courier_batch(system_config['url_base'], system_config['user_name'],
                                               system_config['password'], courier_batch.uuid)
            if batch_obj['status'] == "Waiting":
                courier_batch.status = _(u"等待中")
            elif batch_obj['status'] == "Processing":
                courier_batch.status = _(u"处理中")
            elif batch_obj['status'] == "Completed":
                courier_batch.state, courier_batch.status = CourierBatch.STATUS[1]
            elif batch_obj['status'] == "Failed":
                courier_batch.state, courier_batch.status = CourierBatch.STATUS[2]
                if courier_batch.credit is not None:
                    with transaction.atomic():
                        profile = Profile.objects.select_for_update().get(user=courier_batch.user)
                        profile.credit += courier_batch.credit
                        profile.save()
                        courier_batch.credit = 0
            elif batch_obj['status'] == "Deleted":
                courier_batch.state, courier_batch.status = CourierBatch.STATUS[3]
            else:
                raise Exception, "Batch obj status invalid: %s" % str(batch_obj)

            courier_batch.percentage = batch_obj['percentage']
            courier_batch.message = batch_obj['message']

            courier_batch.save()
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            print >> sys.stderr, "Failed to sync batch: %s" % courier_batch.uuid