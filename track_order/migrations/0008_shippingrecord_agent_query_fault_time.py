# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-05-06 22:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('track_order', '0007_auto_20170506_1833'),
    ]

    operations = [
        migrations.AddField(
            model_name='shippingrecord',
            name='agent_query_fault_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
