from django.contrib import admin
from manager.models import ApplicationTechnic, ApplicationStatus, ApplicationToday
from manager.models import ConstructionSite, ConstructionSiteStatus
from manager.models import TechnicDriver, DriverTabel
from manager.models import StaffAdmin, StaffForeman, StaffMaster, StaffDriver, StaffMechanic, StaffSupply
from manager.models import Technic, TechnicName, TechnicType
from manager.models import WorkDayTabel
from manager.models import Variable
from manager.models import TeleBot

# Register your models here.
admin.site.register(ApplicationTechnic)
admin.site.register(ApplicationStatus)
admin.site.register(ApplicationToday)

admin.site.register(ConstructionSite)
admin.site.register(ConstructionSiteStatus)

admin.site.register(TechnicDriver)
admin.site.register(DriverTabel)

admin.site.register(WorkDayTabel)

admin.site.register(StaffAdmin)
admin.site.register(StaffForeman)
admin.site.register(StaffMaster)
admin.site.register(StaffDriver)
admin.site.register(StaffMechanic)
admin.site.register(StaffSupply)


admin.site.register(Technic)
admin.site.register(TechnicName)
admin.site.register(TechnicType)

admin.site.register(Variable)
admin.site.register(TeleBot)

