# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-11 00:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issue_order', '0005_auto_20170211_0033'),
    ]

    operations = [
        migrations.AddField(
            model_name='courierbatch',
            name='num_order',
            field=models.IntegerField(blank=True, null=True, verbose_name='Number of Orders'),
        ),
    ]