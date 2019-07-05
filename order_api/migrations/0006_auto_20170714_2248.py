# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-07-14 21:48
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order_api', '0005_auto_20170714_2157'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='request',
            name='completion_date',
        ),
        migrations.AddField(
            model_name='package',
            name='height',
            field=models.IntegerField(default=20, validators=[django.core.validators.MinValueValidator(1)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='length',
            field=models.IntegerField(default=20, validators=[django.core.validators.MinValueValidator(1)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='receiver_address',
            field=models.CharField(default='default', max_length=256),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='receiver_city',
            field=models.CharField(default='default', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='receiver_id_number',
            field=models.CharField(default='default', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='receiver_name',
            field=models.CharField(default='default', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='receiver_phone_number',
            field=models.CharField(default='default', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='receiver_post_code',
            field=models.CharField(default='default', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='sender_address',
            field=models.CharField(default='default', max_length=256),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='sender_name',
            field=models.CharField(default='default', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='sender_phone_number',
            field=models.CharField(default='default', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='weight',
            field=models.DecimalField(decimal_places=2, default=4, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='package',
            name='width',
            field=models.IntegerField(default=20, validators=[django.core.validators.MinValueValidator(1)]),
            preserve_default=False,
        ),
    ]