from django.shortcuts import render
from django.contrib.auth import logout, login, authenticate
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q

from django.contrib.auth.models import User

from manager.models import ApplicationTechnic, ApplicationStatus, ApplicationToday
from manager.models import ConstructionSite, ConstructionSiteStatus
from manager.models import TechnicDriver, DriverTabel
from manager.models import StaffAdmin, StaffForeman, StaffMaster, StaffDriver, StaffMechanic, StaffSupply
from manager.models import Technic, TechnicName, TechnicType
from manager.models import WorkDayTabel
from manager.models import Variable

# from manager.forms import CreateNewApplicationForm

# --IMPORT CONST--
from manager.utilities import WEEKDAY
from manager.utilities import TODAY
from manager.utilities import TOMORROW
from manager.utilities import MONTH
from manager.utilities import dict_Staff
from manager.utilities import status_application as STATUS_AP
from manager.utilities import status_constr_site as STATUS_CS
#-----------------
from manager.utilities import get_day_in_days
from manager.utilities import get_difference
from manager.utilities import get_week
from manager.utilities import timedelta
from manager.utilities import choice as rand_choice
from manager.utilities import convert_str_to_date
# ----------------

# ----------PREPARE--------------
# set_locale()

# -------------------------------

# ------FUNCTION VIEW----------------------


def append_in_hos_tech(request, id_drv):
    _driver_table = DriverTabel.objects.get(id=id_drv)
    status = _driver_table.status
    date = _driver_table.date
    driver = _driver_table.driver
    if not status:
        return HttpResponseRedirect(f'/applications/{date}')

    constr_site, _ = ConstructionSite.objects.get_or_create(
        address='',
        foreman=None)
    constr_site.status = ConstructionSiteStatus.objects.get(status=STATUS_CS['opened'])
    constr_site.save()

    app_for_day, _ = ApplicationToday.objects.get_or_create(
        construction_site=constr_site,
        date=date)
    app_for_day.status = ApplicationStatus.objects.get(status=STATUS_AP['submitted'])
    app_for_day.save()

    technic_driver = TechnicDriver.objects.filter(
        driver=_driver_table,
        date=date,
        driver__status=True
    ).first()

    ApplicationTechnic.objects.get_or_create(
        app_for_day=app_for_day,
        technic_driver=technic_driver,
        description='Хоз. работы или за свой счет'
    )

    return HttpResponseRedirect(f"/applications/{date}")


def foreman_app_list_view(request, day):
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)
    foreman_list = StaffForeman.objects.filter()
    app_list = []
    for _fman in foreman_list:
        _app = ApplicationToday.objects.filter(date=current_day, construction_site__foreman=_fman)
        app_list.append((_fman, _app))

    out['app_list'] = app_list
    out['foreman_list'] = foreman_list

    return render(request, 'foreman_app_list.html', out)


def driver_app_list_view(request, day):
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)
    current_app_tech = ApplicationTechnic.objects.filter(
        technic_driver__status=True,
        app_for_day__date=current_day,
        app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['send']))
    current_driver_list = DriverTabel.objects.filter(status=True,
                                                     date=current_day,
                                                     technicdriver__status=True).distinct().order_by('driver__user__last_name')
    app_list = []
    for drv in current_driver_list:
        _app = current_app_tech.filter(technic_driver__driver=drv).order_by('priority')
        app_list.append((drv, _app))
    out['app_list'] = app_list

    return render(request, 'driver_app_list.html', out)


def conflict_correction_view(request, day, id_applications):
    out = {}
    id_application_list = id_applications.split(',')[:-1]
    tech_app_list = ApplicationTechnic.objects.filter(id__in=id_application_list)
    current_user = request.user
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)
    out["date_of_target"] = current_day
    out['tech_app_list'] = tech_app_list.order_by('technic_driver__driver__driver__user__last_name')
    out['conflicts_vehicles_list'] = get_conflicts_vehicles_list(current_day, 1)
    out['work_TD_list'] = get_work_TD_list(current_day, 0)
    # out["uniq_name_of_vehicles"] = TechnicName.objects.all().order_by('name')

    vehicle_and_driver = TechnicDriver.objects.filter(date=current_day, driver__isnull=False, status=True).values_list(
        'technic__name__name',
        'driver__driver__user__last_name',
        'id'
    )
    out['vehicle_and_driver'] = vehicle_and_driver
    out["uniq_name_of_vehicles"] = TechnicDriver.objects.filter(date=current_day, driver__isnull=False, status=True).values_list(
        'technic__name__name',
    ).order_by('technic__name__name').distinct()

    if request.method == 'POST':
        app_id_list = request.POST.getlist('id_list')
        for app_id in app_id_list:
            app = ApplicationTechnic.objects.get(id=app_id)
            if request.POST.get(f"vehicle_{app_id}"):
                app.technic_driver = TechnicDriver.objects.get(
                    date=current_day,
                    driver__driver__user__last_name=request.POST.get(f"driver_{app_id}"),
                    technic__name__name=request.POST.get(f"vehicle_{app_id}"),
                    status=True)
                app.description = request.POST.get(f"description_{app_id}")
                app.priority = request.POST.get(f"priority_{app_id}")

                app.save()
            else:
                app.delete()

        return HttpResponseRedirect(f'/conflict_resolution/{day}')
    return render(request, 'conflict_correction.html', out)


def conflict_resolution_view(request, day):
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)
    out["date_of_target"] = current_day
    lack_list = get_conflicts_vehicles_list(current_day, lack=True)
    out['lack_list'] = lack_list
    conflict_list = get_conflicts_vehicles_list(current_day)
    out['conflicts_list'] = conflict_list
    out['work_TD_list'] = get_work_TD_list(current_day)

    today_technic_applications_list = []
    for v in conflict_list:
        today_technic_applications = ApplicationTechnic.objects.filter(app_for_day__date=current_day,
                                                                       technic_driver__technic__name__name=v).values(
            'id',
            'technic_driver__driver__driver__user__last_name',
            'description',
            'app_for_day__construction_site__foreman__user__last_name',
            'app_for_day__construction_site__address',
            'technic_driver_id'
        ).order_by('app_for_day__construction_site__foreman__user__last_name')
        today_technic_applications_list.append((v, today_technic_applications))
    out['today_technic_applications'] = today_technic_applications_list

    return render(request, 'conflict_resolution.html', out)


# CONSTRURTION SITE------------------------------------------------------------------------CONSTRURTION SITE------------
def show_construction_sites_view(request):
    out = {}
    get_prepare_data(out, request)

    all_constr_site_list = ConstructionSite.objects.all().order_by('address').exclude(address='')

    if is_admin(request.user):
        construction_sites_list = all_constr_site_list
    elif is_foreman(request.user):
        construction_sites_list = all_constr_site_list.filter(foreman=StaffForeman.objects.get(user=request.user))
    elif is_master(request.user):
        foreman = StaffMaster.objects.get(user=request.user).foreman
        construction_sites_list = all_constr_site_list.filter(foreman=foreman)
    else:
        return HttpResponseRedirect('/')
    out["construction_sites_list"] = construction_sites_list.filter(
        status=ConstructionSiteStatus.objects.get(status='Открыт'))
    out["constr_sites_list_close"] = construction_sites_list.filter(
        status=ConstructionSiteStatus.objects.get(status='Закрыт'))
    return render(request, 'construction_sites.html', out)


def edit_construction_sites_view(request, id_construction_sites):
    out = {}
    get_prepare_data(out, request)
    construction_sites = ConstructionSite.objects.get(id=id_construction_sites)

    if is_admin(request.user):
        staff_list = StaffForeman.objects.filter().values_list('id', 'user__username', 'user__first_name')
    elif is_foreman(request.user):

        staff_list = StaffForeman.objects.filter(user=request.user).values_list('id', 'user__username',
                                                                                'user__first_name')
    elif is_master(request.user):
        foreman = StaffMaster.objects.get(user=request.user).foreman.user
        staff_list = StaffForeman.objects.filter(user=foreman).values_list('id', 'user__username', 'user__first_name')
    else:
        return HttpResponseRedirect('/')

    out["staff_list"] = staff_list
    out["construction_sites"] = construction_sites

    if request.method == 'POST':
        construction_sites.address = request.POST['construction_site_address']
        construction_sites.foreman = StaffForeman.objects.get(id=request.POST['foreman'])
        construction_sites.save()
        return HttpResponseRedirect('/construction_sites/')
    return render(request, 'edit_construction_site.html', out)


def delete_construction_sites_view(request, id_construction_sites):
    construction_sites = ConstructionSite.objects.get(id=id_construction_sites)
    construction_sites.delete()
    return HttpResponseRedirect('/construction_sites/')


def change_status_construction_site(request, id_construction_sites):
    constr_site = ConstructionSite.objects.get(id=id_construction_sites)
    if constr_site.status.status == STATUS_CS['opened']:
        constr_site.status = ConstructionSiteStatus.objects.get(status=STATUS_CS['closed'])
    else:
        constr_site.status = ConstructionSiteStatus.objects.get(status=STATUS_CS['opened'])
    constr_site.save()
    return HttpResponseRedirect('/construction_sites/')


def add_construction_sites_view(request):
    out = {}
    get_prepare_data(out, request)

    if is_admin(request.user):
        staff_list = StaffForeman.objects.filter().values_list('id', 'user__username', 'user__first_name')
    elif is_foreman(request.user):

        staff_list = StaffForeman.objects.filter(user=request.user).values_list('id', 'user__username', 'user__first_name')
    elif is_master(request.user):
        foreman = StaffMaster.objects.get(user=request.user).foreman.user
        staff_list = StaffForeman.objects.filter(user=foreman).values_list('id', 'user__username', 'user__first_name')
    else:
        return HttpResponseRedirect('/')

    out["staff_list"] = staff_list
    if request.method == 'POST':
        construction_sites = ConstructionSite.objects.create()
        construction_sites.address = request.POST['construction_site_address']
        if request.POST.get('foreman'):
            construction_sites.foreman = StaffForeman.objects.get(id=request.POST['foreman'])
        else:
            construction_sites.foreman = None
        construction_sites.status = ConstructionSiteStatus.objects.get(status=STATUS_CS['opened'])
        construction_sites.save()
        return HttpResponseRedirect('/construction_sites/')
    return render(request, 'edit_construction_site.html', out)

#-------------------------------------------------CONSTRURTION SITE-----------------------------------------------------

# STAFF----------------------------------------------------------------------------------------STAFF--------------------


def show_staff_view(request):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    get_prepare_data(out, request)
    staff_list = User.objects.all().order_by('last_name')
    _user_post = []
    for _user in staff_list:
        _post = dict_Staff[get_current_post(_user, key=True)]
        _tel = get_current_post(_user)
        _user_post.append((_user, _post, _tel))
    out['user_post'] = _user_post
    out['staff_list'] = staff_list
    return render(request, 'show_staff.html', out)


def edit_staff_view(request, id_staff):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    get_prepare_data(out, request)

    current_user = User.objects.get(id=id_staff)
    out['current_user'] = current_user
    post_list = dict_Staff
    out['post_list'] = post_list
    foreman_list = StaffForeman.objects.values_list('user_id', 'user__last_name', 'user__first_name')
    out['foreman_list'] = foreman_list
    current_post = get_current_post(current_user, key=True)
    out['current_post'] = get_current_post(current_user, key=True)
    if is_master(current_user):
        out['current_foreman'] = StaffMaster.objects.get(user=current_user).foreman.user.id

    if request.method == 'POST':
        selected_user = User.objects.get(id=id_staff)
        if request.POST.get('post') != current_post:
            get_current_post(selected_user).delete()

        if request.POST['post'] == 'master':
            foreman = StaffForeman.objects.get(user=request.POST['foreman'])
            staff, _ = StaffMaster.objects.get_or_create(user=selected_user)
            staff.foreman = foreman
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'admin':
            staff, _ = StaffAdmin.objects.get_or_create(user=selected_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'foreman':
            staff, _ = StaffForeman.objects.get_or_create(user=selected_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'driver':
            staff, _ = StaffDriver.objects.get_or_create(user=selected_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'mechanic':
            staff, _ = StaffMechanic.objects.get_or_create(user=selected_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'employee_supply':
            staff, _ = StaffSupply.objects.get_or_create(user=selected_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()

        selected_user.username = request.POST['username']
        selected_user.first_name = request.POST['first_name']
        selected_user.last_name = request.POST['last_name']
        if request.POST['new_password'] == 'true':
            selected_user.set_password(request.POST['password'])
        else:
            selected_user.password = request.POST['password']
        selected_user.save()

        return HttpResponseRedirect('/show_staff/')
    return render(request, 'edit_staff.html', out)

#-----------------------------------------------------STAFF-------------------------------------------------------------

# TABEL----------------------------------------------------------------------------------------TABEL--------------------


def tabel_driver_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)
    prepare_driver_table(day)
    driver_today_tabel = DriverTabel.objects.filter(date=current_day)
    out['driver_list'] = driver_today_tabel.order_by('driver__user__last_name')


    if request.POST.get('id_drv'):
        _id = request.POST.get('id_drv')
        _status = request.POST.get('status')
        _user = DriverTabel.objects.get(id=_id)
        _user.status = str(_status).capitalize()
        _user.save()

    if request.POST.getlist('staff_id'):
        id_driver_list = request.POST.getlist('staff_id')
        for n, staff_id in enumerate(id_driver_list, 1):
            if request.POST.get(f'staff_status_{n}'):
                st = DriverTabel.objects.get(id=staff_id)
                st.status = True
                st.save()
            else:
                st = DriverTabel.objects.get(id=staff_id)
                st.status = False
                st.save()
        return HttpResponseRedirect(f'/tabel_driver/{day}')

    return render(request, 'tabel_driver.html', out)


def tabel_workday_view(request, ch_week):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    if ch_week == 'nextweek':
        _day = TODAY+timedelta(7)
        out['week_title'] = 'Следующая неделя'
        out['ch_week'] = ch_week
    else:
        _day = TODAY
        out['week_title'] = 'Текущая неделя'

    get_prepare_data(out, request)
    last_week = list(get_week(_day, 'l'))
    current_week = list(get_week(_day))

    if WorkDayTabel.objects.filter(date=current_week[0]).count()==0:
        for n, day in enumerate(current_week, 1):
            if n in (6, 7):
                WorkDayTabel.objects.create(date=day, status=False)
            else:
                WorkDayTabel.objects.create(date=day)

    out['week'] = []
    for _day in range(7):
        out['week'].append((WorkDayTabel.objects.get(date=current_week[_day]), WEEKDAY[_day]))

    if request.POST.get('id_day'):
        _id = request.POST.get('id_day')
        _status = request.POST.get('status')
        _day = WorkDayTabel.objects.get(id=_id)
        _day.status = str(_status).capitalize()
        _day.save()

    if request.POST.getlist('day_id'):
        id_day_list = request.POST.getlist('day_id')
        for n, day_id in enumerate(id_day_list, 1):

            if request.POST.get(f'day_status_{n}'):
                st = WorkDayTabel.objects.get(id=day_id)
                st.status = True
                st.save()
            else:
                st = WorkDayTabel.objects.get(id=day_id)
                st.status = False
                st.save()
        return HttpResponseRedirect(f'/tabel_workday/{ch_week}')

    return render(request, 'tabel_workday.html', out)


def Technic_Driver_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)
    if DriverTabel.objects.filter(date=current_day, status=True).count() == 0:
        prepare_driver_table(day)



    work_driver_list = DriverTabel.objects.filter(date=current_day, status=True)
    if work_driver_list.count()==0:
        return HttpResponse('work_driver_list is empty')
    tech_drv_list_today = TechnicDriver.objects.filter(date=TODAY)

    if TechnicDriver.objects.filter(date=current_day).count() == 0:
        if get_CH_day(day) == 'next_day':
            for _tech in Technic.objects.all():
                _drv = tech_drv_list_today.filter(technic=_tech).values_list('driver__driver__user__last_name', 'status')
                driver = _drv[0][0]
                status = _drv[0][1]

                c_drv = work_driver_list.filter(driver__user__last_name=driver)

                if c_drv.count() != 0:
                    TechnicDriver.objects.create(technic=_tech,
                                                 driver=DriverTabel.objects.get(date=current_day, driver__user__last_name = driver),
                                                 date=current_day,
                                                 status=status)
                else:

                    TechnicDriver.objects.create(technic=_tech,
                                                 driver=None,
                                                 date=current_day,
                                                 status=status)
        else:
            for tech in Technic.objects.all():
                TechnicDriver.objects.create(technic=tech, date=TODAY, status=True)
    else:
        technic_driver_list = TechnicDriver.objects.filter(date=current_day)

        for _td in technic_driver_list:
            if not _td.driver:
                _attach_drv = _td.technic.attached_driver
                if not _attach_drv: continue
                _attach_drv_staff = DriverTabel.objects.get(driver=_attach_drv, date=current_day)
                if _attach_drv_staff.status:
                    _td.driver = _attach_drv_staff
                    _td.save()
                else:
                    _td.driver = None
                    _td.save()

    technic_driver_list = TechnicDriver.objects.filter(date=current_day)
    out['technic_driver_list'] = technic_driver_list.order_by('technic__name__name')
    out['work_driver_list'] = work_driver_list.order_by('driver__user__last_name')

    if request.POST.get('tech'):
        tech = request.POST.get('tech')
        id_drv = request.POST.get('id_drv')
        stat = request.POST.get('status')
        _td = TechnicDriver.objects.get(id=tech)
        if id_drv:
            _td.driver = DriverTabel.objects.get(id=id_drv)
        else:
            _td.driver = None
        _td.status = str(stat).capitalize()
        _td.save()

    if request.POST.getlist('tech_drv_id'):
        driver_list = request.POST.getlist('select_drv')
        tech_drv_id_list = request.POST.getlist('tech_drv_id')  ###   tech_status_

        for n, _id_td in enumerate(tech_drv_id_list):
            _td = TechnicDriver.objects.get(id=_id_td)
            if driver_list[n]:
                _td.driver = DriverTabel.objects.get(id=driver_list[n])
            else:
                _td.driver = None
            if request.POST.get(f'tech_status_{n + 1}'):
                _td.status = True
                _td.save()
            else:
                _td.status = False
                _td.save()

    if 'tech_list' in request.path:
        return render(request, 'tech_list.html', out)
    else:
        return render(request, 'technic_driver.html', out)

#-----------------------------------------------------TABEL-------------------------------------------------------------


def clear_application_view(request, id_application):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    current_application = ApplicationToday.objects.get(id=id_application)
    ApplicationTechnic.objects.filter(app_for_day=current_application).delete()
    current_application.status = ApplicationStatus.objects.get(status=STATUS_AP['absent'])
    current_application.save()
    return HttpResponseRedirect(f'/applications/{current_application.date}')


def show_applications_view(request, day, id_user=None):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    current_day = convert_str_to_date(day)
    if not current_day:
        return HttpResponseRedirect('/')
    out = {"constr_site_list": []}

    if id_user:
        current_user = User.objects.get(id=id_user)
        out['current_user'] = current_user
    else:
        current_user = request.user

    get_prepare_data(out, request, current_day)

    construction_site_list = ConstructionSite.objects.filter(status=ConstructionSiteStatus.objects.get(status=STATUS_CS['opened']))

    applications_today_list_all = ApplicationToday.objects.filter(date=current_day)
    if applications_today_list_all.count() < construction_site_list.count():
        for constr_site in construction_site_list:
            _app, _ = ApplicationToday.objects.get_or_create(construction_site=constr_site, date=current_day)
            if _:
                _app.status = ApplicationStatus.objects.get(status=STATUS_AP['absent'])
                _app.save()
    else:
        if construction_site_list.count() < applications_today_list_all.count():
            applications_today_list_all.exclude(construction_site__in=construction_site_list).delete()
        else:
            print("OK")

    if is_admin(current_user):
        app_for_day = ApplicationToday.objects.filter(Q(date=current_day),
                                                      Q(
                                                          Q(status = ApplicationStatus.objects.get(
                                                              status=STATUS_AP['submitted'])) |
                                                          Q(status = ApplicationStatus.objects.get(
                                                              status=STATUS_AP['approved']))|
                                                          Q(status=ApplicationStatus.objects.get(
                                                              status=STATUS_AP['send']))
                                                      ))

        out['conflicts_vehicles_list'] = get_conflicts_vehicles_list(current_day)
        out['work_TD_list'] = get_work_TD_list(current_day)
        if ApplicationToday.objects.filter(date=current_day,
                                           status=ApplicationStatus.objects.get(
                                               status=STATUS_AP['submitted'])).count() != 0:
            out['submitted_app_list'] = True
        if ApplicationToday.objects.filter(date=current_day,
                                           status=ApplicationStatus.objects.get(
                                               status=STATUS_AP['approved'])).count() != 0:
            out['send_app_list'] = True


        driver_table_list = DriverTabel.objects.filter(date=current_day).order_by('driver__user__last_name')

        l_out = []
        for _drv in driver_table_list:
            app = ApplicationTechnic.objects.filter(technic_driver__driver=_drv)
            tech_drv = TechnicDriver.objects.filter(driver=_drv)
            attach_drv = Technic.objects.filter(attached_driver=_drv.driver).values_list('name__name')
            count = app.count()

            l_out.append((_drv, count, attach_drv, tech_drv))
        out["DRV_LIST"] = l_out

        out["priority_list"] = get_priority_list(current_day)

        if request.POST.get('panel'):
            _flag = request.POST.get('panel')
            _flag = str(_flag).capitalize()
            set_var(f'panel_{request.user.id}', value=request.user.id, flag=_flag)
        out['var_drv_panel'] = get_var(f'panel_{request.user.id}')

    if is_foreman(current_user):
        _foreman = StaffForeman.objects.get(user=current_user).user
        app_for_day = ApplicationToday.objects.filter(construction_site__foreman__user=_foreman, date=current_day)
        out['saved_app_list'] = app_for_day.filter(status=ApplicationStatus.objects.get(status=STATUS_AP['saved']))
    if is_master(current_user):
        _foreman = StaffMaster.objects.get(user=current_user).foreman
        app_for_day = ApplicationToday.objects.filter(construction_site__foreman=_foreman, date=current_day)
        out['saved_app_list'] = app_for_day.filter(status=ApplicationStatus.objects.get(status=STATUS_AP['saved']))

    if is_employee_supply(current_user):
        app_for_day = ApplicationToday.objects.filter(date=current_day)
        out['saved_app_list'] = app_for_day.filter(status=ApplicationStatus.objects.get(status=STATUS_AP['saved']))


    out['today_applications_list'] = []
    for appToday in app_for_day.order_by('construction_site__address'):
        appTech = ApplicationTechnic.objects.filter(app_for_day=appToday)
        out['today_applications_list'].append({'app_today': appToday, 'apps_tech': appTech})
        if appTech.count() == 0:
            appToday.status = ApplicationStatus.objects.get(status=STATUS_AP['absent'])

    if id_user:
        return render(request, "extend/admin_application_foreman.html", out)
    else:
        return render(request, "main.html", out)


def show_application_for_driver(request, day, id_user=None):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)
    if id_user:
        current_user = User.objects.get(id=id_user)
    else:
        current_user = User.objects.get(username=request.user)
    out["current_user"] = current_user

    out["date_of_target"] = current_day.strftime('%d %B')

    applications = ApplicationTechnic.objects.filter(app_for_day__date=current_day,
                                                     technic_driver__driver__driver__user=current_user,
                                                     app_for_day__status=ApplicationStatus.objects.get(
                                                         status=STATUS_AP['send'])).order_by('priority')

    out['applications'] = applications

    if is_admin(request.user):
        return render(request, 'extend/admin_app_for_driver.html', out)
    return render(request, 'applications_for_driver.html', out)

def show_today_applications(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    current_day = convert_str_to_date(day)
    out = {}
    get_prepare_data(out, request, current_day)

    out["date_of_target"] = current_day
    if is_admin(request.user):
        today_technic_applications = ApplicationTechnic.objects.filter(app_for_day__date=current_day)
        out['conflicts_list'] = get_conflicts_vehicles_list(current_day)
    elif is_master(request.user):
        foreman = StaffMaster.objects.get(user=request.user).foreman
        today_technic_applications = ApplicationTechnic.objects.filter(app_for_day__date=current_day)
    elif is_foreman(request.user):
        today_technic_applications = ApplicationTechnic.objects.filter(app_for_day__date=current_day)

    else:
        today_technic_applications = ApplicationTechnic.objects.filter(app_for_day__date=current_day)

    app_tech_day = ApplicationTechnic.objects.filter(
        Q(app_for_day__date=current_day),
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['submitted'])) |
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['approved']))  |
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['send']))
    )
    driver_technic = app_tech_day.values_list('technic_driver__driver__driver__user__last_name',
                                              'technic_driver__technic__name__name').order_by(
        'technic_driver__driver__driver__user__last_name').distinct()
    app_list = []
    for _drv, _tech in driver_technic:
        desc = app_tech_day.filter(technic_driver__driver__driver__user__last_name=_drv,
                                   technic_driver__technic__name__name=_tech).order_by('priority')
        if (_drv, _tech, desc) not in app_list:
            app_list.append((_drv, _tech, desc))
    out["today_technic_applications"] = app_list
    out["priority_list"] = get_priority_list(current_day)

    if request.method == 'POST':
        prior_id_list = request.POST.getlist('prior_id')
        priority_list = request.POST.getlist('priority')
        description_list = request.POST.getlist('descr')

        for id_p, pr, desc in zip(prior_id_list, priority_list, description_list):
            app = ApplicationTechnic.objects.get(id=id_p)
            app.priority = pr
            app.description = desc
            app.save()
        return HttpResponseRedirect(f'/today_app/{day}')
    return render(request, "today_applications.html", out)


def show_info_application(request, id_application):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_application = ApplicationToday.objects.get(id=id_application)

    out["application_id"] = id_application

    out["construction_site"] = current_application.construction_site
    out["date_of_target"] = current_application.date
    get_prepare_data(out, request, selected_day=get_CH_day(current_application.date))

    list_of_vehicles = ApplicationTechnic.objects.filter(app_for_day=current_application)
    out["list_of_vehicles"] = list_of_vehicles
    if is_admin(request.user):
        return render(request, 'extend/admin_show_inf_app.html', out)
    return render(request, "show_info_application.html", out)


def create_new_application(request, id_application):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_user = request.user
    current_application = ApplicationToday.objects.get(id=id_application)
    current_date = current_application.date
    get_prepare_data(out, request, selected_day=get_CH_day(current_application.date))
    out["current_user"] = current_user
    out["construction_site"] = current_application.construction_site
    out["date_of_target"] = str(current_application.date)
    conflicts_vehicles_list = get_conflicts_vehicles_list(current_application.date, 1)
    out['conflicts_vehicles_list'] = conflicts_vehicles_list
    out['work_TD_list'] = get_work_TD_list(current_application.date, 0)
    tech_driver_list = TechnicDriver.objects.filter(date=current_date, status=True)
    tech_name_list = TechnicName.objects.all().order_by('name')
    work_tech_name_list = TechnicDriver.objects.filter(date=current_date, driver__isnull=False, status=True).values_list('technic__name__name').distinct()
    work_tech_name_list = [_[0] for _ in work_tech_name_list]
    out['work_tech_name_list'] = work_tech_name_list

    _tech_drv = []
    for _tech_name in tech_name_list:
        t_d = tech_driver_list.filter(technic__name=_tech_name, driver__isnull=False).values_list('id','driver__driver__user__last_name').order_by('driver__driver__user__last_name')
        _n = _tech_name.name.replace(' ', '').replace('.', '')
        if (_n, _tech_name.name, t_d) not in _tech_drv:
            _tech_drv.append((_n, _tech_name.name, t_d))
    out['D'] = _tech_drv

    _tech_drv2 = []
    for _t_d in tech_driver_list.filter(driver__isnull=False).values_list('id', 'technic__name__name','driver__driver__user__last_name').order_by('driver__driver__user__last_name'):
        _srt_name = _t_d[1].replace(' ', '').replace('.', '')
        _des = (_t_d[0], _srt_name, _t_d[1], _t_d[2])
        if _des not in _tech_drv2:
            _tech_drv2.append(_des)
    out['D2'] = _tech_drv2

    list_of_vehicles = ApplicationTechnic.objects.filter(app_for_day=current_application)
    out["list_of_vehicles"] = list_of_vehicles

    if request.method == "POST":  # ----------------POST
        id_app_tech = request.POST.getlist('io_id_app_tech')
        id_tech_drv_list = request.POST.getlist('io_id_tech_driver')
        vehicle_list = request.POST.getlist('io_technic')
        driver_list = request.POST.getlist('io_driver')###
        description_app_list = request.POST.getlist('description_app_list')

        for i in get_difference(set([i[0] for i in list_of_vehicles.filter().values_list('id')]), set(int(i) for i in id_app_tech)):
            ApplicationTechnic.objects.filter(app_for_day=current_application, id=i).delete()

        work_TD_list_F_saved = get_work_TD_list(current_application.date, 0, True)
        for n, _id in enumerate(id_tech_drv_list):
            if _id == '' and driver_list[n] == '':
                _td = tech_driver_list.filter(technic__name__name=vehicle_list[n]).values_list(
                    'id', 'driver__driver__user__last_name')
                if _td.exclude(id__in=work_TD_list_F_saved).count() == 0:   #if not free td
                    _td_ch = rand_choice(_td)
                    id_tech_drv_list[n] = _td_ch[0]
                    driver_list[n] = _td_ch[1]

                else:
                    id_tech_drv_list[n] = _td.exclude(id__in=work_TD_list_F_saved).first()[0]
                    driver_list[n] = _td.exclude(id__in=work_TD_list_F_saved).first()[1]
                    work_TD_list_F_saved.append(id_tech_drv_list[n])

        _len__id_app_list = len(id_app_tech)
        for i, _id in enumerate(id_app_tech):
            l_of_v = ApplicationTechnic.objects.get(id=int(_id))
            v_d_app = TechnicDriver.objects.get(
                driver__driver__user__last_name=driver_list[i],
                technic__name__name=vehicle_list[i],
                date=current_date,
                status=True)

            l_of_v.technic_driver = v_d_app
            l_of_v.description = description_app_list[i]
            l_of_v.save()

        if len(id_app_tech) < len(vehicle_list):
            n = len(vehicle_list) - _len__id_app_list
            for i in range(0, n):
                tech_drv = TechnicDriver.objects.get(
                    driver__driver__user__last_name=driver_list[_len__id_app_list + i],
                    technic__name__name=vehicle_list[_len__id_app_list + i],
                    date=current_date, status=True)#############
                description = description_app_list[_len__id_app_list + i]
                ApplicationTechnic.objects.create(app_for_day=current_application,
                                                  technic_driver=tech_drv,
                                                  description=description).save()


        if is_admin(request.user):
            current_application.status = ApplicationStatus.objects.get(status=STATUS_AP['submitted'])
        else:
            current_application.status = ApplicationStatus.objects.get(status=STATUS_AP['saved'])
        current_application.save()

        return HttpResponseRedirect(f'/applications/{current_date}')
    return render(request, "create_application.html", out)


def signin_view(request):
    out = {
        'TODAY': TODAY,
        'WEEKDAY_TODAY': WEEKDAY[TODAY.weekday()],
        'err': False
    }

    if request.method == 'POST':
        username = request.POST['username']
        username = str(username).strip(' ')
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/')
        else:
            out['err'] = True
    return render(request, 'signin.html', out)


def del_staff(request, id_staff):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    user = User.objects.get(id=id_staff)
    get_current_post(user).delete()
    user.delete()
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    return HttpResponseRedirect('/show_staff/')


def signup_view(request):
    out = {
        'TODAY': TODAY,
        'WEEKDAY_TODAY': WEEKDAY[TODAY.weekday()],
    }
    foreman_list = StaffForeman.objects.filter().values_list('user_id', 'user__last_name', 'user__first_name')
    out['foreman_list'] = foreman_list
    if request.user.is_anonymous:
        post_list = {'driver': 'Водитель'}
    else:
        post_list = dict_Staff
    out['post_list'] = post_list
    if not request.user.is_anonymous:
        get_prepare_data(out, request)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        first_name = request.POST['first_name']
        telephone = request.POST['telephone']
        last_name = request.POST['last_name']
        post = request.POST['post']
        foreman = request.POST['foreman']

        new_user = User.objects.create_user(username=username, password=password,
                                            first_name=first_name, last_name=last_name,
                                            is_staff=False, is_superuser=False)

        if request.POST['post'] == 'master':
            foreman = StaffForeman.objects.get(user=request.POST['foreman'])
            staff = StaffMaster.objects.create(user=new_user)
            staff.foreman = foreman
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'admin':
            staff = StaffAdmin.objects.create(user=new_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'foreman':
            staff = StaffForeman.objects.create(user=new_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'driver':
            staff = StaffDriver.objects.create(user=new_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'mechanic':
            staff = StaffMechanic.objects.create(user=new_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()
        elif request.POST['post'] == 'employee_supply':
            staff = StaffSupply.objects.create(user=new_user)
            staff.telephone = request.POST.get('telephone')
            staff.save()
        new_user.save()

        if request.user.is_anonymous:
            login(request, new_user)

        return HttpResponseRedirect('/show_staff/')
    return render(request, 'signup.html', out)


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')


# ------------------SUPPORT FUNCTION-------------------------------
def send_all_applications(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    if is_admin(request.user):
        current_day = convert_str_to_date(day)
        current_applications = ApplicationToday.objects.filter(
            status=ApplicationStatus.objects.get(status=STATUS_AP['approved']), date=current_day)
        for app in current_applications:
            app.status = ApplicationStatus.objects.get(status=STATUS_AP['send'])
            app.save()
    return HttpResponseRedirect(f'/applications/{day}')


def approv_all_applications(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    if is_admin(request.user):
        current_day = convert_str_to_date(day)
        current_applications = ApplicationToday.objects.filter(
            status=ApplicationStatus.objects.get(status=STATUS_AP['submitted']), date=current_day)
        for app in current_applications:
            app.status = ApplicationStatus.objects.get(status=STATUS_AP['approved'])
            app.save()
    return HttpResponseRedirect(f'/applications/{day}')


def submitted_all_applications(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    if is_foreman(request.user) or is_master(request.user) or is_employee_supply(request.user):
        current_day = convert_str_to_date(day)
        current_applications = ApplicationToday.objects.filter(
            status=ApplicationStatus.objects.get(status=STATUS_AP['saved']), date=current_day)
        for app in current_applications:
            app.status = ApplicationStatus.objects.get(status=STATUS_AP['submitted'])
            app.save()
    return HttpResponseRedirect(f'/applications/{day}')


def get_priority_list(current_day):
    """
    return ApplicationTechnic_id
    """
    l = []
    app_tech = ApplicationTechnic.objects.filter(app_for_day__date=current_day).values_list('priority', 'technic_driver_id', 'id').order_by('technic_driver_id')
    ll = [(int(a[0]), a[1]) for a in app_tech]
    for _app in set(ll):
        count = ll.count(_app)
        if count > 1:
            _l = [q[0] for q in ApplicationTechnic.objects.filter(app_for_day__date=current_day,
                                                    priority=_app[0],
                                                    technic_driver_id=_app[1]).distinct().values_list('id')]
            l.extend(_l)
    return l


def get_work_TD_list(current_day, c_in=1, F_saved=False):
    out = []
    tech_app_status = ApplicationTechnic.objects.filter(
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['submitted'])) |
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['approved']))
    )
    if F_saved: #if ApplicationTechnic have status = 'saved'
        tech_app_status = tech_app_status.filter(
            Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['saved'])))

    app_list_day = tech_app_status.filter(app_for_day__date=current_day)
    app_list_priority = app_list_day#.filter(priority=1)
    tech_app_today = app_list_priority.values_list('technic_driver')
    _out = [_[0] for _ in tech_app_today]
    for _i in set(_out):
        if _out.count(_i)>c_in:
            out.append(_i)
    return out


def get_conflicts_vehicles_list(current_day, c_in=0, all=False, lack=False):   #applicationtech
    '''
        c_in - количество тех. которое может быть заказано, прежде чем попасть в список
        all - сравнение с всей в том числе нероботающей техникой
        lack - получить количество недостоющей техники
    '''
    out = {}
    l = []
    if all:
        for _a in Technic.objects.all():
            out[_a.name.name] = Technic.objects.filter(name=_a.name).count()
    else:
        for f in Technic.objects.all():
            out[f.name.name] = TechnicDriver.objects.filter(status=True, date=current_day,
                                                            technic__name__name=f.name.name).count()

    app_list_today = ApplicationTechnic.objects.filter(app_for_day__date=current_day)
    app_list_submit_approv = app_list_today.filter(Q(app_for_day__status=ApplicationStatus.objects.get(
                                                           status=STATUS_AP['submitted'])) |
                                                   Q(app_for_day__status=ApplicationStatus.objects.get(
                                                       status=STATUS_AP['approved']))
                                                   )
    app_list_priority = app_list_submit_approv.filter(priority=1)
    app_tech = app_list_priority.values_list('technic_driver', 'technic_driver__technic__name__name')

    work_app_tech_list = [_[1] for _ in app_tech]
    for i in set(work_app_tech_list):
        if work_app_tech_list.count(i)+c_in > out[i]:
            if lack:
                _c = work_app_tech_list.count(i) - out[i]
                l.append((i, _c))
            else:
                l.append(i)
    return l


def get_current_post(user, key=False):
    if is_admin(user):
        current_staff, post = StaffAdmin.objects.get(user=user), 'admin'
    elif is_foreman(user):
        current_staff, post = StaffForeman.objects.get(user=user), 'foreman'
    elif is_master(user):
        current_staff, post = StaffMaster.objects.get(user=user), 'master'
    elif is_driver(user):
        current_staff, post = StaffDriver.objects.get(user=user), 'driver'
    elif is_mechanic(user):
        current_staff, post = StaffMechanic.objects.get(user=user), 'mechanic'
    elif is_employee_supply(user):
        current_staff, post = StaffSupply.objects.get(user=user), 'employee_supply'
    else:
        current_staff, post = None, None
    if key:
        return post
    else:
        return current_staff

def is_admin(user):
    if StaffAdmin.objects.filter(user=user):
        return True
    return False


def is_foreman(user):
    if StaffForeman.objects.filter(user=user):
        return True
    return False


def is_master(user):
    if StaffMaster.objects.filter(user=user):
        return True
    return False


def is_driver(user):
    if StaffDriver.objects.filter(user=user):
        return True
    return False


def is_mechanic(user):
    if StaffMechanic.objects.filter(user=user):
        return True
    return False


def is_employee_supply(user):
    if StaffSupply.objects.filter(user=user):
        return True
    return False


def show_start_page(request):
    if request.user.is_anonymous:
        return HttpResponseRedirect("signin/")
    else:
        if is_admin(request.user):
            return HttpResponseRedirect(f"applications/{get_current_day('next_day')}")
        elif is_foreman(request.user):
            return HttpResponseRedirect(f"applications/{get_current_day('next_day')}")
        elif is_master(request.user):
            return HttpResponseRedirect(f"applications/{get_current_day('next_day')}")
        elif is_driver(request.user):
            return HttpResponseRedirect(f"personal_application/{get_current_day('last_day')}/{request.user.id}")
        elif is_mechanic(request.user):
            return HttpResponseRedirect(f"tech_list/{get_current_day('last_day')}")
        elif is_employee_supply(request.user):
            return HttpResponseRedirect(f"applications/{get_current_day('next_day')}")
        else:
            return HttpResponseRedirect(f"/today_app/{get_current_day('last_day')}")


def get_prepare_data(out: dict, request, current_day=TOMORROW, selected_day: str = 'next_day'):
    if isinstance(current_day, str):
        current_day = convert_str_to_date(current_day)
    out['nw_day'] = str(get_current_day('next_day'))
    out['cw_day'] = str(get_current_day(get_CH_day(current_day)))
    out['lw_day'] = str(get_current_day('last_day'))
    out["WEEKDAY_TODAY"] = WEEKDAY[TODAY.weekday()]
    out['TODAY'] = f'{TODAY.day} {MONTH[TODAY.month-1]}'
    out["DAY"] = f'{current_day.day} {MONTH[current_day.month-1]}'
    out["WEEKDAY"] = WEEKDAY[current_day.weekday()]
    out["post"] = get_current_post(request.user, key=True)

    # out["TOMORROW"] = TOMORROW.strftime('%d %B')
    # out["CH_DAY"] = selected_day
    return out


def success_application(request, id_application):
    """изменение статуса заявки"""
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    current_application = ApplicationToday.objects.get(id=id_application)
    if is_admin(request.user):
        approved = ApplicationStatus.objects.get(status=STATUS_AP['approved'])
        send = ApplicationStatus.objects.get(status=STATUS_AP['send'])
        _status = current_application.status.status

        if _status == STATUS_AP['submitted']:
            current_application.status = approved
        elif _status == STATUS_AP['approved']:
            current_application.status = send
    else:
        current_application.status = ApplicationStatus.objects.get(status=STATUS_AP['submitted'])
    current_application.save()
    return HttpResponseRedirect(f'/applications/{current_application.date}')


def get_current_day(selected_day: str):
    """получить (следующий, текущий, прошлый) рабочий день """
    if selected_day == 'next_day':
        for n in range(1, 14):
            _day = WorkDayTabel.objects.get(date=TODAY+timedelta(n))
            if _day.status:
                return _day.date
    elif selected_day == 'last_day':
        for n in range(14):
            _day = WorkDayTabel.objects.get(date=TODAY - timedelta(n))
            if _day.status:
                return _day.date
    else:
        return selected_day


def get_CH_day(day):
    if str(day) == str(get_current_day('next_day')):
        return 'next_day'
    elif str(day) == str(get_current_day('last_day')):
        return 'last_day'
    else:
        return str(day)


def prepare_driver_table(day):
    current_day = day
    ch_day = get_CH_day(day)
    driver_list = StaffDriver.objects.all()
    if DriverTabel.objects.filter(date=current_day).count() == 0:
        if ch_day == 'next_day':
            try:
                for _drv in DriverTabel.objects.filter(date=TODAY):
                    DriverTabel.objects.create(driver=_drv.driver, date=current_day, status=_drv.status)
            except DriverTabel.DoesNotExist:
                for drv in driver_list:
                    DriverTabel.objects.create(driver=drv, date=current_day)
        else:
            for drv in driver_list:
                DriverTabel.objects.create(driver=drv, date=current_day)


# ---------------------------------------------------------------


def get_var(var, value=False, flag=False):
    try:
        _var = Variable.objects.get(name=var)
        if flag and not value:
            return _var.flag
        elif value and flag:
            return _var.value, _var.flag
        elif value and not flag:
            return _var.value
        else:
            return _var
    except Variable.DoesNotExist:
        return None


def set_var(name, value=None, flag=False):
    _var, _ = Variable.objects.get_or_create(name=name)
    _var.value = value
    _var.flag = flag
    _var.save()
    return _var

def redirect_view(request):
    return render(request, 'REDIRECT.html', {})
