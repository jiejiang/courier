# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-08-31 15:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        ('issue_order', '0008_groupextend'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupPrice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('system', models.CharField(choices=[('yunda', '\u97f5\u8fbe\u7ebf'), ('postal', '\u90ae\u653f\u7ebf')], db_index=True, max_length=32, verbose_name='\u7ebf\u8def')),
                ('price_4_pieces_high', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='4\u7f50\u5305\u542b1/2\u6bb5')),
                ('price_4_pieces_low', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='4\u7f50\u53ea\u5305\u542b3/4\u6bb5')),
                ('price_6_pieces_high', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='6\u7f50\u5355\u4ef7\u4ecb\u4e8e22\u4e0e13\u78c5\u4e4b\u95f4')),
                ('price_6_pieces_low', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='6\u7f50\u5355\u4ef7\u4f4e\u4e8e13\u78c5(\u542b)')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='auth.Group')),
            ],
        ),
        migrations.RemoveField(
            model_name='groupextend',
            name='group',
        ),
        migrations.DeleteModel(
            name='GroupExtend',
        ),
        migrations.AlterUniqueTogether(
            name='groupprice',
            unique_together=set([('group', 'system')]),
        ),
    ]
