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
class MultiDBModelAdmin(admin.ModelAdmin):
    # A handy constant for the name of the alternate database.
    using = 'archive'

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'other' database
        obj.delete(using=self.using)

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super().formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super().formfield_for_manytomany(db_field, request, using=self.using, **kwargs)


admin.site.register(User, MultiDBModelAdmin)
admin.site.register(ConstructionSite, MultiDBModelAdmin)
admin.site.register(Technic, MultiDBModelAdmin)
admin.site.register(TWorkDay, MultiDBModelAdmin)
admin.site.register(TDriver, MultiDBModelAdmin)
admin.site.register(TTechnicDriver, MultiDBModelAdmin)
admin.site.register(ApplicationToDay, MultiDBModelAdmin)
admin.site.register(ApplicationTechnic, MultiDBModelAdmin)
admin.site.register(ApplicationMeterial, MultiDBModelAdmin)