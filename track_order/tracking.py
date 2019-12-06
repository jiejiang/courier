# *- coding: utf-8 -*

import sys, requests, os, datetime, random, pytz
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from mezzanine.conf import settings

from models import ShippingRecord
import kuaidi100

china_pytz = pytz.timezone('Asia/Shanghai')

class DBError(Exception):
    pass

def __query_order(route, order_number):
    system_config = settings.COURIER_SYSTEMS[route]
    url = system_config['url_base'] + "/api/v1.0/order/" + order_number
    auth = (system_config['user_name'], system_config['password'])
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json()
    return None

def __calc_landed_custom_clearance_time(depature_time):
    #return depature_time + datetime.timedelta(days=1), depature_time + datetime.timedelta(days=2)
    landed_time = depature_time + datetime.timedelta(
        days=3, hours=random.randrange(-3, 3), minutes=random.randrange(-30, 30),
        seconds=random.randrange(-30, 30))
    custom_clearance_time = depature_time + datetime.timedelta(
        days=4, hours=random.randrange(-3, 3), minutes=random.randrange(-30, 30),
        seconds=random.randrange(-30, 30))
    return landed_time.replace(microsecond=0), custom_clearance_time.replace(microsecond=0)

def __is_agent_query_allowed(record, now):
    if not record.departure_time or record.departure_time + datetime.timedelta(days=4) > now:
        return False
    if record.agent_query_fault_time and record.agent_query_fault_time + datetime.timedelta(seconds=30) > now:
        return False
    if record.agent_query_time and record.agent_query_time + datetime.timedelta(seconds=30) > now:
        return False
    return True

def __parse_datetime(datetime, zone=pytz.utc):
    return zone.localize(parse_datetime(datetime))

def query_tracking_info(order_number, now):
    record = ShippingRecord.objects.filter(order_number=order_number).first()
    created = False
    if not record: #generate record from query
        order = None
        route = None
        for system_name in reversed(settings.COURIER_SYSTEMS.keys()):
            route = system_name
            order = __query_order(route, order_number)
            if order:
                break
        if order is None or not order['usedTime']:
            raise Exception, _(u"暂无该空运包裹追踪，请稍后再查！")
        _record = ShippingRecord.objects.filter(order_number=order_number).first()
        if _record is None:
            record = ShippingRecord(order_number=order['orderNumber'],
                                    creation_time=__parse_datetime(order['usedTime']),
                                    route=route, status=ShippingRecord.Status.CREATED)
            try:
                record.save()
            except Exception, inst:
                import traceback
                traceback.print_exc(sys.stderr)
                raise DBError
        else:
            record = _record
        if order['retractionTime']:
            record.departure_time = __parse_datetime(order['retractionTime'])
            record.status = ShippingRecord.Status.DEPARTURE
            #pre populate the landing and custom time
            if order['landedTime'] and order['customClearanceTime']:
                record.landed_time = __parse_datetime(order['landedTime'])
                record.custom_clearance_time = __parse_datetime(order['customClearanceTime'])
            else:
                record.landed_time, record.custom_clearance_time = \
                    __calc_landed_custom_clearance_time(record.departure_time)
            print record.landed_time, record.custom_clearance_time
        created = True

    modified = created

    #check record status
    if record.status < ShippingRecord.Status.DEPARTURE and not created:
        order = __query_order(record.route, record.order_number)
        if order and order['retractionTime']:
            record.creation_time = __parse_datetime(order['usedTime']) #override the previous usedTime, because
            #when an order were reused, the usedTime would change. Note that retracted order cannot be reused, so safe here
            record.departure_time = __parse_datetime(order['retractionTime'])
            record.status = ShippingRecord.Status.DEPARTURE
            #pre populate the landing and custom time
            if order['landedTime'] and order['customClearanceTime']:
                record.landed_time = __parse_datetime(order['landedTime'])
                record.custom_clearance_time = __parse_datetime(order['customClearanceTime'])
            else:
                record.landed_time, record.custom_clearance_time = \
                    __calc_landed_custom_clearance_time(record.departure_time)
            modified = True
        # in the case of order reused, order would return None here, but no need to deal with it since no one knew
            # the old order number anyway

    if ShippingRecord.Status.DEPARTURE <= record.status < ShippingRecord.Status.ARRIVED:
        if __is_agent_query_allowed(record, now):
            agent_result = kuaidi100.query(record.route, record.order_number)
            if agent_result:
                print >> sys.stderr, now, "%s agent resulted" % order_number
                record.agent_query_result = agent_result
                record.agent_query_time = now
                record.agent_query_count = record.agent_query_count + 1
                if agent_result['state'] == '3':
                    record.status = ShippingRecord.Status.ARRIVED
            else:
                record.agent_query_fault_time = now
            modified = True
        else:
            print >> sys.stderr, now, "%s not allowed for agent query" % order_number

    if modified:
        try:
            record.save()
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            raise DBError

    agent_items = []
    if record.agent_query_result and 'data' in record.agent_query_result:
        for item in record.agent_query_result['data']:
            agent_items.append({
                'time': __parse_datetime(item['ftime'], china_pytz),
                'detail': item['context']
            })
    return record, reversed(agent_items)
