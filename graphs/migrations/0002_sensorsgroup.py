# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-18 21:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("graphs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SensorsGroup",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Nazwa")),
                ("enabled", models.BooleanField(default=True, verbose_name="Aktywna")),
                ("posted_date", models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")),
                ("sensors", models.ManyToManyField(to="graphs.Sensor", verbose_name="Lista czujników")),
            ],
            options={"verbose_name": "Grupa czujników", "verbose_name_plural": "Grupy czujników",},
        ),
    ]