# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-07-23 21:31
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='univ_roster',
            name='Token_LastPop',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 22, 21, 31, 39, 688224, tzinfo=utc)),
        ),
    ]
