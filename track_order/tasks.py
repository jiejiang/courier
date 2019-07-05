# *- coding: utf-8 -*
from __future__ import absolute_import
from django.utils.translation import ugettext as _
import datetime, sys
from celery import shared_task
from django.db import transaction

from .models import ParcelForceImportJob, ParcelForceOrder
from .parcel_force import extract_order_info

@shared_task
def import_parcel_force_orders(job_id):
    #print job_id
    job = ParcelForceImportJob.objects.get(id=job_id)
    def callback(percentage):
        job.percentage = float(percentage)
        job.save()

    reference_number = None
    try:
        info = extract_order_info(job.input_file, callback)
        with transaction.atomic():
            job.pages = info['num_pages']
            for order_info in info['order_info']:
                reference_number = order_info['reference_number']
                order = ParcelForceOrder(reference_number=order_info['reference_number'],
                                         receiver_name=order_info['name'],
                                         receiver_phone=order_info['telephone'],
                                         dispatch_date=order_info['dispatch_date'],
                                         import_job=job)
                order.save()
            job.state = ParcelForceImportJob.STATUS[1][0]
            job.save()
    except Exception, inst:
        import traceback
        traceback.print_exc(sys.stderr)
        job.state = ParcelForceImportJob.STATUS[2][0]
        job.message = ("%s: " % reference_number if reference_number else "") + inst.message.encode('utf-8')
        job.save()
    finally:
        job.input_file.delete()


