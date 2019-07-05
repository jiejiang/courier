# *- coding: utf-8 -*

import pandas as pd
import requests, uuid, os, redis, time, sys, json, random
from requests.auth import HTTPBasicAuth
from django.utils.translation import ugettext_lazy as _
from order_api.models import Product

def normalize_columns(in_df):
    in_df.columns = map(lambda x: "".join(x.strip().split()), in_df.columns)


def check_line_by_line(n_row, in_row):
    sender_name = in_row[u'发件人名字']
    sender_phone = in_row[u'发件人电话号码']
    sender_address = in_row[u'发件人地址']
    receiver_name = in_row[u'收件人名字（中文）']
    receiver_mobile = in_row[u'收件人手机号（11位数）']
    receiver_address = in_row[u'收件人地址（无需包括省份和城市）']
    receiver_city = in_row[u'收件人城市（中文）']
    receiver_post_code = in_row[u'收件人邮编']
    n_package = in_row[u'包裹数量']
    package_weight = in_row[u'包裹重量（公斤）']
    length = in_row[u'长（厘米）']
    width = in_row[u'宽（厘米）']
    height = in_row[u'高（厘米）']
    id_number = in_row[u'身份证号(EMS需要)']

    for check_field in (sender_name, sender_phone, sender_address, receiver_name, receiver_mobile, receiver_address,
                        receiver_city, receiver_post_code, n_package, id_number):
        if pd.isnull(check_field):
            raise Exception, u"第%d行数据不完整,请更正" % n_row

    if not isinstance(sender_name, basestring) or not isinstance(sender_address, basestring):
        raise Exception, u"第%d行发件人信息异常" % n_row
    if not isinstance(n_package, int):
        raise Exception, u"第%d行包裹数量异常" % n_row
    if not isinstance(receiver_city, basestring) or not receiver_city.strip():
        raise Exception, u"第%d行收件人城市名异常" % n_row

def count_order_number(file_obj):
    in_df = pd.read_excel(file_obj, converters={
        u'发件人电话号码': lambda x: str(x),
        u'收件人邮编': lambda x: str(x),
        u'收件人手机号\n（11位数）': lambda x: str(x),
        u'身份证号\n(EMS需要)': lambda x: str(x),
        u'收件人手机号（11位数）': lambda x: str(x),
        u'身份证号(EMS需要)': lambda x: str(x),
        u'包裹数量': lambda x: int(x),
    })
    normalize_columns(in_df)
    for index, in_row in in_df.iterrows():
        check_line_by_line(index, in_row)
    return len(in_df)


def line_to_package(n_row, in_row):
    sender_name = in_row[u'发件人名字']
    sender_phone = in_row[u'发件人电话号码']
    sender_address = in_row[u'发件人地址']
    receiver_name = in_row[u'收件人名字（中文）']
    receiver_mobile = in_row[u'收件人手机号（11位数）']
    receiver_address = in_row[u'收件人地址（无需包括省份和城市）']
    receiver_city = in_row[u'收件人城市（中文）']
    receiver_post_code = in_row[u'收件人邮编']
    n_package = in_row[u'包裹数量']
    package_weight = in_row[u'包裹重量（公斤）']
    length = in_row[u'长（厘米）']
    width = in_row[u'宽（厘米）']
    height = in_row[u'高（厘米）']
    id_number = in_row[u'身份证号(EMS需要)']

    for check_field in (sender_name, sender_phone, sender_address, receiver_name, receiver_mobile, receiver_address,
                        receiver_city, receiver_post_code, n_package, id_number):
        if pd.isnull(check_field):
            raise Exception, u"第%d行数据不完整,请更正" % n_row

    if not isinstance(sender_name, basestring) or not isinstance(sender_address, basestring):
        raise Exception, u"第%d行发件人信息异常" % n_row
    if not isinstance(n_package, int):
        raise Exception, u"第%d行包裹数量异常" % n_row
    if not isinstance(receiver_city, basestring) or not receiver_city.strip():
        raise Exception, u"第%d行收件人城市名异常" % n_row

    total_count = 0
    package_items = []
    for i in xrange(n_package):
        suffix = "" if i == 0 else ".%d" % i
        item_name = in_row[u'申报物品%d(英文）' % (i + 1)]
        item_count = in_row[u'数量%s' % suffix]
        if item_name is None or pd.isnull(item_name):
            raise Exception, u"第%d行第%d个商品名称为空" % (n_row, i + 1)
        item_name = unicode(item_name).strip()
        product = Product.find_product(item_name)
        if not product:
            raise Exception, u"找不到产品:%s" % item_name
        total_count += item_count
        package_items.append({
            'product': product,
            'count': int(item_count)
        })

    return {
        'total_count': total_count,
        'package_items': package_items
    }


def parse_packages(file_obj):
    in_df = pd.read_excel(file_obj, converters={
        u'发件人电话号码': lambda x: unicode(x).encode('utf-8'),
        u'收件人邮编': lambda x: unicode(x).encode('utf-8'),
        u'收件人手机号\n（11位数）': lambda x: unicode(x).encode('utf-8'),
        u'身份证号\n(EMS需要)': lambda x: unicode(x).encode('utf-8'),
        u'收件人手机号（11位数）': lambda x: unicode(x).encode('utf-8'),
        u'身份证号(EMS需要)': lambda x: unicode(x).encode('utf-8'),
        u'包裹数量': lambda x: int(x),
    })
    normalize_columns(in_df)
    packages = []
    for index, in_row in in_df.iterrows():
        packages.append(line_to_package(index, in_row))
    return packages

def list_cities(url_base, user_name, password):
    return requests.get(url_base + "/api/v1.0/cities", auth=HTTPBasicAuth(user_name, password))

def create_courier_batch(url_base, user_name, password, file_obj, issuer, filename=None, test_mode=None,
                         route=None):
    file_obj.seek(0)
    if filename:
        file_obj = (str(uuid.uuid4()) + os.path.splitext(filename)[-1], file_obj)
    else:
        file_obj.name = str(uuid.uuid4()) + os.path.splitext(file_obj.name)[-1]
    data = {'issuer': issuer}
    if test_mode:
        data['test_mode'] = True
    if route:
        data['route'] = route
    response = requests.post(url_base + "/api/v1.0/batch-order", data=data, files={'file': file_obj},
                             auth=HTTPBasicAuth(user_name, password))
    print response.content
    json_obj = response.json()
    if not 'id' in json_obj:
        raise Exception, u"订单系统错误，联系客户: %s" % (json_obj['message'] if 'message' in json_obj else "")
    return json_obj['id']

def query_courier_batch(url_base, user_name, password, uuid):
    response = requests.get(url_base + "/api/v1.0/job/" + uuid, auth=HTTPBasicAuth(user_name, password))
    batch_obj = response.json()
    if not 'id' in batch_obj:
        raise Exception, "Failed to connect"
    return batch_obj

def query_products(url_base, user_name, password, code=None):
    url = url_base + "/api/v1.0/products"
    if code:
        url += '?route_code=%s' % code
    response = requests.get(url, auth=HTTPBasicAuth(user_name, password))
    if response.status_code != requests.codes.ok:
        raise Exception, "Failed query products"
    return response.json()

def download_courier_batch(url_base, user_name, password, uuid):
    return requests.get(url_base + "/api/v1.0/batch-order", params={'id': uuid},
                        auth=HTTPBasicAuth(user_name, password), stream=True)

def get_user_systems(user):
    group = user.groups.first()
    if not group:
        return []
    return group.prices.values_list('system', flat=True)

def get_user_prices(user, system):
    group = user.groups.first()
    if not group:
        return None
    return group.prices.filter(system=system).first()

def calculate_package_price(prices, package):
    has_1st_or_2nd = False
    price_over_thd = False

    total_count = package['total_count']
    if total_count <> 4 and total_count <> 6:
        raise Exception, _(u"包裹产品数量(%d)无效，需为4或者6个产品。" % total_count)

    for item in package['package_items']:
        product = item['product']
        if u'1段' in product.name or u'2段' in product.name:
            has_1st_or_2nd = True
        if product.unit_price > 13:
            price_over_thd = True

    if total_count == 4:
        if has_1st_or_2nd:
            if prices.price_4_pieces_high is None:
                raise Exception(_(u"价格栏4H未配置"))
            cost = prices.price_4_pieces_high
        else:
            if prices.price_4_pieces_low is None:
                raise Exception(_(u"价格栏4L未配置"))
            cost = prices.price_4_pieces_low
    elif total_count == 6:
        if price_over_thd:
            if prices.price_6_pieces_high is None:
                raise Exception(_(u"价格栏6H未配置"))
            cost = prices.price_6_pieces_high
        else:
            if prices.price_6_pieces_low is None:
                raise Exception(_(u"价格栏6L未配置"))
            cost = prices.price_6_pieces_low

    return cost
