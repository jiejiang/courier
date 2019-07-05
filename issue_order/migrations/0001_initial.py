# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-09 17:17
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourierBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='UUID')),
                ('percentage', models.CharField(blank=True, max_length=16, null=True, verbose_name='Percentage')),
                ('status', models.CharField(blank=True, db_index=True, max_length=32, null=True, verbose_name='Status')),
                ('creation_time', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation Time')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courier_batches', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
