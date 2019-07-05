# *- coding: utf-8 -*

from __future__ import unicode_literals
import os, json, re
from collections import OrderedDict
from math import ceil

from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.http.request import QueryDict
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import Sum, Count

COURIER_SYSTEMS = (
    ('jixun', _(u"吉讯CC线")),
    ('postal', _(u"邮政BC线")),
    ('yunda', _(u"韵达CC线")),
    ('heshan', _(u"鹤山CC线")),
    ('xian', _(u"西安CC线")),
)

COURIER_SYSTEMS_MAP = {key: value for key, value in COURIER_SYSTEMS}

class PickupOption:
    SELF_SERVE = 'self_serve'
    PICKUP_REQUIRED = 'pickup_required'
    COMPANY_PICKUP = 'company_pickup'
    DPD_PICKUP = 'dpd_pickup'

class CourierBatch(models.Model):
    STATUS = (
        (0, _(u"等待")),
        (1, _(u"成功")),
        (2, _(u"失败")),
        (3, _(u"删除")),
    )

    user = models.ForeignKey("auth.User", related_name="courier_batches", on_delete=models.CASCADE)
    uuid = models.CharField(_(u"UUID"), max_length=64, null=True, blank=True, unique=True, db_index=True)
    percentage = models.CharField(_("Percentage"), null=True, blank=True, max_length=16)
    status = models.CharField(_("Status"), null=True, blank=True, max_length=32, db_index=True)
    creation_time = models.DateTimeField(_("Creation Time"), auto_now_add=True, null=True, blank=True)
    system = models.CharField(_("System Name"), max_length=32, db_index=True, null=False, blank=False,
                              choices=COURIER_SYSTEMS)
    rate = models.DecimalField(_("Rate per Package"), null=True, blank=True, max_digits=10, decimal_places=2)
    credit = models.DecimalField(_("Credit"), null=True, blank=True, max_digits=10, decimal_places=2)
    state = models.IntegerField(_("State"), null=False, blank=False, db_index=True, default=2)
    message = models.TextField(_("Message"), null=True, blank=True)
    num_order = models.IntegerField(_("Number of Orders"), null=True, blank=True)

    @property
    def system_name(self):
        return COURIER_SYSTEMS_MAP[self.system] if self.system in COURIER_SYSTEMS_MAP else "N/A"

class Profile(models.Model):
    user = models.OneToOneField("auth.User")
    credit = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    locked_credit = models.DecimalField(default=0, max_digits=10, decimal_places=2) #deprecated

    #credit order helper context
    PICKUP_CHOICES = (
        (PickupOption.SELF_SERVE, _(u'自送曼城仓库')),
        (PickupOption.PICKUP_REQUIRED, _(u'上门取件')),
    )

    pickup_option = models.CharField(choices=PICKUP_CHOICES, default=PickupOption.SELF_SERVE, max_length=64)
    pickup_address = models.ForeignKey("Address", on_delete=models.PROTECT, related_name='+', null=True)

    @property
    def system_number(self):
        return CourierRate.objects.filter(user=self.user).count()

    @property
    def valid_order_number(self):
        obj = CourierBatch.objects.filter(user=self.user, state=CourierBatch.STATUS[1][0])\
            .aggregate(models.Sum('num_order'))
        return obj['num_order__sum'] if 'num_order__sum' in obj and obj['num_order__sum'] is not None else 0


class CourierRate(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    system = models.CharField(_("System Name"), max_length=32, db_index=True, null=False, blank=False,
                              choices=COURIER_SYSTEMS)
    rate = models.DecimalField(_("Rate per Package"), null=False, blank=False, max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('user', 'system')


class GroupPrice(models.Model):
    group = models.ForeignKey("auth.Group", on_delete=models.CASCADE, related_name="prices")
    system = models.CharField(_(u"线路"), max_length=32, db_index=True, null=False, blank=False,
                              choices=COURIER_SYSTEMS)
    price_4_pieces_high = models.DecimalField(_(u"4罐包含1/2段"), null=True, blank=True, max_digits=10,
                                              decimal_places=2)
    price_4_pieces_low = models.DecimalField(_(u"4罐只包含3/4段"), null=True, blank=True, max_digits=10,
                                             decimal_places=2)
    price_6_pieces_high = models.DecimalField(_(u"6罐单价介于22与13磅之间"), null=True, blank=True, max_digits=10,
                                              decimal_places=2)
    price_6_pieces_low = models.DecimalField(_(u"6罐单价低于13磅(含)"), null=True, blank=True, max_digits=10,
                                             decimal_places=2)
    @property
    def details(self):
        return COURIER_SYSTEMS_MAP[self.system] + ": " + \
               " / ".join(map(lambda x: str(x),
                       (self.price_4_pieces_high, self.price_4_pieces_low,
                        self.price_6_pieces_high, self.price_6_pieces_low)))

    class Meta:
        unique_together = ('group', 'system')


class Address(models.Model):
    GB = 'GB'
    CN = 'CN'
    COUNTRY_CHOICES = (
        (GB, u'UK'),
        (CN, u'中国'),
    )

    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    is_template = models.BooleanField(default=False)

    country = models.CharField(max_length=32, choices=COUNTRY_CHOICES)
    post_code = models.CharField(max_length=32)
    contact_name = models.CharField(max_length=64)
    address_line_1 = models.CharField(max_length=64)
    address_line_2 = models.CharField(max_length=64, blank=True, null=True)
    province = models.CharField(max_length=32, blank=True, null=True)
    city = models.CharField(max_length=32)
    district = models.CharField(max_length=32, blank=True, null=True)
    contact_number = models.CharField(max_length=32)

    id_number = models.CharField(max_length=32, blank=True, null=True)

    alias = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        text = ''
        if self.country == self.GB:
            text = u", ".join(
                (self.contact_name, self.address_line_1, self.city, self.post_code,
                 self.get_country_display(), 'Tel:%s' % self.contact_number))
        elif self.country == self.CN:
            text = " ".join(
                (self.contact_name,
                 "".join((self.get_country_display(), self.province, self.city,
                         self.district, self.address_line_1)),
                 u'邮编:%s' % self.post_code, u'电话:%s' % self.contact_number,
                 u'证件:%s' % self.id_number))
        if self.alias:
            text = (u'%s (%s)' % (self.alias, text))
        return text.encode('utf-8')

    @classmethod
    def get_sender_address_templates(cls, user):
        return cls.objects.filter(user=user, is_template=True, country=Address.GB)

    @classmethod
    def get_receiver_address_template(cls, user):
        return cls.objects.filter(user=user, is_template=True, country=Address.CN)


class PricingRule(models.Model):
    name = models.CharField(max_length=32)
    config = JSONField()

    def __unicode__(self):
        return self.name

    @property
    def default_price(self):
        return float(self.config['default_price'])

    def normalize_input(self, data, user):
        package = {}
        if isinstance(data, basestring):
            package = json.loads(data)
            def get_value(obj, field, convert):
                value = obj.get(field, '')
                return convert(value) if value is not None and value != '' else 0
            for field in ('length', 'width', 'height'):
                package[field] = get_value(package, field, int)
            package['gross_weight'] = get_value(package, 'gross_weight', float)
            for i in xrange(len(package.get('item_set', []))):
                if package['item_set'][i].get('count', ''):
                    package['item_set'][i]['count'] = int(package['item_set'][i]['count'])
        elif isinstance(data, Package):
            package = model_to_dict(data)
            package['item_set'] = [model_to_dict(item) for item in data.item_set.all()]
        else:
            raise NotImplementedError('input not supported yet')

        #common fields
        for field in ('sender_address', 'receiver_address'):
            if package.get(field, ''):
                package[field] = Address.objects.filter(pk=int(package.get(field)), user=user).first()
        return package

    def make_package_price(self, data, user):
        if not data:
            raise Exception, "Empty input"
        package = self.normalize_input(data, user)
        if self.config.get('type') == 'flat':
            return self.default_price
        elif self.config.get('type') == 'weight_based':
            levels = int(self.config.get('levels'))
            volumetric_weight = Package.calculate_volumetric_weight(package['length'], package['width'], package['height'])
            weight = volumetric_weight if volumetric_weight > package['gross_weight'] else package['gross_weight']
            price = None
            for i in range(levels):
                if weight <= float(self.config.get('level_%d' % i)):
                    price = float(self.config.get('level_%d_price' % i))
                    break
            if price is None:
                price = float(self.config.get('extra_price_per_kg')) \
                        * ceil(weight - self.config.get('level_%d' % (levels-1))) \
                        + float(self.config.get('level_%d_price' % (levels-1)))
            return price
        else:
            raise NotImplementedError('type not supported')


class Route(models.Model):
    system = models.CharField(max_length=32, db_index=True, null=False, blank=False, choices=COURIER_SYSTEMS)
    code = models.CharField(max_length=64, db_index=True, null=False, blank=False)
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64, db_index=True, null=False, blank=False, unique=True)

    max_items_per_package = models.PositiveIntegerField(blank=True, null=True)
    max_weight_per_package = models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=1)

    pricing_rule = models.ForeignKey(PricingRule, on_delete=models.SET_NULL, null=True, blank=True)

    is_online = models.BooleanField(default=True, blank=False)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('system', 'code',)


class CourierOrder(models.Model):
    class STATUS:
        CREATED = 'created'
        PAID = 'paid'
        SUBMITTED = 'submitted'
        GENERATED = 'generated'
        FAILED = 'failed'
        CANCELLED = 'cancelled'

    STATUS_CHOICES = (
        (STATUS.CREATED, u'已下单'),
        (STATUS.PAID, u'已支付'),
        (STATUS.SUBMITTED, u'已提交'),
        (STATUS.GENERATED, u'已生成'),
        (STATUS.FAILED, u'系统错误'),
        (STATUS.CANCELLED, u'已取消'),
    )

    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.PROTECT, null=False, blank=False)
    status = models.CharField(max_length=16, db_index=True, null=False, blank=False, choices=STATUS_CHOICES,
                              default=STATUS.CREATED)
    last_update = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(null=True, blank=True, max_digits=8, decimal_places=2)

    def calculate_price(self):
        # get pricing rule, TODO choose user specific pricing rule
        if not self.route.pricing_rule:
            raise Exception, "no route pricing available"
        pricing_rule = self.route.pricing_rule
        self.price = sum([package.calculate_price(pricing_rule) for package in self.package_set.all()])
        self.save()
        return self.price


class Package(models.Model):
    order = models.ForeignKey(CourierOrder, on_delete=models.CASCADE)
    sender_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='+', null=True)
    receiver_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='+', null=True)

    gross_weight = models.DecimalField(max_digits=4, decimal_places=1)
    length = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    price = models.DecimalField(null=True, blank=True, max_digits=8, decimal_places=2)

    @classmethod
    def calculate_volumetric_weight(cls, length, width, height):
        return length * width * height / 5000.

    def calculate_price(self, pricing_rule):
        self.price = pricing_rule.make_package_price(self, self.order.user)
        self.save()
        return self.price

    @property
    def effective_gross_weight(self):
        volumetric_weight = self.calculate_volumetric_weight(self.length, self.width, self.height)
        return volumetric_weight if volumetric_weight > self.gross_weight else self.gross_weight


@receiver(post_delete, sender=Package)
def __on_delete_package(**kwargs):
    package = kwargs.get('instance')
    if package.sender_address:
        package.sender_address.delete()
    if package.receiver_address:
        package.receiver_address.delete()


class Item(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    count = models.PositiveIntegerField(default=1)

__CN_ADDRESSES = None
def get_cn_addresses(province_name=None, city_name=None):
    global __CN_ADDRESSES
    if __CN_ADDRESSES is None:
        __cn_address_json = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "order_api",
                                         "json", "cities.json")
        with open(__cn_address_json) as f:
            data = json.load(f)
            __CN_ADDRESSES = OrderedDict()
            for province in data:
                province_data = OrderedDict()
                for city in province['contains']:
                    city_data = []
                    for district in city['contains']:
                        city_data.append(district['name'])
                    province_data[city['name']] = city_data
                __CN_ADDRESSES[province['name']] = province_data
    if province_name is not None:
        if city_name is not None:
            return __CN_ADDRESSES.get(province_name, {}).get(city_name, [])
        else:
            return __CN_ADDRESSES.get(province_name, {}).keys()
    else:
        return __CN_ADDRESSES.keys()


def get_courier_cart_stats(user):
    orders = CourierOrder.objects.filter(user=user, status=CourierOrder.STATUS.CREATED)
    stats = orders.aggregate(total_order_price=Sum('price'))
    if stats['total_order_price'] is None:
        stats['total_order_price'] = 0
    stats['total_package_count'] = 0
    stats['total_gross_weight'] = 0
    for order in orders:
        for package in order.package_set.all():
            stats['total_package_count'] += 1
            stats['total_gross_weight'] += package.effective_gross_weight
    return stats


def calculate_cost_with_pickup(pickup_type, pickup_address, cart_stats):
    ret = {
        'total_price': None,
        'pickup_price': None,
        'pickup_option': PickupOption.PICKUP_REQUIRED,
    }
    if pickup_type == PickupOption.SELF_SERVE:
        ret['total_price'] = cart_stats['total_order_price']
        ret['pickup_price'] = 0
        ret['pickup_option'] = PickupOption.SELF_SERVE
    else:
        if pickup_address is None or pickup_address.country != Address.GB or not pickup_address.post_code: #set to none to disable checkout
            pass
        else:
            if re.match(r'^M\d', pickup_address.post_code, flags=re.I):
                ret['pickup_price'] = 3 if cart_stats['total_package_count'] < 5 else 0
                ret['pickup_option'] = PickupOption.COMPANY_PICKUP
            else:
                ret['pickup_price'] = 10
                if cart_stats['total_gross_weight'] > 20:
                    ret['pickup_price'] += ceil(cart_stats['total_gross_weight'] - 20) * 0.4
                ret['pickup_option'] = PickupOption.DPD_PICKUP
            ret['total_price'] = ret['pickup_price'] + cart_stats['total_order_price']
    return ret
