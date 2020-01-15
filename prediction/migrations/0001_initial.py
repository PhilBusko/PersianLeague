# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-07-14 13:50
from __future__ import unicode_literals

import datetime
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('football', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Univ_Prediction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('OpenDate', models.DateTimeField(default=datetime.date(1, 1, 1))),
                ('CloseDate', models.DateTimeField(default=datetime.date(1, 1, 1))),
                ('Result', models.IntegerField(null=True)),
                ('GoalsHome', models.IntegerField(null=True)),
                ('GoalsAway', models.IntegerField(null=True)),
                ('AbilitiesUsed', models.CharField(max_length=500, null=True)),
                ('PntsResult', models.IntegerField(null=True)),
                ('PntsGoal', models.IntegerField(null=True)),
                ('PntsScorer', models.IntegerField(null=True)),
                ('PntsTotal', models.IntegerField(null=True)),
                ('GameFK', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='football.Game')),
                ('ScorerAwayFK', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pu_away', to='football.Player')),
                ('ScorerHomeFK', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pu_home', to='football.Player')),
                ('UserFK', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Univ_Roster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Token_LastPop', models.DateTimeField(default=django.utils.timezone.now)),
                ('Token_Rate', models.DecimalField(decimal_places=16, default=Decimal('0.0347222222222222'), max_digits=18)),
                ('Token_Total', models.IntegerField(default=0)),
                ('Upgrades', models.CharField(default='{"goalsG": 0, "scorersG": 0, "doubleDown": 0, "secondChance": 0, "clubFav": 0, "tokenRate": 0}', max_length=200)),
                ('Medals', models.CharField(default='[]', max_length=200)),
                ('SeasonFK', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='football.Season')),
                ('UserFK', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Univ_Scoring',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Round', models.CharField(max_length=10)),
                ('Points_Round', models.IntegerField(default=0)),
                ('Points_AllTime', models.IntegerField(default=0)),
                ('RewardStatus', models.IntegerField(default=0)),
                ('Rank_Round', models.IntegerField(null=True)),
                ('Perc_Round', models.DecimalField(decimal_places=4, max_digits=8, null=True)),
                ('Rank_AllTime', models.IntegerField(null=True)),
                ('Perc_AllTime', models.DecimalField(decimal_places=4, max_digits=8, null=True)),
                ('SeasonFK', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='football.Season')),
                ('UserFK', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]