# *- coding: utf-8 -*
import os
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_(u'文件后缀名不支持'))
