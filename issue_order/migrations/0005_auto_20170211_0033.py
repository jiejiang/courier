# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-11 00:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issue_order', '0004_auto_20170210_2358'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courierbatch',
            name='credit',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Credit'),
        ),
        migrations.AlterField(
            model_name='courierbatch',
            name='rate',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Rate per Package'),
        ),
        migrations.AlterField(
            model_name='courierbatch',
            name='state',
            field=models.IntegerField(db_index=True, default=2, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='courierbatch',
            name='system',
            field=models.CharField(blank=True, choices=[('yunda', '\u97f5\u8fbe\u7ebf'), ('postal', '\u90ae\u653f\u7ebf')], db_index=True, max_length=32, null=True, verbose_name='System Name'),
        ),
        migrations.AlterField(
            model_name='courierbatch',
            name='uuid',
            field=models.CharField(blank=True, db_index=True, max_length=64, null=True, unique=True, verbose_name='UUID'),
        ),
    ]