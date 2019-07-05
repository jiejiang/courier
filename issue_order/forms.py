# *- coding: utf-8 -*
import sys, re

from django.forms import BaseInlineFormSet, ModelForm
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset, ButtonHolder, Div, Field, HTML
from crispy_forms.bootstrap import PrependedText, InlineRadios, FieldWithButtons, StrictButton, AppendedText
from djangoformsetjs.utils import formset_media_js
from mezzanine.conf import settings
from django.db import transaction
from mezzanine.accounts.forms import LoginForm, PasswordResetForm, ProfileForm
from captcha.fields import CaptchaField
from nested_formset import nestedformset_factory, inlineformset_factory, BaseNestedFormset, BaseNestedModelForm
from ukpostcodeutils.validation import is_valid_postcode as post_code_validate_uk

from utils.id_number import validate as id_number_validate
from utils.phone_number import validate_cn as phone_number_validate_cn, validate_uk as phone_number_validate_uk

from models import CourierBatch, CourierRate, COURIER_SYSTEMS_MAP, Profile, Package, Item, CourierOrder, Address, \
    get_cn_addresses
from validators import validate_file_extension
from courier_systems import count_order_number, create_courier_batch, get_user_prices, calculate_package_price, \
    parse_packages, get_user_systems
from products import get_product_info

class CourierBatchForm(forms.ModelForm):
    file = forms.FileField(label=_(u"订单excel文件"), validators=[validate_file_extension])

    class Meta:
        model = CourierBatch
        exclude = ('user', 'uuid', 'percentage', 'status', 'creation_time', 'rate', 'credit', 'state', 'message',
                   'num_order')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(CourierBatchForm, self).__init__(*args, **kwargs)

        self.fields['system'].label = _(u"线路选择")

        self.fields['system'].choices = \
            [('', '---------'), ] \
            + map(lambda x:(x, COURIER_SYSTEMS_MAP[x]), get_user_systems(self.user))

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-5'
        self.helper.field_class = 'col-lg-7'

        self.helper.layout = Layout(
            'system',
            'file',
            ButtonHolder(Submit("submit", _(u"提交"), css_class='btn btn-success btn-lg btn-block')))

    def clean(self):
        file_obj = self.cleaned_data['file']
        system = self.cleaned_data['system']
        if not system in settings.COURIER_SYSTEMS:
            raise forms.ValidationError({'system': _(u"线路未配置，联系客服")})
        system_config = settings.COURIER_SYSTEMS[system]
        if not 'url_base' in system_config or not 'user_name' in system_config or not 'password' in system_config:
            raise forms.ValidationError({'system': _(u"线路配置错误，联系客服")})

        prices = get_user_prices(self.user, system)
        if not prices:
            raise forms.ValidationError({'system': _(u"价格未配置")})

        try:
            packages = parse_packages(file_obj)
            if not packages:
                raise Exception, _(u"订单号为空")
            charge_amount = reduce(lambda x, y:x + y,
                                   map(lambda package:calculate_package_price(prices, package), packages))
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            raise forms.ValidationError({'file' : (_(u"文件格式错误：") + unicode(inst.message)).encode('utf-8')})

        pre_profile = Profile.objects.get(user=self.user)
        if pre_profile.credit < charge_amount:
            raise forms.ValidationError(_(u"余额£(%.2f)不足，需要£%.2f") % (pre_profile.credit, charge_amount))

        try:
            params = {
                'url_base': system_config['url_base'],
                'user_name': system_config['user_name'],
                'password': system_config['password'],
                'file_obj': file_obj,
                'issuer': " | ".join(filter(lambda x:x, (self.user.username, self.user.last_name,
                                                         self.user.first_name, self.user.email))),
            }
            if system == 'postal':
                params['route'] = 'fast-track'
            #params['test_mode'] = True
            uuid = create_courier_batch(**params)
            with transaction.atomic():
                profile = Profile.objects.select_for_update().get(user=self.user)
                profile.credit -= charge_amount
                profile.save()

            self.instance.uuid = uuid
            self.instance.user = self.user
            self.instance.percentage = "0"
            self.instance.status = _(u"已提交")
            self.instance.system = system
            self.instance.rate = None
            self.instance.credit = charge_amount
            self.instance.state = 0
            self.instance.num_order = len(packages)

        except Exception, inst:
            raise forms.ValidationError((_(u"错误：") + inst.message).encode('utf-8'))

        return self.cleaned_data

class LoginForm(LoginForm):
    captcha = CaptchaField(label=_(u"验证码"))

class PasswordResetForm(PasswordResetForm):
    captcha = CaptchaField(label=_(u"验证码"))

class ProfileForm(ProfileForm):
    captcha = CaptchaField(label=_(u"验证码"))

