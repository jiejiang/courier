# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-07-15 15:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order_api', '0008_product_internal_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='system',
            field=models.CharField(blank=True, db_index=True, max_length=32, null=True, verbose_name='System Name'),
        ),
        migrations.AddField(
            model_name='request',
            name='uuid',
            field=models.CharField(blank=True, db_index=True, max_length=64, null=True, unique=True, verbose_name='UUID'),
        ),
    ]
