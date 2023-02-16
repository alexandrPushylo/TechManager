from django.db import models
from django.contrib.auth.models import User

# Create your models here.


#------------------------------STAFF-----------------------------------------------------------------------------------
class StaffAdmin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")

    def __str__(self): return f"{self.user}"

    class Meta:
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"


class StaffForeman(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    def __str__(self): return f"{self.user}"
    class Meta:
        verbose_name = "Прораб"
        verbose_name_plural = "Прорабы"


class StaffMaster(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    foreman = models.ForeignKey(StaffForeman, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Прораб')
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    def __str__(self): return f"{self.user}"
    class Meta:
        verbose_name = "Мастер"
        verbose_name_plural = "Мастера"


class StaffDriver(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    def __str__(self): return f"{self.user}"
    class Meta:
        verbose_name = "Водитель"
        verbose_name_plural = "Водители"


class StaffMechanic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    def __str__(self): return f"{self.user}"
    class Meta:
        verbose_name = "Механик"
        verbose_name_plural = "Механики"


class StaffSupply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    def __str__(self): return f"{self.user}"
    class Meta:
        verbose_name = "Сотрудник снабжение"
        verbose_name_plural = "Сотрудники снабжение"


#------------------------------STAFF-----------------------------------------------------------------------------------
#------------------------------TECHNIC----------------------------------------------------------------------------------

class TechnicType(models.Model):
    name = models.CharField(max_length=256, verbose_name='Тип техники')
    short_name = models.CharField(max_length=256, null=True, blank=True, verbose_name='Тип техники(коротко)')
    def __str__(self): return self.name
    class Meta:
        verbose_name = "Тип техники"
        verbose_name_plural = "Тип техники"
class TechnicName(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название группы техники')
    def __str__(self): return self.name
    class Meta:
        verbose_name = "Название группы техники"
        verbose_name_plural = "Название групп техники"

class Technic(models.Model):
    name = models.ForeignKey(TechnicName, on_delete=models.SET_NULL, null=True, verbose_name="Название техники")
    id_information = models.CharField(max_length=256, null=True, blank=True, verbose_name="Идентификационная информация")
    tech_type = models.ForeignKey(TechnicType, on_delete=models.SET_NULL, null=True, verbose_name='Тип техники')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    attached_driver = models.ForeignKey(StaffDriver, on_delete=models.SET_NULL, null=True, verbose_name='Прикрепленный водитель')
    def __str__(self): return f"{self.name} [{self.id_information}] - {self.description} -- {self.attached_driver}"
    class Meta:
        verbose_name = "Единица техники"
        verbose_name_plural = "Техника"



#------------------------------TECHNIC----------------------------------------------------------------------------------


class WorkDayTabel(models.Model):
    date = models.DateField(verbose_name="Дата", null=True)
    status = models.BooleanField(default=True, verbose_name="Рабочий день")
    def __str__(self): return f"{self.date} [{self.status}]"
    class Meta:
        verbose_name = 'Рабочий день'
        verbose_name_plural = 'Рабочие дени'

class DriverTabel(models.Model):
    driver = models.ForeignKey(StaffDriver, on_delete=models.SET_NULL, null=True, verbose_name="Водитель")
    status = models.BooleanField(default=True, verbose_name="Статус водителя")
    date = models.DateField(verbose_name="Дата", null=True)
    def __str__(self): return f"{self.driver} {self.date} [{self.status}]"
    class Meta:
        verbose_name = 'Табель водителя'
        verbose_name_plural = 'Табеля водителей'

class TechnicDriver(models.Model):
    technic = models.ForeignKey(Technic, on_delete=models.CASCADE, verbose_name='Транспортное средство')
    driver = models.ForeignKey(DriverTabel, on_delete=models.SET_NULL, null=True, verbose_name="Водитель техники")
    date = models.DateField(verbose_name="Дата", null=True)
    status = models.BooleanField(default=True, verbose_name="Статус техники")
    def __str__(self): return f"{self.technic} {self.driver} [{self.date}] {self.status}"
    class Meta:
        verbose_name = 'Техника-Водитель'
        verbose_name_plural = 'Техника-Водители'

#----------------------------------------------------------------------------------------------------------------------

class ConstructionSiteStatus(models.Model):
    status = models.CharField(max_length=256, verbose_name="Статус объекта")
    def __str__(self): return self.status
    class Meta:
        verbose_name = "Статус объекта"
        verbose_name_plural = "Статусы объектов"

class ConstructionSite(models.Model):  #Строительные объекты
    address = models.CharField(max_length=512, verbose_name="Адрес", null=True, blank=True)
    foreman = models.ForeignKey(StaffForeman, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Прораб")
    status = models.ForeignKey(ConstructionSiteStatus, on_delete=models.SET_NULL, null=True, verbose_name="Статус объекта")
    def __str__(self): return f"{self.address} ({self.foreman}) - {self.status}"
    class Meta:
        verbose_name = "Строительный объект"
        verbose_name_plural = "Строительные объекты"

class ApplicationStatus(models.Model):
    status = models.CharField(max_length=255, verbose_name="Статус заявки")
    def __str__(self): return f"{self.status}"
    class Meta:
        verbose_name = "Статус заявки"
        verbose_name_plural = "Статусы заявок"



class ApplicationToday(models.Model):
    construction_site = models.ForeignKey(ConstructionSite, on_delete=models.CASCADE,
                                          verbose_name="Строительный объект")

    date = models.DateField(verbose_name="Дата", null=True)
    status = models.ForeignKey(ApplicationStatus, on_delete=models.SET_NULL, null=True, verbose_name="Статус заявки")
    def __str__(self): return f"{self.construction_site} [{self.date}] - {self.status}"
    class Meta:
        verbose_name = "Заявка на объект"
        verbose_name_plural = "Заявки на объект"

class ApplicationTechnic(models.Model):
    app_for_day = models.ForeignKey(ApplicationToday, on_delete=models.CASCADE, verbose_name="Заявка на объект")
    technic_driver = models.ForeignKey(TechnicDriver, on_delete=models.SET_NULL, null=True, verbose_name = 'Техника-Водитель')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    priority = models.DecimalField(max_digits=3, decimal_places=0, default=1, verbose_name='Приоритет заявки')
    def __str__(self): return f"{self.app_for_day} {self.technic_driver}"
    class Meta:
        verbose_name = "Заявка на технику"
        verbose_name_plural = "Заявки на технику"


class Variable(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название переменной')
    value = models.CharField(max_length=512, null=True, blank=True, verbose_name='Значение переменной')
    flag = models.BooleanField(default=False, verbose_name='Флаг переменной')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    def __str__(self): return f'{self.name} {self.value} [{self.flag}]'
    class Meta:
        verbose_name = "Переменная"
        verbose_name_plural = "Переменные"
