# Generated by Django 3.2.15 on 2023-01-01 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sdr', '0007_auto_20220913_1820'),
    ]

    operations = [
        migrations.AddField(
            model_name='transmission',
            name='data_type',
            field=models.CharField(default='uint8', max_length=255, verbose_name='Typ danych'),
            preserve_default=False,
        ),
    ]