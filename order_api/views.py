# *- coding: utf-8 -*
import urllib, PyPDF2, sys, os, json
from cStringIO import StringIO
from wsgiref.util import FileWrapper

from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.http.response import StreamingHttpResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from issue_order.models import Profile
from rest_framework import viewsets, permissions
from order_api.models import Product, Request, PackageItem, Package
from order_api.serializers import ProductSerializer, RequestSerializer, PackageSerializer, WaybillSerializer
from order_api.permissions import IsApiUser, IsPackageOwner, IsRequestOwner
from rest_framework.exceptions import APIException, status, NotFound, ParseError, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from issue_order.courier_systems import list_cities, get_user_prices, calculate_package_price
from order_api.tasks import get_system_config
from track_order.tracking import query_tracking_info, DBError


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class URLConfMixin(object):
    def dispatch(self, request, *args, **kwargs):
        request.urlconf = "order_api.urls"
        return super(URLConfMixin, self).dispatch(request, *args, **kwargs)


class ProductViewSet(URLConfMixin,
                     viewsets.mixins.ListModelMixin,
                     viewsets.mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    queryset = Product.objects.exclude(is_enabled=False).order_by('name')
    serializer_class = ProductSerializer
    permission_classes = (permissions.IsAuthenticated, IsApiUser,)
    lookup_field = "barcode"
    lookup_value_regex = r"[\w\-]+"


class RequestViewSet(URLConfMixin,
                     viewsets.mixins.CreateModelMixin,
                     viewsets.mixins.RetrieveModelMixin,
                     viewsets.mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = RequestSerializer
    permission_classes = (permissions.IsAuthenticated, IsApiUser, IsRequestOwner)
    lookup_field = "request_no"
    lookup_value_regex = r"[\w\-]+"
    pagination_class = Pagination

    def get_queryset(self):
        return Request.objects.filter(owner=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        system = settings.API_SYSTEM
        try:
            data = serializer.validated_data

            prices = get_user_prices(self.request.user, system)
            if not prices:
                raise APIException(_(u"价格未配置"), code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            with transaction.atomic():
                packages = data.pop('packages')
                serializer.save(owner=self.request.user, test_mode=self.request.user.api_profile.api_test_mode)
                for i, _package in enumerate(packages):
                    packageitem_set = _package.pop('packageitem_set')
                    package = Package.objects.create(request=serializer.instance, **_package)
                    for j, item in enumerate(packageitem_set):
                        if not 'product' in item:
                            raise ValidationError, _(u"第%d个包裹第%d个产品信息无效" % (i+1, j+1))
                        if 'barcode' in item['product']:
                            product = get_object_or_404(Product, barcode=item['product']['barcode'])
                        elif 'name' in item['product']:
                            product = get_object_or_404(Product, name=item['product']['name'])
                        else:
                            raise ValidationError, _(u"第%d个包裹第%d个产品barcode或者name信息无效" % (i+1, j+1))
                        PackageItem.objects.create(product=product, package=package, count=item['count'])

                    try:
                        package.cost = calculate_package_price(prices, package)
                    except Exception, inst:
                        raise APIException(detail=_(u"第%d个包裹异常: %s" % (i+1, inst.message)))
                    package.save()

                total_cost = serializer.instance.total_cost
                if total_cost < 0:
                    raise APIException, _(u"无效订单费用£%.2f" % total_cost)
                #charge if not in test mode
                if not serializer.instance.test_mode and total_cost > 0:
                    if self.request.user.profile.credit < total_cost:
                        raise APIException, _(u"余额(£%.2f)不足订单费用£%.2f" % (self.request.user.profile.credit, total_cost))

                    profile = Profile.objects.select_for_update().get(user=self.request.user)
                    if profile.credit < total_cost:
                        raise APIException, _(u"余额(£%.2f)不足订单费用£%.2f" % (profile.credit, total_cost))
                    profile.credit -= total_cost
                    profile.save()

                serializer.instance.request_no = "".join(
                    (getattr(settings, "REQUEST_ID_PREFIX", ""),
                     timezone.localtime(serializer.instance.creation_date).strftime('%Y%m%d'),
                     str(serializer.instance.id).zfill(8))
                )
                serializer.instance.save()

        except Exception, inst:
            if not isinstance(inst, APIException):
                import traceback
                traceback.print_exc(sys.stderr)
                raise APIException(detail={'detail': 'Server Internal Error'},
                                   code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            raise inst


class PackageViewSet(URLConfMixin,
                     viewsets.ReadOnlyModelViewSet):
    serializer_class = PackageSerializer
    permission_classes = (permissions.IsAuthenticated, IsApiUser, IsPackageOwner)
    lookup_field = "slug"
    lookup_value_regex = r"[\w\-]+"
    pagination_class = Pagination

    def get_queryset(self):
        return Package.objects.filter(request__owner=self.request.user).exclude(tracking_no__isnull=True).order_by('-id')


class WaybillViewSet(URLConfMixin,
                     viewsets.ReadOnlyModelViewSet):
    serializer_class = WaybillSerializer
    permission_classes = (permissions.IsAuthenticated, IsApiUser, IsPackageOwner)
    lookup_field = "slug"
    lookup_value_regex = r"[\w\-]+"
    pagination_class = Pagination

    def get_queryset(self):
        return Package.objects.filter(request__owner=self.request.user).exclude(tracking_no__isnull=True).order_by('-id')

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception, inst:
            raise inst
        response = StreamingHttpResponse(FileWrapper(instance.waybill_file, 8192), content_type='application/octet-stream')
        response['Content-Length'] = instance.waybill_file.size
        response['Content-Disposition'] = "attachment; filename=%s" % urllib.quote(instance.slug + '.pdf')
        return response


class RequestWaybillViewSet(URLConfMixin,
                            viewsets.mixins.ListModelMixin,
                            viewsets.mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = RequestSerializer
    permission_classes = (permissions.IsAuthenticated, IsApiUser, IsRequestOwner)
    lookup_field = "request_no"
    lookup_value_regex = r"[\w\-]+"

    def get_queryset(self):
        return Request.objects.filter(owner=self.request.user).order_by('-id')

    def list(self, request, *args, **kwargs):
        raise NotFound()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception, inst:
            raise inst

        merger = PyPDF2.PdfFileMerger()
        for package in instance.packages.order_by('id'):
            merger.append(PyPDF2.PdfFileReader(package.waybill_file.file))
        merger_data = StringIO()
        merger.write(merger_data)
        file_size = merger_data.tell()
        merger_data.seek(0)
        response = StreamingHttpResponse(FileWrapper(merger_data, 8192), content_type='application/octet-stream')
        response['Content-Length'] = file_size
        response['Content-Disposition'] = "attachment; filename=%s" % urllib.quote(instance.request_no + '.pdf')
        return response


class CityViewSet(viewsets.mixins.ListModelMixin,
                  viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, IsApiUser,)

    def list(self, request, *args, **kwargs):
        try:
            # system_config = get_system_config("yunda")
            # return Response(
            #     list_cities(system_config['url_base'], system_config['user_name'], system_config['password']).json())
            cities_json = os.path.join(os.path.dirname(os.path.realpath(__file__)), "json", "cities.json")
            with open(cities_json) as f:
                data = json.load(f)
                return Response(data)
        except Exception, inst:
            raise APIException(
                detail={'detail': 'City list error!'},
                code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrackingViewSet(URLConfMixin,
                      viewsets.mixins.ListModelMixin,
                      viewsets.mixins.RetrieveModelMixin,
                      viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, IsApiUser,)

    def list(self, request, *args, **kwargs):
        raise NotFound()

    def retrieve(self, request, *args, **kwargs):
        if not 'pk' in kwargs:
            raise NotFound()
        if not Package.objects.exclude(request__test_mode=True)\
                .filter(tracking_no=kwargs['pk'], request__owner=request.user).first():
            if Package.objects.exclude(request__test_mode=False)\
                .filter(tracking_no=kwargs['pk'], request__owner=request.user).first():
                with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "json",
                                       "tracking_sample.json")) as f:
                    data = json.load(f)
                data['timestamp'] = timezone.now()
                data['tracking_no'] = kwargs['pk']
                return Response(data)
            raise NotFound()
        order_number = kwargs['pk']
        try:
            now = timezone.now()
            record, agent_items = query_tracking_info(order_number, now)
            pre_agent_items = []
            if record.creation_time and record.creation_time < now:
                pre_agent_items.append({
                    'time': record.creation_time,
                    'detail':
                        _(u"英国包裹信息与面单已生成") if record.route == 'yunda'
                        else _(u"【英国】包裹信息与面单已生成")
                })
            if record.departure_time and record.departure_time < now:
                pre_agent_items.append({
                    'time': record.departure_time,
                    'detail':
                        _(u"英国离开处理中心发往中国广州") if record.route == 'yunda'
                        else _(u"【英国】离开处理中心发往中国") if record.route == 'xian'
                        else _(u"【英国】离开处理中心发往中国广州")
                })
            if record.landed_time and record.landed_time < now:
                pre_agent_items.append({
                    'time': record.landed_time,
                    'detail':
                        _(u"广州市到达广州白云机场 运往海关申报清关") if record.route == 'yunda'
                        else _(u"【西安市】到达西安咸阳国际机场 进行转关") if record.route == 'xian'
                        else _(u"【广州市】到达广州白云机场 运往海关申报清关")
                })
            if record.custom_clearance_time and record.custom_clearance_time < now:
                pre_agent_items.append({
                    'time': record.custom_clearance_time,
                    'detail':
                        _(u"江门市到达海关快件处理中心 进行清关") if record.route == 'yunda'
                        else _(u"【西安市】到达海关快件处理中心 进行申报清关") if record.route == 'xian'
                        else _(u"【江门市】到达海关快件处理中心 进行清关")
                })
            data = {
                'timestamp': now,
                'tracking_no': order_number,
                'progress': pre_agent_items + list(agent_items),
                'delivered': record.status == record.Status.ARRIVED
            }
            return Response(data)
        except DBError, inst:
            raise APIException(detail=u"系统繁忙, 请稍后再试!", code=status.HTTP_503_SERVICE_UNAVAILABLE)
        except NotFound, inst:
            raise inst
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            raise APIException(detail=inst.message, code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountViewSet(viewsets.mixins.ListModelMixin,
                     viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, IsApiUser,)
    CENTS = Decimal('0.01')

    def list(self, request, *args, **kwargs):
        return Response({
            'username':request.user.username,
            'credit':request.user.profile.credit.quantize(self.CENTS),
            'currency': 'GBP'
        })
