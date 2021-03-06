# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-08-25 12:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        ('issue_order', '0007_auto_20170211_0115'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupExtend',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_4_pieces_high', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='4\u7f50\u5305\u542b1/2\u6bb5')),
                ('price_4_pieces_low', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='4\u7f50\u53ea\u5305\u542b3/4\u6bb5')),
                ('price_6_pieces_high', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='6\u7f50\u5355\u4ef7\u4ecb\u4e8e22\u4e0e13\u78c5\u4e4b\u95f4')),
                ('price_6_pieces_low', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='6\u7f50\u5355\u4ef7\u4f4e\u4e8e13\u78c5(\u542b)')),
                ('group', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='auth.Group')),
            ],
        ),
    ]
