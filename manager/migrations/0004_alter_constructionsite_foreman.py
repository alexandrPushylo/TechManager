# Generated by Django 4.1.6 on 2023-02-14 07:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0003_delete_technicstatus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='constructionsite',
            name='foreman',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='manager.staffforeman', verbose_name='Прораб'),
        ),
    ]
