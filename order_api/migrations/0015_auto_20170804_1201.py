# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-08-04 11:01
from __future__ import unicode_literals

import django.core.files.storage
from django.db import migrations, models
import order_api.models


class Migration(migrations.Migration):

    dependencies = [
        ('order_api', '0014_auto_20170716_1750'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='barcode',
            field=models.CharField(blank=True, db_index=True, max_length=128, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='package',
            name='waybill_file',
            field=models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='/home/jie/work/django/projects/courier/waybill_storage'), upload_to=order_api.models.waybill_upload_to),
        ),
    ]