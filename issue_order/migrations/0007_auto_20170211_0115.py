# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-11 01:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issue_order', '0006_courierbatch_num_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courierbatch',
            name='system',
            field=models.CharField(choices=[('yunda', '\u97f5\u8fbe\u7ebf'), ('postal', '\u90ae\u653f\u7ebf')], db_index=True, default=1, max_length=32, verbose_name='System Name'),
            preserve_default=False,
        ),
    ]
