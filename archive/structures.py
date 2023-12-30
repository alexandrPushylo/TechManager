from archive.models import TTechnicDriver
from archive.models import TDriver
from archive.models import TWorkDay
from archive.models import ApplicationMeterial
from archive.models import ApplicationTechnic
from archive.models import ApplicationToDay

from archive.models import Technic
from archive.models import ConstructionSite
from archive.models import User


from manager.utilities import archive_db as ARCHIVE_DB


class AUser:
    title = User._meta.verbose_name_plural.title().capitalize()

    def __init__(self, user_id):
        try:
            user = User.objects.using(ARCHIVE_DB).get(id_U=user_id)
            self.exists = True
            self.id = user.id_U
            self.username = user.username
            self.first_name = user.first_name
            self.last_name = user.last_name
            self.post = user.post
            self.telephone = user.telephone
            self.deleted = user.bd_status
        except User.DoesNotExist:
            self.exists = False

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class AConstructionSite:
    title = ConstructionSite._meta.verbose_name_plural.title().capitalize()

    def __init__(self, construction_site_id):
        try:
            construction_site = ConstructionSite.objects.using(ARCHIVE_DB).get(id_C_S=construction_site_id)
            self.exists = True
            self.id = construction_site.id_C_S
            self.address = construction_site.address
            self.foreman = AUser(construction_site.foreman_i) if construction_site.foreman_i is not None else None
            self.deleted = construction_site.bd_status
        except ConstructionSite.objects.DoesNotExist:
            self.exists = False

    def __str__(self):
        return f'{self.address} ({self.foreman})'


class ATechnic:
    title = Technic._meta.verbose_name_plural.title().capitalize()

    def __init__(self, technic_id):
        try:
            technic = Technic.objects.using(ARCHIVE_DB).get(id_T=technic_id)
            self.exists = True
            self.id = technic.id_T
            self.name = technic.name
            self.id_information = technic.id_information
            self.type = technic.tech_type
            self.description = technic.description
            self.attached_driver = AUser(
                technic.attached_driver_i) if technic.attached_driver_i is not None else None
            self.supervisor = AUser(
                technic.supervisor_i).id if technic.supervisor_i is not None else None
            self.deleted = technic.bd_status
        except Technic.objects.DoesNotExist:
            self.exists = False

    def __str__(self):
        return f'{self.name} [{self.id_information}]'


class AWorkday:
    title = TWorkDay._meta.verbose_name_plural.title().capitalize()

    def __init__(self, day):
        try:
            wday = TWorkDay.objects.using(ARCHIVE_DB).get(date=day)
            self.exists = True
            self.id = wday.id_W_D
            self.date = wday.date
            self.status = wday.status
        except TWorkDay.DoesNotExist:
            self.exists = False

    def __str__(self):
        return f'{self.date} - {"Рабочий" if self.status else "Выходной"}'


class ATDriver:
    title = TDriver._meta.verbose_name_plural.title().capitalize()

    def __init__(self, driver_id):
        try:
            driver = TDriver.objects.using(ARCHIVE_DB).get(id_D=driver_id)
            self.exists = True
            self.id = driver.id_D
            self.driver = AUser(driver.driver_i) if driver.driver_i is not None else None
            self.status = driver.status
            self.date = driver.date
        except TDriver.DoesNotExist:
            self.exists = False

    def __str__(self):
        return f'[{self.date}] {self.driver} - {"Работает" if self.status else "Не работает"}'


class ATTechnicDriver:
    title = TTechnicDriver._meta.verbose_name_plural.title().capitalize()

    def __init__(self, technic_driver_id):
        try:
            tech_driver = TTechnicDriver.objects.using(ARCHIVE_DB).get(id_T_D=technic_driver_id)
            self.exists = True
            self.id = tech_driver.id_T_D
            self.technic = ATechnic(tech_driver.technic_i) if tech_driver.technic_i is not None else None
            self.driver = ATDriver(tech_driver.driver_i) if tech_driver.driver_i is not None else None
            self.date = tech_driver.date
            self.status = tech_driver.status
        except TTechnicDriver.DoesNotExist:
            self.exists = False

    def __str__(self):
        return f'[{self.date}] {self.technic} - {"Работает" if self.status else "Не работает"}'


class AApplicationMaterial:
    title = ApplicationMeterial._meta.verbose_name_plural.title().capitalize()

    def __init__(self, application_material_id):
        try:
            application_material = ApplicationMeterial.objects.using(ARCHIVE_DB).get(id_A_M=application_material_id)
            self.exists = True
            self.id = application_material.id_A_M
            self.date = application_material.date
            self.app_to_day_id = application_material.app_for_day_i if application_material.app_for_day_i is not None else None
            self.description = application_material.description
        except ApplicationMeterial.DoesNotExist:
            self.exists = False

    def __str__(self):
        return f'[{self.date}] | {self.description}'


class AApplicationTechnic:
    title = ApplicationTechnic._meta.verbose_name_plural.title().capitalize()

    def __init__(self, application_technic_id):
        try:
            application_technic = ApplicationTechnic.objects.using(ARCHIVE_DB).get(id_A_T=application_technic_id)
            self.exists = True
            self.id = application_technic.id_A_T
            self.date = application_technic.date
            self.app_to_day_id = application_technic.app_for_day_i if application_technic.app_for_day_i is not None else None
            self.technic_driver = ATTechnicDriver(application_technic.technic_driver_i) if application_technic.technic_driver_i is not None else None
            self.description = application_technic.description
            self.priority = application_technic.priority
        except ApplicationTechnic.DoesNotExist:
            self.exists = False

    def __str__(self):
        return f'[{self.date}] | {self.technic_driver.technic} ({self.technic_driver.driver}) | {self.description}'


class AApplicationToday:
    title = ApplicationToDay._meta.verbose_name_plural.title().capitalize()

    def __init__(self, application_today_id):
        try:
            application_today = ApplicationToDay.objects.using(ARCHIVE_DB).get(id_A_T_D=application_today_id)
            self.exists = True
            self.id = application_today.id_A_T_D
            self.date = application_today.date
            self.construction_site = AConstructionSite(application_today.construction_site_i)
            self.description = application_today.description

            self.applications_technic = []
            self.applications_material = []
            self._get_application_technic()
            self._get_applications_material()

        except ApplicationToDay.DoesNotExist:
            self.exists = False

    def _get_application_technic(self):
        for at in ApplicationTechnic.objects.using(ARCHIVE_DB).filter(app_for_day_i=self.id):
            self.applications_technic.append(AApplicationTechnic(at.id_A_T))

    def _get_applications_material(self):
        for am in ApplicationMeterial.objects.using(ARCHIVE_DB).filter(app_for_day_i=self.id):
            self.applications_material.append(AApplicationMaterial(am.id_A_M))

    def __str__(self):
        return f'[{self.date}] | {self.construction_site}'


def get_application_today(day):
    applications = []
    app = ApplicationToDay.objects.using(ARCHIVE_DB).filter(date=day)
    if app.exists():
        for app_today in app:
            applications.append(AApplicationToday(app_today.id_A_T_D))
        return applications
    else:
        return None
