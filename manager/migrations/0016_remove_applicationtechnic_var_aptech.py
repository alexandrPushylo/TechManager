# Generated by Django 4.1.7 on 2023-02-28 07:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0015_applicationtechnic_var_id_orig'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='applicationtechnic',
            name='var_aptech',
        ),
    ]
