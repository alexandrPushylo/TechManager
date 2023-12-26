from django.db import models

# Create your models here.

class User(models.Model):
    id_U = models.IntegerField(null=False, blank=False)
    username = models.CharField(max_length=150, null=False, blank=False)
    first_name = models.CharField(max_length=150, null=False, blank=False)
    last_name = models.CharField(max_length=150, null=False, blank=False)
    post = models.CharField(max_length=150, null=True, blank=True)
    date_joined = models.DateTimeField()
    telephone = models.CharField(max_length=20, null=True, blank=True)
    bd_status = models.BooleanField(null=False, default=True)


class ConstructionSite(models.Model):
    id_C_S = models.IntegerField(null=False, blank=False)
    address = models.CharField(max_length=512, verbose_name="Адрес", null=True, blank=True)
    foreman_i = models.IntegerField(null=False, blank=False, verbose_name="Прораб")
    bd_status = models.BooleanField(null=False, default=True)


class Technic(models.Model):
    id_T = models.IntegerField(null=False, blank=False)
    name = models.CharField(max_length=256, null=False, blank=False)
    id_information = models.CharField(max_length=256, null=False, blank=False)
    tech_type = models.CharField(max_length=256, null=False, blank=False)
    designation = models.TextField(max_length=1024, null=True, blank=True)
    attached_driver_i = models.IntegerField(null=False, blank=False, verbose_name='Прикрепленный водитель')
    supervisor_i = models.IntegerField(null=False, blank=False, verbose_name='Руководитель')

    bd_status = models.BooleanField(null=False, default=True)


class TWorkDay(models.Model):
    id_W_D = models.IntegerField(null=False, blank=False)
    date = models.DateField(null=False, blank=False)
    status = models.BooleanField(null=False, default=True)


class TDriver(models.Model):
    id_D = models.IntegerField(null=False, blank=False)
    driver_i = models.IntegerField(null=False, blank=False, verbose_name="Водитель")
    status = models.BooleanField(default=True, verbose_name="Статус водителя")
    date = models.DateField(verbose_name="Дата", null=False)


class TTechnicDriver(models.Model):
    id_T_D = models.IntegerField(null=False, blank=False)
    technic_i = models.IntegerField(null=False, blank=False, verbose_name='Транспортное средство')
    driver_i = models.IntegerField(null=False, blank=False, verbose_name="Водитель техники")
    date = models.DateField(verbose_name="Дата", null=True)
    status = models.BooleanField(default=True, verbose_name="Статус техники")


class ApplicationToDay(models.Model):
    id_A_T_D = models.IntegerField(null=False, blank=False)
    date = models.DateField(null=False)
    construction_site_i = models.IntegerField(null=False, blank=False)
    description = models.TextField(max_length=1024, null=True, blank=True, default='',
                                   verbose_name="Примечание для объекта")


class ApplicationTechnic(models.Model):
    id_A_T = models.IntegerField(null=False, blank=False)
    date = models.DateField(null=False)
    app_for_day_i = models.IntegerField(null=False, blank=False, verbose_name="Заявка на объект")
    technic_driver_i = models.IntegerField(null=False, blank=False, verbose_name = 'Техника-Водитель')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    priority = models.DecimalField(max_digits=3, decimal_places=0, default=1, verbose_name='Приоритет заявки')


class ApplicationMeterial(models.Model):
    id_A_M = models.IntegerField(null=False, blank=False)
    date = models.DateField(null=False)
    app_for_day_i = models.IntegerField(null=False, blank=False, verbose_name="Заявка на объект")
    description = models.TextField(max_length=2048, null=True, blank=True, verbose_name="Описание")
