# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-19 20:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('issue_order', '0013_auto_20180818_2356'),
    ]

    operations = [
        migrations.AddField(
            model_name='courierorder',
            name='last_update',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='courierorder',
            name='status',
            field=models.CharField(choices=[('created', '\u5df2\u4e0b\u5355'), ('paid', '\u5df2\u652f\u4ed8'), ('submitted', '\u5df2\u63d0\u4ea4'), ('generated', '\u5df2\u751f\u6210'), ('failed', '\u7cfb\u7edf\u9519\u8bef'), ('cancelled', '\u5df2\u53d6\u6d88')], db_index=True, default='created', max_length=16),
        ),
        migrations.AlterField(
            model_name='courierorder',
            name='system',
            field=models.CharField(choices=[('jixun', '\u5409\u8bafCC\u7ebf'), ('postal', '\u90ae\u653fBC\u7ebf'), ('yunda', '\u97f5\u8fbeCC\u7ebf')], db_index=True, max_length=32),
        ),
    ]