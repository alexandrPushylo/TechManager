from django.db import models
from django.contrib.auth.models import User

# Create your models here.


#------------------------------STAFF-----------------------------------------------------------------------------------
class PostName(models.Model):
    name_post = models.CharField(max_length=128, verbose_name='Название должности')
    def __str__(self): return self.name_post
    class Meta:
        verbose_name = 'Название должности'
        verbose_name_plural = 'Название должностей'


class Post(models.Model):
    user_post = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Сотрудник', related_name='user_post')
    post_name = models.ForeignKey(PostName, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Название должности')
    telephone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Телефон")
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Руководитель', related_name='supervisor')
    def __str__(self): return f"{self.user_post.last_name} - {self.post_name}"
    class Meta:
        verbose_name = 'Категория сотрудника'
        verbose_name_plural = 'Категории сотрудников'

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
    attached_driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Прикрепленный водитель', related_name='attached_driver')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Руководитель',
                                   related_name='tech_supervisor')
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
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Водитель")
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
    foreman = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Прораб")
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
    var_aptd = models.CharField(max_length=256, null=True, blank=True)
    def __str__(self): return f"{self.construction_site} [{self.date}] - {self.status}"
    class Meta:
        verbose_name = "Заявка на объект"
        verbose_name_plural = "Заявки на объект"


class ApplicationTechnic(models.Model):
    id_group = models.DecimalField(max_digits=9, decimal_places=0, null=True, blank=True, verbose_name='Ид группы')
    app_for_day = models.ForeignKey(ApplicationToday, on_delete=models.CASCADE, verbose_name="Заявка на объект")
    technic_driver = models.ForeignKey(TechnicDriver, on_delete=models.SET_NULL, null=True, verbose_name = 'Техника-Водитель')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    priority = models.DecimalField(max_digits=3, decimal_places=0, default=1, verbose_name='Приоритет заявки')
    var_check = models.BooleanField(default=False, verbose_name='Проверена')
    var_ID_orig = models.DecimalField(max_digits=9, decimal_places=0, null=True, blank=True, verbose_name='Ид ApplicationTechnic')
    def __str__(self): return f"{self.app_for_day} {self.technic_driver}"
    class Meta:
        verbose_name = "Заявка на технику"
        verbose_name_plural = "Заявки на технику"


class CloneApplicationTechnic(models.Model):
    id_original_ap = models.DecimalField(max_digits=9, decimal_places=0, null=True, blank=True, verbose_name='Ид оригинала')
    ID_app_for_day = models.DecimalField(max_digits=9, decimal_places=0, null=True, blank=True, verbose_name="Ид заявки на объект")
    ID_technic_driver = models.DecimalField(max_digits=9, decimal_places=0, null=True, blank=True, verbose_name="Ид техника-водитель")
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    priority = models.DecimalField(max_digits=3, decimal_places=0, default=1, verbose_name='Приоритет заявки')
    var_check = models.BooleanField(default=False, verbose_name='Проверена')
    def __str__(self): return f'[{self.id_original_ap}]-[{self.ID_app_for_day}][{self.ID_technic_driver}]'
    class Meta:
        verbose_name = 'Снимок заявки на технику'
        verbose_name_plural = 'Снимоки заявки на технику'


class Variable(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название переменной')
    value = models.CharField(max_length=512, null=True, blank=True, verbose_name='Значение переменной')
    flag = models.BooleanField(default=False, verbose_name='Флаг переменной')
    description = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Описание")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self): return f'{self.name} - {self.value} - [{self.flag}] -- [{self.user}]'
    class Meta:
        verbose_name = "Переменная"
        verbose_name_plural = "Переменные"


class TeleBot(models.Model):
    user_bot = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='id пользователя')
    id_chat = models.CharField(max_length=128, verbose_name='id chat')
    def __str__(self): return f"{self.user_bot.last_name} - [{self.id_chat}]"