# *- coding: utf-8 -*
import json
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from django.utils.translation import ugettext as _

from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.forms import UserChangeForm, UsernameField
from django import forms
from mezzanine.accounts.admin import ProfileInline, UserProfileAdmin
from mezzanine.core.admin import TabularDynamicInlineAdmin

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from django.utils.safestring import mark_safe

from models import CourierRate, GroupPrice, Route, PricingRule


class CourierRateAdmin(TabularDynamicInlineAdmin):
    model = CourierRate

class ReadOnlyWidget(forms.Widget):
    def render(self, name, value, attrs):
        return format_html("<h2>%s</h2>" % value)


class ReadOnlyField(forms.Field):
    widget = ReadOnlyWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        super(ReadOnlyField, self).__init__(*args, **kwargs)

    def bound_data(self, data, initial):
        return initial

    def has_changed(self, initial, data):
        return False


class CreditUserChangeForm(UserChangeForm):
    change_credit = forms.DecimalField(label=_(u"充值金额 £"), required=False, initial=0)
    credit = ReadOnlyField(label=_(u"有效余额 £"))
    #locked_credit = ReadOnlyField(label=_(u"锁定余额 £"))
    can_use_api = forms.BooleanField(label=_(u"API用户"), required=False)
    api_test_mode = forms.BooleanField(label=_(u"API测试模式"), required=False)

    def __init__(self, *args, **kwargs):
        super(CreditUserChangeForm, self).__init__(*args, **kwargs)
        self.fields['credit'].initial = self.instance.profile.credit
        #self.fields['locked_credit'].initial = self.instance.profile.locked_credit
        self.fields['credit'].widget.attrs['font'] = 5
        self.fields['can_use_api'].initial = self.instance.api_profile.can_use_api
        self.fields['api_test_mode'].initial = self.instance.api_profile.api_test_mode

    def save(self, commit=True):
        if self.cleaned_data['change_credit'] <> 0:
            self.instance.profile.credit += self.cleaned_data['change_credit']
            self.instance.profile.save()
        if self.cleaned_data['can_use_api'] <> self.instance.api_profile.can_use_api \
                or self.cleaned_data['api_test_mode'] <> self.instance.api_profile.api_test_mode:
            self.instance.api_profile.can_use_api = self.cleaned_data['can_use_api']
            self.instance.api_profile.api_test_mode = self.cleaned_data['api_test_mode']
            self.instance.api_profile.save()
        return super(CreditUserChangeForm, self).save(commit)

    class Meta:
        model = User
        fields = '__all__'
        field_classes = {'username': UsernameField}

#UserProfileAdmin.inlines += [CourierRateAdmin,]
UserAdmin.form = CreditUserChangeForm
UserAdmin.fieldsets[0][1]['fields'] = ('username', 'password', ('credit', 'change_credit', 'can_use_api',
                                                                'api_test_mode'))
ProfileInline.exclude = ('credit', 'locked_credit')
UserProfileAdmin.list_display = ('username', 'last_name', 'first_name', 'is_active', 'is_staff', 'is_superuser',
                                 'credit', 'valid_order_number', 'can_use_api', 'api_test_mode', 'group_names')

def credit(cls, self):
    return self.profile.credit
credit.short_description = _(u"有效余额 £")
UserProfileAdmin.credit = credit

# def locked_credit(cls, self):
#     return self.profile.locked_credit
# locked_credit.short_description = _(u"锁定余额 £")
# UserProfileAdmin.locked_credit = locked_credit

def system_number(cls, self):
    return self.profile.system_number
system_number.short_description = _(u"开通系统个数")
UserProfileAdmin.system_number = system_number


def valid_order_number(cls, self):
    return self.profile.valid_order_number
valid_order_number.short_description = _(u"有效订单总数")
UserProfileAdmin.valid_order_number = valid_order_number

def can_use_api(cls, self):
    return self.api_profile.can_use_api
can_use_api.short_description = _(u"可以使用API")
can_use_api.boolean = True
UserProfileAdmin.can_use_api = can_use_api

def api_test_mode(cls, self):
    return self.api_profile.api_test_mode
api_test_mode.short_description = _(u"API测试模式")
api_test_mode.boolean = True
UserProfileAdmin.api_test_mode = api_test_mode

def group_names(cls, self):
    return " / ".join(self.groups.values_list('name', flat=True))
group_names.short_description = _(u"价格组")
UserProfileAdmin.group_names = group_names


class GroupPriceInline(admin.TabularInline):
    model = GroupPrice
    verbose_name = _(u"价格设置")
    verbose_name_plural = _(u"价格设置")
    extra = 1

class GroupAdmin(GroupAdmin):
    inlines = (GroupPriceInline, )
    list_display = ('name', 'prices')

    @classmethod
    def prices(cls, self):
        return " | ".join(map(lambda x:x.details, self.prices.all()))

class RouteAdmin(ModelAdmin):
    list_display = ('name', 'max_items_per_package', 'max_weight_per_package', 'pricing_rule', 'system', 'is_online')


class PricingRuleAdmin(ModelAdmin):
    list_display = ('name', 'config_prettified')

    def config_prettified(self, instance):
        response = json.dumps(instance.config, sort_keys=True, indent=2)
        response = response[:5000]
        formatter = HtmlFormatter(style='colorful')
        response = highlight(response, JsonLexer(), formatter)
        style = "<style>" + formatter.get_style_defs() + "</style>"
        return mark_safe(style + response)

    config_prettified.short_description = 'config'

admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

admin.site.register(Route, RouteAdmin)
admin.site.register(PricingRule, PricingRuleAdmin)
