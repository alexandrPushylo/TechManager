# Generated by Django 4.1 on 2024-01-01 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0006_alter_tdriver_driver_i_alter_technic_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ttechnicdriver',
            name='driver_i',
            field=models.IntegerField(blank=True, null=True, verbose_name='id отметки водителя'),
        ),
    ]