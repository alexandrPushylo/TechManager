# Generated by Django 4.2 on 2023-04-13 06:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0024_alter_applicationtoday_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='technicdriver',
            name='technic',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='manager.technic', verbose_name='Транспортное средство'),
        ),
    ]
