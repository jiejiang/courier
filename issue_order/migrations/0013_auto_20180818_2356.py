# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-18 22:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issue_order', '0012_address_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='country',
            field=models.CharField(choices=[('GB', 'UK'), ('CN', '\u4e2d\u56fd')], max_length=32),
        ),
    ]
