# Generated by Django 5.0.2 on 2024-07-06 14:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RFIDTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('RFID', models.CharField(max_length=100, unique=True)),
                ('is_location', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('rfid_tag', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='rvapi.rfidtag')),
            ],
            options={
                'ordering': ('rfid_tag',),
            },
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('Inv_Last_Check_Time', models.DateTimeField(auto_now_add=True, null=True)),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('Inv_Last_Loc', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='rvapi.location')),
                ('rfid_tag', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='rvapi.rfidtag')),
            ],
        ),
        migrations.CreateModel(
            name='Inspection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inspected_at', models.DateTimeField(auto_now_add=True)),
                ('inspected_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('rfid_tags', models.ManyToManyField(to='rvapi.rfidtag')),
            ],
        ),
    ]
