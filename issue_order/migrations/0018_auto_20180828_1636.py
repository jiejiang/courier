# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-28 15:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issue_order', '0017_auto_20180824_2217'),
    ]

    operations = [
        migrations.AddField(
            model_name='courierorder',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='package',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
    ]
