# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-02 01:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lapsecore', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='camera',
            name='camera_web',
            field=models.TextField(blank=True, max_length=200, verbose_name=b'web interface url'),
        ),
    ]