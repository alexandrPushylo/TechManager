from django.contrib import admin
from archive.models import User
from archive.models import ConstructionSite
from archive.models import Technic
from archive.models import TWorkDay
from archive.models import TDriver
from archive.models import TTechnicDriver
from archive.models import ApplicationToDay
from archive.models import ApplicationTechnic
from archive.models import ApplicationMeterial

# Register your models here.

admin.site.register(User)
admin.site.register(ConstructionSite)
admin.site.register(Technic)
admin.site.register(TWorkDay)
admin.site.register(TDriver)
admin.site.register(TTechnicDriver)
admin.site.register(ApplicationToDay)
admin.site.register(ApplicationTechnic)
admin.site.register(ApplicationMeterial)
