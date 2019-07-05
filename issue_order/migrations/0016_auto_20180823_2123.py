# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-23 20:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issue_order', '0015_auto_20180823_2108'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='slug',
            field=models.SlugField(default='', max_length=64, unique=True),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='route',
            unique_together=set([('system', 'code')]),
        ),
    ]
