# Generated by Django 3.1.2 on 2020-10-01 20:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'City',
                'verbose_name_plural': 'Cities',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Contry',
                'verbose_name_plural': 'Countries',
            },
        ),
        migrations.CreateModel(
            name='IP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=255, unique=True, verbose_name='IP address')),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='logs.city')),
            ],
            options={
                'verbose_name': 'IP',
                'verbose_name_plural': 'IPs',
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024, unique=True, verbose_name='Name')),
            ],
        ),
        migrations.CreateModel(
            name='UserAgent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024, unique=True, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'User Agent',
                'verbose_name_plural': 'User Agents',
            },
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw', models.CharField(max_length=1024, unique=True, verbose_name='Raw')),
                ('posted_date', models.DateTimeField(auto_now_add=True, verbose_name='Added datetime')),
                ('ip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='logs.ip')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='logs.resource')),
                ('user_agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='logs.useragent')),
            ],
        ),
        migrations.AddField(
            model_name='city',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='logs.country'),
        ),
        migrations.AlterUniqueTogether(
            name='city',
            unique_together={('name', 'country')},
        ),
    ]