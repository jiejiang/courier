# *- coding: utf-8 -*
import sys, zipfile
from cStringIO import StringIO

from django.db.models import Sum
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, RedirectView, CreateView, DeleteView, TemplateView, View, UpdateView
from django.contrib import messages
from django.http import Http404, StreamingHttpResponse, JsonResponse, HttpResponseRedirect
from wsgiref.util import FileWrapper
from django.views.generic.detail import BaseDetailView, DetailView, SingleObjectMixin
from django.views.generic.edit import BaseDeleteView
from mezzanine.conf import settings

from models import CourierBatch, CourierOrder, Package, Item, get_cn_addresses, Address, Route, Profile, \
    calculate_cost_with_pickup, get_courier_cart_stats
from forms import CourierBatchForm

from courier_systems import download_courier_batch

@method_decorator(login_required, name='dispatch')
class ProfileView(RedirectView):
    url = reverse_lazy("courier_batch")

@method_decorator(login_required, name='dispatch')
class CourierBatchListView(ListView):
    model = CourierBatch
    template_name = "courier_batch/list.html"
    paginate_by = 10

    def get_queryset(self):
        return CourierBatch.objects.filter(user_id=self.request.user.id).order_by('-id')

@method_decorator(login_required, name='dispatch')
class CourierBatchCreateView(CreateView):
    model = CourierBatch
    success_url = reverse_lazy("courier_batch")
    form_class = CourierBatchForm
    template_name = "courier_batch/form.html"

    def get_form_kwargs(self):
        kwargs = super(CourierBatchCreateView, self).get_form_kwargs()
        kwargs.update({
            'user': self.request.user
        })
        return kwargs

    def form_valid(self, form):
        messages.info(self.request, _(u"订单已提交"))
        return super(CourierBatchCreateView, self).form_valid(form)

@method_decorator(login_required, name='dispatch')
class CourierBatchDeleteView(DeleteView):
    model = CourierBatch
    success_url = reverse_lazy("courier_batch")
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        obj = super(CourierBatchDeleteView, self).get_object(queryset)
        if obj.user_id <> self.request.user.id:
            raise Http404
        if obj.state <> CourierBatch.STATUS[2][0]:
            raise Http404
        return obj

    def get(self, request, *args, **kwargs):
        messages.info(self.request, _(u"订单批次已经删除"))
        return self.post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class CourierBatchDownloadView(BaseDetailView):
    model = CourierBatch
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        obj = super(CourierBatchDownloadView, self).get_object(queryset)
        if obj.user_id <> self.request.user.id:
            raise Http404
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        download_file_obj = None
        batch_zipfile = None
        courier_batch = self.object
        try:
            if not courier_batch.system in settings.COURIER_SYSTEMS:
                raise Exception, "System not configured: %s" % courier_batch.system
            system_config = settings.COURIER_SYSTEMS[courier_batch.system]
            if not 'url_base' in system_config or not 'user_name' in system_config or not 'password' in system_config:
                raise Exception, "Invalid system_config: %s" % str(system_config)

            zipped_file_stream = download_courier_batch(system_config['url_base'], system_config['user_name'],
                                            system_config['password'], courier_batch.uuid)
            zipdata = StringIO()
            for data in zipped_file_stream:
                zipdata.write(data)
            batch_zipfile = zipfile.ZipFile(zipdata)
            output_filename = None
            for file_name in batch_zipfile.namelist():
                if file_name.lower().endswith('.pdf'):
                    output_filename = file_name
            if output_filename is None:
                raise Exception, "PDF not found"
            download_file_obj = batch_zipfile.open(output_filename)
            chunk_size = 8192
            response = StreamingHttpResponse(FileWrapper(download_file_obj, chunk_size),
                                             content_type='application/octet-stream')
            response['Content-Length'] = batch_zipfile.getinfo(output_filename).file_size
            response['Content-Disposition'] = "attachment; filename=%s" % output_filename.encode('utf8')

        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            raise Http404
        finally:
            if download_file_obj is not None:
                download_file_obj.close()
            if batch_zipfile is not None:
                batch_zipfile.close()

        return response

