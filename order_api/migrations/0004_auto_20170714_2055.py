# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-07-14 19:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order_api', '0003_auto_20170714_2054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packageitem',
            name='package',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order_api.Package'),
        ),
    ]
