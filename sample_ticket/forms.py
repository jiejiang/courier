# *- coding: utf-8 -*

import os
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset, ButtonHolder, Div, Field, HTML

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.xlsx', '.xls', '.xlt']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_(u'文件后缀名不支持'))

class SampleTicketForm(forms.Form):
    files = forms.FileField(label=_(u"上传文件"), widget=forms.ClearableFileInput(attrs={'multiple': True}),
                            validators=[validate_file_extension,])
    is_jixun = forms.BooleanField(label=_(u"吉讯线小票"), required=False)

    def __init__(self, *args, **kwargs):
        super(SampleTicketForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-8'

        self.helper.layout = Layout(
            'files',
            'is_jixun',
            ButtonHolder(
                Submit('submit', _(u"上传"), css_class='btn btn-success btn-lg btn-block'),
            )
        )