# *- coding: utf-8 -*
from django.core.validators import RegexValidator

import re
from django.shortcuts import get_object_or_404
from django import forms
from django.db.models.manager import Manager
from django.utils.translation import ugettext as _
from mezzanine.accounts.forms import LoginForm, PasswordResetForm, ProfileForm, get_profile_for_user
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset, ButtonHolder, Div, Field, HTML
from crispy_forms.bootstrap import PrependedText, InlineRadios, FieldWithButtons, StrictButton
from captcha.fields import CaptchaField

def format_parcel_force_import_job_create_form(form):
    form.helper = FormHelper()
    form.helper.form_class = 'form-horizontal'
    form.helper.label_class = 'col-lg-5'
    form.helper.field_class = 'col-lg-7'
    form.fields['input_file'].label = _(u"选择PDF文件")

    form.helper.layout = Layout(
        'input_file',
        ButtonHolder(
            Submit('submit', _(u"上载"), css_class='btn-block btn-lg btn-success btn'),
        )
    )
    return form

class QueryOrderForm(forms.Form):
    ROUTE_CHOICES = (('order_system', _(u"包税线路")), ('parcel_force', _(u"Parcel Force")))
    DAYS_CHOICES = (('7', _(u"一周")), ('14', _(u"两周")), ('31', _(u"一个月")), ('62', _(u"两个月")),)

    route = forms.ChoiceField(label=_(u"线路选择"), choices=ROUTE_CHOICES, required=True, initial='order_system')
    name = forms.CharField(label=_(u"收件人姓名"), required=False)
    mobile = forms.CharField(label=_(u"收件人手机号码(无区号)"), required=False)
    id = forms.CharField(label=_(u"收件人身份证号码"), required=False)
    days = forms.ChoiceField(label=_(u"下单时间范围"), choices=DAYS_CHOICES, required=True, initial=31)
    captcha = CaptchaField(label=_(u"验证码"))

    class Media:
        js = ('js/route_choice.js',)


    def __init__(self, *args, **kwargs):
        super(QueryOrderForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'cols-sm-2'
        self.helper.field_class = 'cols-sm-10'

        self.helper.layout = Layout(
            InlineRadios('route'),
            Div(
                HTML("<span>" + _(u"信息填写") + "</span>"), css_class="strike"
            ),
            PrependedText('name', '<i class="fa-user fa" aria-hidden="true"></i>', placeholder=_(u"收件人姓名"),
                          wrapper_class='order_system'),
            PrependedText('mobile', '<i class="fa-mobile fa" aria-hidden="true"></i>', placeholder=_(u"收件人手机号码")),
            Div(
                HTML("<span>" + _(u"或") + "</span>"), css_class="strike order_system"
            ),
            PrependedText('id', '<i class="fa-id-card fa" aria-hidden="true"></i>', placeholder=_(u"收件人身份证号码"),
                          wrapper_class='order_system'),
            InlineRadios('days'),
            HTML("<hr/>"),
            Field('captcha', placeholder=_(u"输入验证码")),
            ButtonHolder(
                Submit('submit', _(u"查询"), css_class='btn-block btn-lg login-button'),
                css_class='form-group',
            )
        )

        self.valid_days = set([x[0] for x in self.DAYS_CHOICES])

    def clean(self):
        error = {}

        route = self.cleaned_data['route']
        id = self.cleaned_data.get('id', None)
        name = self.cleaned_data.get('name', None)
        mobile = self.cleaned_data.get('mobile', None)
        days = self.cleaned_data.get('days', None)
        if days not in self.valid_days:
            error['days'] = _(u"非法选项")

        if (route == 'order_system' and (id or (name and mobile))) or (route == 'parcel_force' and mobile):
            pass
        else:
            for field in ('id', 'name', 'mobile'):
                if not self.cleaned_data.get(field, None):
                    error[field] = _(u"请填写此字段")
            raise forms.ValidationError(error)


class TrackShippingForm(forms.Form):
    order_number = forms.CharField(min_length=8, max_length=25,
                                   validators=[
                                       RegexValidator(
                                           regex=r'^[a-zA-Z\d]+$',
                                           message=_(u'订单号格式错误'),
                                       ),
                                   ]
    )

    def __init__(self, *args, **kwargs):
        super(TrackShippingForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.form_id = "track-form"

        self.helper.layout = Layout(
            FieldWithButtons(Field('order_number', placeholder=_(u"输入订单号")),
                             StrictButton("<i class='fa fa-search'></i> " + _(u"立刻查询"), type="submit",
                                          css_class="btn-primary", id="track-submit"))
        )

