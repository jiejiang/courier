# *- coding: utf-8 -*
from django.utils.translation import ugettext_lazy as _
import re
from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    try:
        pattern = '^' + reverse(pattern_or_urlname) + '$'
    except NoReverseMatch:
        pattern = pattern_or_urlname
    path = context['request'].path
    if re.match(pattern, path):
        return 'active'
    return ''

@register.filter
def currency_format(value):
    if value is None or value == '':
        return ""
    value = intcomma(str("%.2f" % float(value)))
    return value[:-3] if value.endswith('.00') else value
