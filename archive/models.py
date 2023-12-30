from django.db import models

# Create your models here.

class User(models.Model):
    id_U = models.IntegerField(null=False, blank=False, verbose_name="id user")
    username = models.CharField(max_length=150, null=False, blank=False, verbose_name="Никнейм")
    first_name = models.CharField(max_length=150, null=False, blank=False, verbose_name="Имя пользователя")
    last_name = models.CharField(max_length=150, null=False, blank=False, verbose_name="Фамилия пользователя")
    post = models.CharField(max_length=150, null=True, blank=True, verbose_name="Должность")
    date_joined = models.DateTimeField(verbose_name="Дата регистрации")
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    bd_status = models.BooleanField(null=False, default=False, verbose_name="Удален из базы данных")
    def __str__(self):
        return f'{self.first_name} {self.last_name} | Удален: {self.bd_status}'

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"


class ConstructionSite(models.Model):
    id_C_S = models.IntegerField(null=False, blank=False, verbose_name="id объекта")
    address = models.CharField(max_length=512, verbose_name="Адрес", null=True, blank=True)
    foreman_i = models.IntegerField(null=True, blank=True, verbose_name="id прораба")
    bd_status = models.BooleanField(null=False, default=False, verbose_name="Удален из базы данных")
    def __str__(self): return f"{self.address} | Удален: {self.bd_status}"

    class Meta:
        verbose_name = "Строительный объект"
        verbose_name_plural = "Строительные объекты"


class Technic(models.Model):
    id_T = models.IntegerField(null=False, blank=False, verbose_name="id техники")
    name = models.CharField(max_length=256, null=True, blank=True, verbose_name="Название техники")
    id_information = models.CharField(max_length=256, null=False, blank=False, verbose_name="Идентификационная информация")
    tech_type = models.CharField(max_length=256, null=False, blank=False, verbose_name='Тип техники')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    attached_driver_i = models.IntegerField(null=True, blank=True, verbose_name='id Прикрепленного водителя')
    supervisor_i = models.IntegerField(null=True, blank=True, verbose_name='id Руководителя')
    bd_status = models.BooleanField(null=False, default=False, verbose_name="Удален из базы данных")
    def __str__(self): return f"{self.name} [{self.id_information}] - {self.description} | Удален: {self.bd_status}"

    class Meta:
        verbose_name = "Единица техники"
        verbose_name_plural = "Техника"


class TWorkDay(models.Model):
    id_W_D = models.IntegerField(null=False, blank=False, verbose_name="id рабочего дня")
    date = models.DateField(null=False, blank=False, verbose_name="Дата")
    status = models.BooleanField(null=False, default=True, verbose_name="Рабочий день")
    def __str__(self): return f"{self.date} | Рабочий день: {self.status}"

    class Meta:
        verbose_name = 'Рабочий день'
        verbose_name_plural = 'Табель | Рабочие дени'


class TDriver(models.Model):
    id_D = models.IntegerField(null=False, blank=False, verbose_name="id отметки водителя")
    driver_i = models.IntegerField(null=True, blank=True, verbose_name="id водителя")
    status = models.BooleanField(default=True, verbose_name="Статус водителя")
    date = models.DateField(verbose_name="Дата", null=False)
    def __str__(self): return f"{self.date} [{self.status}]"

    class Meta:
        verbose_name = 'Отметка водителя'
        verbose_name_plural = 'Табель | Водители'


class TTechnicDriver(models.Model):
    id_T_D = models.IntegerField(null=False, blank=False, verbose_name="id отметки техники")
    technic_i = models.IntegerField(null=True, blank=True, verbose_name='id транспортного средства')
    driver_i = models.IntegerField(null=True, blank=True, verbose_name="id отметки водителя")
    date = models.DateField(verbose_name="Дата", null=True)
    status = models.BooleanField(default=True, verbose_name="Статус техники")
    def __str__(self): return f"{self.technic_i} - {self.date} [{self.status}]"

    class Meta:
        verbose_name = 'Отметка техники'
        verbose_name_plural = 'Табель | Техники'


class ApplicationToDay(models.Model):
    id_A_T_D = models.IntegerField(null=False, blank=False, verbose_name="id заявки на объект")
    date = models.DateField(null=False, verbose_name="Дата")
    construction_site_i = models.IntegerField(null=False, blank=False, verbose_name="id объекта")
    description = models.TextField(max_length=1024, null=True, blank=True, default='',
                                   verbose_name="Примечание для объекта")

    def __str__(self): return f"{self.date} - {self.description}"

    class Meta:
        verbose_name = "Заявка на объект"
        verbose_name_plural = "Заявки на объект"


class ApplicationTechnic(models.Model):
    id_A_T = models.IntegerField(null=False, blank=False, verbose_name="id заявки на технику")
    date = models.DateField(null=False, verbose_name="Дата")
    app_for_day_i = models.IntegerField(null=False, blank=False, verbose_name="id заявки на объект")
    technic_driver_i = models.IntegerField(null=True, blank=True, verbose_name='id отметки техники')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    priority = models.DecimalField(max_digits=3, decimal_places=0, default=1, verbose_name='Приоритет заявки')
    def __str__(self): return f"{self.date} | {self.description}"

    class Meta:
        verbose_name = "Заявка на технику"
        verbose_name_plural = "Заявки на технику"


class ApplicationMeterial(models.Model):
    id_A_M = models.IntegerField(null=False, blank=False, verbose_name="id заявки на материал")
    date = models.DateField(null=False, verbose_name="Дата")
    app_for_day_i = models.IntegerField(null=False, blank=False, verbose_name="id заявки на объект")
    description = models.TextField(max_length=2048, null=True, blank=True, verbose_name="Описание")
    def __str__(self): return f"{self.date} | {self.description}"

    class Meta:
        verbose_name = 'Заявка на материал'
        verbose_name_plural = 'Заявки на материалы'
