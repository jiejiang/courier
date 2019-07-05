

import redis, time, sys, json, ast
from mezzanine.conf import settings
from courier_systems import query_products

r = redis.StrictRedis(host='localhost', port=6379, db=0)

__value_timeout = 60 * 10
__lock_timeout = 10
__refresh_wait = 2
__max_retry = 10

def __obtain_lock(lock_key):
    cur_time = int(time.time())
    my_timeout = cur_time + __lock_timeout + 1
    if r.setnx(lock_key, my_timeout):
        return True
    else:
        last_timeout = int(r.get(lock_key))
        if last_timeout >= cur_time:
            return False
        new_timeout = int(r.getset(lock_key, my_timeout))
        if new_timeout == last_timeout:
            return True
        return False

def __release_lock(lock_key):
    r.delete(lock_key)

def query_product_info(system, code):
    system_config = settings.COURIER_SYSTEMS[system]
    params = {
        'url_base': system_config['url_base'],
        'user_name': system_config['user_name'],
        'password': system_config['password'],
        'code': code,
    }
    return query_products(**params)

def __get_product_info(system, code):
    value_key, lock_key = 'courier:%s:%s:products:value' % (system, code), 'courier:%s:%s:products:lock' % (system, code)
    value = r.get(value_key)
    if value is None:
        if __obtain_lock(lock_key):
            try:
                value = query_product_info(system, code)
                r.setex(value_key, __value_timeout, json.dumps(value))
            except Exception, inst:
                import traceback
                traceback.print_exc(sys.stderr)
                print >> sys.stderr, "Failed to obtain access token: %s" % str(inst)
            finally:
                __release_lock(lock_key)
    else:
        value = json.loads(value)
    return value

def get_product_info(route):
    product_info = None
    retry = 0
    while product_info is None:
        product_info = __get_product_info(route.system, route.code)
        if product_info is None:
            retry += 1
            if retry > __max_retry:
                raise Exception, "Maximum number to retry service"
            time.sleep(__refresh_wait)
    return product_info if product_info is not None else {}

