# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-05-06 16:45
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('track_order', '0005_shippingrecord_shippingrecorditem'),
    ]

    operations = [
        migrations.AddField(
            model_name='shippingrecord',
            name='agent_query_result',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
