# Generated by Django 3.2.15 on 2022-08-12 06:36

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Recording',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('frequency', models.PositiveBigIntegerField(db_index=True)),
                ('duration', models.FloatField(db_index=True)),
                ('file', models.FileField(upload_to='recording/%Y-%m-%d/', validators=[django.core.validators.FileExtensionValidator(['mp3'])])),
                ('recording_date', models.DateTimeField(db_index=True)),
            ],
        ),
    ]