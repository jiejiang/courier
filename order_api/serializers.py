from rest_framework import serializers
import six
from order_api.models import Product, Request, Package, PackageItem, Route

class ProductSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="product-detail", lookup_field='barcode')
    name = serializers.ReadOnlyField()
    barcode = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ('url', 'name', 'barcode')


class RouteSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="route-detail", lookup_field='code')
    code = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()

    class Meta:
        model = Route
        fields = ('url', 'code', 'name')


class PackageItemSerializer(serializers.ModelSerializer):
    name = serializers.ChoiceField(choices=Product.objects.values_list('name', flat=True),
                                   source="product.name", required=False)
    barcode = serializers.ChoiceField(choices=Product.objects.values_list('barcode', flat=True),
                                      source="product.barcode", required=False)
    count = serializers.IntegerField()
    class Meta:
        model = PackageItem
        fields = ('name', 'barcode', 'count')


class TrackingNoHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def __init__(self, *args, **kwargs):
        return super(TrackingNoHyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        if not value.tracking_no:
            return None
        return super(TrackingNoHyperlinkedIdentityField, self).to_representation(value)


class RequestHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def __init__(self, *args, **kwargs):
        return super(RequestHyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        if value.status_code <> Request.StatusCode.SUCCEEDED:
            return None
        return super(RequestHyperlinkedIdentityField, self).to_representation(value)


class PackageSerializer(serializers.ModelSerializer):
    package_no = serializers.CharField(source="external_package_no", required=False)

    url = TrackingNoHyperlinkedIdentityField(view_name="package-detail", lookup_field='slug')
    tracking_no = serializers.ReadOnlyField()
    waybill = TrackingNoHyperlinkedIdentityField(view_name="waybill-detail", lookup_field='slug')
    request = serializers.HyperlinkedIdentityField(view_name="request-detail", lookup_field="request_no")
    items = PackageItemSerializer(many=True, source="packageitem_set")
    cost = serializers.ReadOnlyField()

    class Meta:
        model = Package
        fields = ('url', 'package_no', 'tracking_no', 'waybill', 'request', 'sender_name', 'sender_phone_number', 'sender_address',
                  'receiver_name', 'receiver_phone_number', 'receiver_address', 'receiver_city', 'receiver_post_code',
                  'receiver_id_number', 'weight', 'length', 'width', 'height', 'items', 'cost')

class RequestSerializer(serializers.HyperlinkedModelSerializer):
    route_code_choices = Route.objects.values_list('code', flat=True)
    order_no = serializers.CharField(source="external_order_no", required=False)

    url = serializers.HyperlinkedIdentityField(view_name="request-detail", lookup_field='request_no')
    route_code = serializers.ChoiceField(required=False, choices=route_code_choices, source='route.code')
    test_mode = serializers.ReadOnlyField()
    request_no = serializers.ReadOnlyField()
    waybills = RequestHyperlinkedIdentityField(view_name="request-waybill-detail", lookup_field='request_no')
    creation_date = serializers.DateTimeField(read_only=True)
    status = serializers.ReadOnlyField()
    error_msg = serializers.ReadOnlyField()
    packages = PackageSerializer(many=True)
    total_cost = serializers.ReadOnlyField()



    class Meta:
        model = Request
        fields = ('url', 'order_no', 'route_code', 'test_mode', 'request_no', 'waybills', 'creation_date', 'status', 'error_msg',
                  'packages', 'total_cost')
        lookup_field = "request_no"


class WaybillSerializer(serializers.ModelSerializer):
    tracking_no = serializers.ReadOnlyField()
    waybill = TrackingNoHyperlinkedIdentityField(view_name="waybill-detail", lookup_field='slug')
    package = TrackingNoHyperlinkedIdentityField(view_name="package-detail", lookup_field='slug')

    class Meta:
        model = Package
        fields = ('tracking_no', 'waybill', 'package')