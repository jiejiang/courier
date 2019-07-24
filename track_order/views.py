# *- coding: utf-8 -*

from django.utils.translation import ugettext as _

import sys, requests, os, datetime, random, pytz

from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, TemplateView, DeleteView, CreateView
from django.views.generic.edit import FormView, FormMixin
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from mezzanine.conf import settings
from django.views.decorators.csrf import csrf_exempt

from forms import QueryOrderForm, format_parcel_force_import_job_create_form, TrackShippingForm
from models import ParcelForceImportJob, ParcelForceOrder, ShippingRecord
from tasks import import_parcel_force_orders

from track_order.tracking import query_tracking_info, DBError


class QueryOrderView(TemplateView):
    form_class = QueryOrderForm

    initial = {}
    prefix = None

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(form=self.get_form()), template_name="query_order.html")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        return self.initial.copy()

    def get_prefix(self):
        """
        Returns the prefix to use for forms on this view
        """
        return self.prefix

    def get_form_class(self):
        """
        Returns the form class to use in this view
        """
        return self.form_class

    def get_form(self, form_class=None):
        """
        Returns an instance of the form to be used in this view.
        """
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def render_to_response(self, context, template_name, **response_kwargs):
        return self.response_class(
            request=self.request,
            template=template_name,
            context=context,
            using=self.template_engine,
            **response_kwargs
        )

    def form_invalid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data(form=form), template_name="query_order.html")


    def form_valid(self, form):
        route = form.cleaned_data['route']
        if route == 'order_system':
            orders, data = self.__query_order_system(form)
        elif route == 'parcel_force':
            orders, data = self.__query_parcel_force(form)
        else:
            raise Http404
        return self.render_to_response(self.get_context_data(query=data, orders=orders, route=route),
                                       template_name="order_list.html")

    def __query_parcel_force(self, form):
        mobile = form.cleaned_data['mobile']
        days = int(form.cleaned_data['days'])
        since_date = datetime.datetime.combine(timezone.now() - datetime.timedelta(days=days), datetime.time.min)
        orders = ParcelForceOrder.objects.filter(receiver_phone=mobile, dispatch_date__gte=since_date)\
            .order_by('-dispatch_date')
        data = {
            'mobile': [mobile,],
            'days': days
        }
        return orders, data

    def __query_order_system(self, form):
        name = form.cleaned_data['name']
        mobile = form.cleaned_data['mobile']
        id = form.cleaned_data['id']
        data = {}
        if id:
            data['id'] = [id,]
        else:
            data['name_mobile'] = ["|".join((name.replace('|', ''), mobile.replace('|', ''))),]
        data['days'] = form.cleaned_data['days']
        orders = []

        print >> sys.stderr, timezone.now(), "querying with:", data
        for system_name, system_config in settings.COURIER_SYSTEMS.iteritems():
            url = system_config['url_base'] + "/api/v1.0/order"
            auth = (system_config['user_name'], system_config['password'])
            json = self.__remote_query(url, data, auth)
            print >> sys.stderr, timezone.now(), system_name, "returned with:", json
            if json:
                orders.extend(json)
        for order in orders:
            order['usedTime'] = parse_datetime(order['usedTime'])
        orders = sorted(orders, key=lambda x:x['usedTime'], reverse=True)
        return orders, data

    def __remote_query(self, url, data, auth):
        response = requests.get(url, data=data, auth=auth)
        ret = []
        json = None
        try:
            json = response.json()
        except Exception, inst:
            print >> sys.stderr, str(inst)
        if json is not None:
            if 'message' in json:
                messages.add_message(self.request, messages.ERROR, _(u"系统错误, 请联系客服: ") + str(json['message']))
            else:
                ret = json
        else:
            messages.add_message(self.request, messages.ERROR, _(u"连接错误, 请联系客服!"))

        return ret

@method_decorator(staff_member_required(login_url='login'), name='dispatch')
class ParcelForceImportJobListView(ListView):
    model = ParcelForceImportJob
    template_name = "parcel_force_import_job/list.html"
    paginate_by = 10
    ordering = ('-id',)


@method_decorator(staff_member_required(login_url='login'), name='dispatch')
class ParcelForceImportJobCreateView(CreateView):
    model = ParcelForceImportJob
    template_name = "parcel_force_import_job/form.html"
    fields = ('input_file', )
    success_url = reverse_lazy("parcel_force_import_job")

    def get_form(self, form_class=None):
        form = super(ParcelForceImportJobCreateView, self).get_form(form_class)
        form = format_parcel_force_import_job_create_form(form)
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.filename = os.path.basename(form.instance.input_file.name)
        response = super(ParcelForceImportJobCreateView, self).form_valid(form)
        import_parcel_force_orders.delay(form.instance.id)
        return response


@method_decorator(staff_member_required(login_url='login'), name='dispatch')
class ParcelForceImportJobDeleteView(DeleteView):
    model = ParcelForceImportJob
    success_url = reverse_lazy("parcel_force_import_job")

    def get_object(self, queryset=None):
        obj = super(ParcelForceImportJobDeleteView, self).get_object(queryset)
        if obj.state <> ParcelForceImportJob.STATUS[2][0]:
            raise Http404
        return obj

    def get(self, request, *args, **kwargs):
        messages.info(self.request, _(u"上传记录已经删除"))
        return self.post(request, *args, **kwargs)


@method_decorator(staff_member_required(login_url='login'), name='dispatch')
class ParcelForceOrderListView(ListView):
    model = ParcelForceOrder
    template_name = "parcel_force_order/list_by_job.html"
    paginate_by = 100

    def get_queryset(self):
        return ParcelForceOrder.objects.filter(import_job__id=self.kwargs['job_id']).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super(ParcelForceOrderListView, self).get_context_data(**kwargs)
        context['job'] = get_object_or_404(ParcelForceImportJob, pk=self.kwargs['job_id'])
        context['return_url'] = self.request.GET.get('return', reverse_lazy("parcel_force_import_job"))
        return context


@method_decorator(never_cache, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class TrackShippingView(FormView):
    template_name = "track_shipping.html"
    success_url = "track_shipping"
    form_class = TrackShippingForm

    def form_valid(self, form):
        order_number = form.cleaned_data['order_number']
        context = {
            'order_number': order_number
        }
        try:
            now = timezone.now()
            record, agent_items = query_tracking_info(order_number, now)
            context['agent_items'] = agent_items
            context['now'] = now
            context['record'] = record
            context['show_content'] = True
        except DBError, inst:
            context['message'] = _(u"系统繁忙, 请稍后再试!")
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            context['message'] = inst.message
        return self.render_to_response(self.get_context_data(**context))


class ParcelInfoView(TemplateView):
    template_name = "parcelinfo.html"
