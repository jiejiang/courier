# *- coding: utf-8 -*

import re

def validate_cn(phone):
    """
    #source: https://blog.csdn.net/Beyond_F4/article/details/78490002
    :param phone:
    :return:
    """
    if re.match(r'^1[3,4,5,7,8]\d{9}$', phone):
        #中国联通：
        # 130，131，132，155，156，185，186，145，176
        if re.match(r'13[0,1,2]\d{8}', phone) or \
            re.match(r"15[5,6]\d{8}", phone) or \
            re.match(r"18[5,6]", phone) or \
            re.match(r"145\d{8}", phone) or \
            re.match(r"176\d{8}", phone):
            return True
        #中国移动
        # 134, 135 , 136, 137, 138, 139, 147, 150, 151,
        # 152, 157, 158, 159, 178, 182, 183, 184, 187, 188；
        elif re.match(r"13[4,5,6,7,8,9]\d{8}", phone) or \
            re.match(r"147\d{8}|178\d{8}", phone) or \
            re.match(r"15[0,1,2,7,8,9]\d{8}", phone) or \
            re.match(r"18[2,3,4,7,8]\d{8}", phone):
            return True
        else:
            #中国电信
            #133,153,189
            return True
    else:
        return False

def validate_uk(phone):
    """
    # source: https://github.com/jquery-validation/jquery-validation/issues/154
    :param phone:
    :return:
    """
    if re.match(r'^07([45789]\d{2}|624)\d{6}$', phone):
        return True
    return False
