# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-07-15 21:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order_api', '0011_auto_20170715_1849'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='api_test_mode',
            field=models.BooleanField(default=False),
        ),
    ]
