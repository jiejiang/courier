#!/usr/bin/env python

import requests, hashlib, json, sys
from mezzanine.conf import settings

def query(route, order_number):
    customer = settings.KUAIDI100_CUSTOMER
    key = settings.KUAIDI100_KEY
    #company = settings.COURIER_SYSTEMS[route]['kuaidi100_com']
    if order_number.startswith("997"):
        company = 'youzhengguonei'
    elif order_number.startswith("7"):
        company = 'yunda'
    else:
        company = 'ems'
    param = '{"com":"%s","num":"%s"}' % (company, order_number)
    url = "http://poll.kuaidi100.com/poll/query.do"
    data = {
        "customer" : customer,
        "param" : param,
        "sign" : hashlib.md5("".join((param, key, customer))).hexdigest().upper()
    }
    try:
        response = requests.post(url, data=data, timeout=10)
    except Exception, inst:
        import traceback
        traceback.print_exc(sys.stderr)
        return None
    if response.status_code <> 200:
        return None
    res = json.loads(response.content)
    if 'result' in res and not res['result']:
        print >> sys.stderr, order_number, response.content
        return None
    return res

if __name__ == "__main__":
    query("ems", "1171663704699")
    query("ems", "1171663911899")
