# *- coding: utf-8 -*
from django.utils.translation import ugettext as _
import sys, os, datetime, traceback, zipfile, json, PyPDF2
from wsgiref.util import FileWrapper
from urllib2 import URLError
from celery import shared_task
from django.db import transaction
from django.core.mail import EmailMessage
from django.db.models import Q
from django.utils import timezone
from mezzanine.conf import settings
from cStringIO import StringIO
from celery.utils.log import get_task_logger
from mezzanine.conf import settings
from openpyxl import Workbook
from requests import ConnectionError

logger = get_task_logger(__name__)

from order_api.models import Request, PackageItem
from issue_order.courier_systems import create_courier_batch, query_courier_batch, download_courier_batch
from issue_order.models import Profile

def mark_request_status(job, status_code, timestamp=timezone.now(), message=None, save=True):
    job.status_code = status_code
    job.last_retry = timestamp
    job.message = str(message)
    if save:
        job.save()

def get_system_config(system):
    system_config = settings.COURIER_SYSTEMS[system]
    if not 'url_base' in system_config or not 'user_name' in system_config or not 'password' in system_config:
        raise Exception(_(u"线路配置错误，联系客服"))
    return system_config

def submit_request(request, timestamp=timezone.now(), save=True):
    system = settings.API_SYSTEM
    system_config = get_system_config(system)

    file_obj = StringIO()
    wb = Workbook()
    ws = wb.active
    ws.append([u"发件人名字", u"发件人电话号码", u"发件人地址",
               u"收件人名字（中文）", u"收件人手机号（11位数）", u"收件人地址（无需包括省份和城市）",
               u"收件人城市（中文）", u"收件人邮编", u"身份证号(EMS需要)",
               u"包裹数量", u"包裹重量（公斤）", u"长（厘米）", u"宽（厘米）", u"高（厘米）", u"EXTERNAL_PACKAGE_NO",
               u"申报物品1(英文）", u"数量", u"物品单价（英镑）",
               u"申报物品2(英文）", u"数量", u"物品单价（英镑）",
               u"申报物品3(英文）", u"数量", u"物品单价（英镑）",
               u"申报物品4(英文）", u"数量", u"物品单价（英镑）",
               u"申报物品5(英文）", u"数量", u"物品单价（英镑）",
               u"申报物品6(英文）", u"数量", u"物品单价（英镑）", ])
    for package in request.packages.order_by('id'):
        row = [package.sender_name, package.sender_phone_number, package.sender_address,
               package.receiver_name, package.receiver_phone_number, package.receiver_address,
               package.receiver_city, package.receiver_post_code, package.receiver_id_number,
               package.items.count(), package.weight, package.length, package.width, package.height,
               (package.external_package_no if package.external_package_no else '')]
        for item in PackageItem.objects.filter(package=package).order_by('id'):
            row.extend([item.product.internal_name if item.product.internal_name else item.product.name,
                        item.count, item.product.unit_price])
        ws.append(row)
    wb.save(file_obj)

    uuid = create_courier_batch(system_config['url_base'], system_config['user_name'],
                                system_config['password'], file_obj,
                                " | ".join(filter(lambda x: x, ("API", request.owner.username, request.owner.last_name,
                                                                request.owner.first_name, request.owner.email))),
                                filename=request.request_no + '.xlsx',
                                test_mode=request.test_mode,
                                route=(request.route.code if request.route else None),
                                external_order_no=(request.external_order_no if request.external_order_no else None))
    request.uuid = uuid
    request.system = system
    request.status_code = Request.StatusCode.SUBMITTED
    request.message = None

    if save:
        request.save()

def restore_credit(request):
    if not request.test_mode:
        total_cost = request.total_cost
        if request.total_cost > 0:
            with transaction.atomic():
                profile = Profile.objects.select_for_update().get(user=request.owner)
                profile.credit += total_cost
                profile.save()
            logger.error("Credit Restored: request %s, user(%d), %f" % (request.request_no, request.owner.id, total_cost))

def retrieve_request(request, timestamp=timezone.now(), save=True):
    if not request.uuid:
        raise Exception, "Cannot retrieve request without uuid"
    system_config = get_system_config(request.system)
    batch_obj = query_courier_batch(system_config['url_base'], system_config['user_name'],
                                    system_config['password'], request.uuid)

    if batch_obj['status'] == "Waiting":
        pass
    elif batch_obj['status'] == "Processing":
        pass
    elif batch_obj['status'] == "Completed":
        zipped_file_stream = download_courier_batch(system_config['url_base'], system_config['user_name'],
                                                    system_config['password'], request.uuid)
        zipdata = StringIO()
        for data in zipped_file_stream:
            zipdata.write(data)
        batch_zipfile = zipfile.ZipFile(zipdata)
        pdf_filename = None
        json_filename = None
        for file_name in batch_zipfile.namelist():
            if file_name.lower().endswith('.pdf'):
                pdf_filename = file_name
            elif file_name.lower().endswith('.json'):
                json_filename = file_name
        if pdf_filename is None:
            raise Exception, "PDF not found"
        if json_filename is None:
            raise Exception, "Json not found"
        with batch_zipfile.open(json_filename) as f:
            waybills = json.load(f)
        if len(waybills) <> request.packages.count():
            raise Exception, "Waybill length %d mismatch package number %d" % (len(waybills), request.package.count())
        pdf_data = StringIO(batch_zipfile.open(pdf_filename).read())
        pdf_data.seek(0)
        pdf = PyPDF2.PdfFileReader(pdf_data)
        page_count = pdf.getNumPages()
        for package, waybill in zip(request.packages.order_by('id'), waybills):
            if waybill['end_page'] > page_count or waybill['start_page'] >= page_count:
                raise Exception, "Waybill page length %d-%d larger than pdf length %d" % \
                                 (waybill['start_page'], waybill['end_page'], page_count)
            out_pdf = PyPDF2.PdfFileWriter()
            for i in xrange(waybill['start_page'], waybill['end_page']):
                out_pdf.addPage(pdf.getPage(i))

            package.tracking_no = waybill['tracking_no']
            file_obj = StringIO()
            out_pdf.write(file_obj)
            file_obj.seek(0)
            if save:
                package.waybill_file.delete()
                package.waybill_file.save(package.tracking_no + '.pdf', file_obj)
                package.save()
        request.status_code = Request.StatusCode.SUCCEEDED
    elif batch_obj['status'] == "Failed":
        request.status_code = Request.StatusCode.FAILED
        restore_credit(request)
    else:
        raise Exception, "API Batch obj status invalid: %s" % str(batch_obj)

    request.message = batch_obj['message']
    if save:
        request.save()

def email_notify_failed(request, message=None):
    msg = EmailMessage(
        'API Request {} Failed'.format(request.request_no),
        """
        Dear User:<br><br>
        Reques <b>{}</b> failed with message:<br><br>
        {}<br><br>
        """.format(request.request_no, message),
        bcc=['contact@cnexpress.co.uk'],
    )
    msg.content_subtype = "html"
    msg.send()

@shared_task
def sync_api_requests():
    now = timezone.now()
    retrieve_before = now - datetime.timedelta(minutes=1)
    retry_before = now - datetime.timedelta(minutes=5)

    for request in Request.objects.filter(Q(status_code=Request.StatusCode.CREATED) |
            (Q(status_code=Request.StatusCode.SUBMIT_RETRY) &
                 (Q(last_retry__isnull=True) | Q(last_retry__lt=retry_before)))).order_by('id'):
        logger.warning("Submit request: %s" % request.request_no)
        try:
            submit_request(request, timestamp=now)
        except ConnectionError, inst:
            logger.exception("ConnectionError Submit request: %s" % request.request_no)
            mark_request_status(request, Request.StatusCode.SUBMIT_RETRY, timestamp=now, message=inst)
        except Exception, inst:
            logger.exception("Failed Submit request: %s" % request.request_no)
            mark_request_status(request, Request.StatusCode.FAILED, timestamp=now, message=inst)
            restore_credit(request)


    for request in Request.objects.filter(
                    (Q(status_code=Request.StatusCode.SUBMITTED) &
                         (Q(last_retry__isnull=True) | Q(last_retry__lt=retrieve_before))) |
                    (Q(status_code=Request.StatusCode.RETRIEVE_RETRY) &
                         (Q(last_retry__isnull=True) | Q(last_retry__lt=retry_before)))).order_by('id'):
        logger.warning("Retrieve request: %s" % request.request_no)
        try:
            retrieve_request(request, timestamp=now)
        except ConnectionError, inst:
            logger.exception("ConnectionError Retrieve request: %s" % request.request_no)
            mark_request_status(request, Request.StatusCode.RETRIEVE_RETRY, timestamp=now, message=inst)
        except Exception, inst:
            logger.exception("Failed Retrieve request: %s" % request.request_no)
            mark_request_status(request, Request.StatusCode.RETRIEVE_FAILED, timestamp=now, message=inst)
            email_notify_failed(request, inst)
