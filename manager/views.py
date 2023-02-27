from django.shortcuts import render
from django.contrib.auth import logout, login, authenticate
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q

from django.contrib.auth.models import User

from manager.models import CloneApplicationTechnic
from manager.models import ApplicationTechnic, ApplicationStatus, ApplicationToday
from manager.models import ConstructionSite, ConstructionSiteStatus
from manager.models import TechnicDriver, DriverTabel
from manager.models import PostName, Post
from manager.models import Technic, TechnicName, TechnicType
from manager.models import WorkDayTabel
from manager.models import Variable
from manager.models import TeleBot

# from manager.forms import CreateNewApplicationForm

# --IMPORT CONST--
from manager.utilities import WEEKDAY
from manager.utilities import TODAY
from manager.utilities import TOMORROW
from manager.utilities import MONTH
from manager.utilities import dict_Staff as POST_USER
from manager.utilities import status_application as STATUS_AP
from manager.utilities import status_constr_site as STATUS_CS
#-----------------
from manager.utilities import get_day_in_days
from manager.utilities import get_difference
from manager.utilities import get_week
from manager.utilities import timedelta
from manager.utilities import choice as rand_choice
from manager.utilities import convert_str_to_date

from manager.utilities import get_json
from manager.utilities import get_id_chat
from manager.utilities import BOT
# ----------------

# ----------PREPARE--------------
# set_locale()

# -------------------------------

# ------FUNCTION VIEW----------------------

def supply_today_app_view(request, day):
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    app_for_day = ApplicationToday.objects.get(construction_site__foreman=None, date=current_day,
                                               construction_site__address='Снабжение')
    _app = ApplicationTechnic.objects.filter(app_for_day=app_for_day)



    app_tech_day = _app.filter(
        # Q(app_for_day__date=current_day),
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['submitted'])) |
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['saved'])) |
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['approved'])) |
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['send']))
    )
    driver_technic = app_tech_day.values_list('technic_driver__driver__driver__last_name',
                                              'technic_driver__technic__name__name').order_by(
        'technic_driver__driver__driver__last_name').distinct()
    app_list = []
    for _drv, _tech in driver_technic:
        desc = app_tech_day.filter(technic_driver__driver__driver__last_name=_drv,
                                   technic_driver__technic__name__name=_tech).order_by('priority')
        _id_list = [_[0] for _ in desc.values_list('id')]
        if (_drv, _tech, desc, _id_list) not in app_list:
            app_list.append((_drv, _tech, desc, _id_list))

    out["today_technic_applications"] = app_list
    out["priority_list"] = get_priority_list(current_day)
    out['conflicts_vehicles_list_id'] = get_conflicts_vehicles_list(current_day, get_id=True)

    if request.method == 'POST':
        prior_id_list = request.POST.getlist('prior_id')
        priority_list = request.POST.getlist('priority')
        description_list = request.POST.getlist('descr')

        for id_p, pr, desc in zip(prior_id_list, priority_list, description_list):
            app = ApplicationTechnic.objects.get(id=id_p)
            app.priority = pr
            app.description = desc
            app.save()

        out['message_status'] = True
        out['message'] = 'Сохранено'


        return HttpResponseRedirect(request.path)
    return render(request, 'supply_today_app.html', out)


def move_supply_app(request, day, id_app):
    cur_app_today = ApplicationToday.objects.get(id=id_app)
    current_day = convert_str_to_date(day)
    _save_status = ApplicationStatus.objects.get(status=STATUS_AP['saved'])
    # print(cur_app_today)
    app_for_day = ApplicationToday.objects.get(construction_site__foreman=None, date=current_day,
                                               construction_site__address='Снабжение')
    supply_list = Post.objects.filter(
        post_name__name_post=POST_USER['employee_supply']).values_list('user_post', flat=True)
    cur_app_tech = ApplicationTechnic.objects.filter(app_for_day=cur_app_today,
                                                     technic_driver__technic__supervisor__in=supply_list)
    for _app_tech in cur_app_tech:
        if _app_tech.var_aptech == 'supply_ok':
            continue
        _id = _app_tech.id
        _app_tech.var_aptech = 'supply_ok'
        _app_tech.save()
        _app_tech.pk = None
        _app_tech.description = f'{_app_tech.app_for_day.construction_site.address} ({_app_tech.app_for_day.construction_site.foreman.last_name})\n{_app_tech.description}'
        _app_tech.app_for_day = app_for_day
        _app_tech.var_aptech = _id
        _app_tech.save()
        app_for_day.status = _save_status
        app_for_day.save()
    return HttpResponseRedirect(f'/supply_app/{day}')


def supply_app_view(request, day):
    out = {}
    current_day = convert_str_to_date(day)
    current_user = request.user
    get_prepare_data(out, request, current_day)

    app_for_day = ApplicationToday.objects.get(construction_site__foreman=None, date=current_day,
                                               construction_site__address='Снабжение')
    out['app_today'] = app_for_day

    apps_tech = ApplicationTechnic.objects.filter(app_for_day=app_for_day)
    out['apps_tech'] = apps_tech.order_by('technic_driver__technic__name__name')
    ##-------------------------------------------
    supply_list = Post.objects.filter(
        post_name__name_post=POST_USER['employee_supply']).values_list('user_post', flat=True)

    app_today_list = ApplicationToday.objects.filter(
        Q(date=current_day),
        Q(status=ApplicationStatus.objects.get(status=STATUS_AP['send'])) |
        Q(status=ApplicationStatus.objects.get(status=STATUS_AP['approved'])) |
        Q(status=ApplicationStatus.objects.get(status=STATUS_AP['submitted']))).exclude(id=app_for_day.id)

    tech_drv = TechnicDriver.objects.filter(date=current_day,
                                            status=True,
                                            driver__status=True,
                                            technic__supervisor__in=supply_list).values_list('id', flat=True)

    app_technic = ApplicationTechnic.objects.filter(app_for_day__in=app_today_list, technic_driver__in=tech_drv)

    out['count_app_list'] = get_count_app_for_driver(current_day)
    out['today_applications_list'] = []

    for _app_today in app_today_list:
        appTech = app_technic.filter(app_for_day=_app_today)
        if appTech:
            out['today_applications_list'].append((_app_today, appTech))

    return render(request, 'extend/supply_app.html', out)



def del_technic(request, id_tech):
    if is_admin(request.user) or is_mechanic(request.user):
        _technic = Technic.objects.get(id=id_tech)
        _technic.delete()
    return HttpResponseRedirect('/technic_list/')


def show_technic_view(request):
    out = {}
    get_prepare_data(out, request)
    all_technic_list = Technic.objects.all()
    out['all_technic_list'] = all_technic_list.order_by('name__name')
    return render(request, 'show_technic_list.html', out)


def edit_technic_view(request, id_tech=None):
    out = {}
    get_prepare_data(out, request)
    if id_tech:
        _technic = Technic.objects.get(id=id_tech)
        out['tech'] = _technic
    _attach_drv = Post.objects.filter(post_name__name_post=POST_USER['driver'])#.values_list('user_post', flat=True)
    out['attach_drv'] = _attach_drv.order_by('user_post__last_name')

    _director_drv_list = User.objects.all()
    out['director_drv'] = _director_drv_list.order_by('last_name')

    _name_technic = TechnicName.objects.all()
    out['name_technic'] = _name_technic.order_by('name')

    _type_technic = TechnicType.objects.all()
    out['type_technic'] = _type_technic.order_by('name')

    if request.method == 'POST':
        if request.POST.get('id_tech'):
            _id = request.POST.get('id_tech')
            _technic = Technic.objects.get(id=_id)
        else:
            _technic = Technic.objects.create()

        _t_name = request.POST.get('name_tech')
        t_name = TechnicName.objects.get(id=_t_name)

        _t_type = request.POST.get('type_tech')
        t_type = TechnicType.objects.get(id=_t_type)

        if request.POST.get('att_drv_tech'):
            _t_attr_drv = request.POST.get('att_drv_tech')
            t_attr_drv = User.objects.get(id=_t_attr_drv)
        else:
            t_attr_drv = None


        t_desc = request.POST.get('description')
        t_iden_inf = request.POST.get('iden_inf')

        if request.POST.get('director_drv_tech'):
            _t_direct = request.POST.get('director_drv_tech')
            t_direct = User.objects.get(id=_t_direct)

        else:
            t_direct = None

        _technic.name = t_name
        _technic.tech_type = t_type
        _technic.attached_driver = t_attr_drv
        _technic.description = t_desc
        _technic.id_information = t_iden_inf
        _technic.supervisor = t_direct
        _technic.save()

        return HttpResponseRedirect('/technic_list/')

    return render(request, 'edit_technic.html', out)


def copy_app_view(request, id_application):
    out = {}
    _app_for_day = ApplicationToday.objects.get(id=id_application)
    current_day = _app_for_day.date
    get_prepare_data(out, request, current_day)
    _app_technic = ApplicationTechnic.objects.filter(app_for_day=_app_for_day)
    if is_admin(request.user):
        _status = ApplicationStatus.objects.get(status=STATUS_AP['submitted'])
    else:
        _status = ApplicationStatus.objects.get(status=STATUS_AP['saved'])

    if current_day != get_current_day('next_day'):
        next_app_for_day, _ = ApplicationToday.objects.get_or_create(date=get_current_day('next_day'),
                                                                     construction_site=_app_for_day.construction_site)
        next_app_for_day.status = _status
        next_app_for_day.save()

        for _apptech in _app_technic:
            if DriverTabel.objects.filter(date=get_current_day('next_day'),
                                          status=True, driver=_apptech.technic_driver.driver.driver).count() != 0:
                _drv_tab = DriverTabel.objects.get(date=get_current_day('next_day'),
                                                   status=True, driver__user=_apptech.technic_driver.driver.driver.user)

                if TechnicDriver.objects.filter(status=True,
                                                date=get_current_day('next_day'),
                                                driver=_drv_tab,
                                                technic=_apptech.technic_driver.technic).count() != 0:
                    _technic_driver = TechnicDriver.objects.get(status=True,
                                                                technic=_apptech.technic_driver.technic,
                                                                date=get_current_day('next_day'),
                                                                driver=_drv_tab)
                    _td, _ = ApplicationTechnic.objects.get_or_create(app_for_day=next_app_for_day,
                                                                      description=_apptech.description,
                                                                      technic_driver=_technic_driver)
                    _td.save()
                else:
                    continue
            else:
                continue
    return HttpResponseRedirect(f'/applications/{current_day}')


def append_in_hos_tech(request, id_drv):
    _driver_table = DriverTabel.objects.get(id=id_drv)
    status = _driver_table.status
    date = _driver_table.date
    driver = _driver_table.driver
    if not status:
        return HttpResponseRedirect(f'/applications/{date}')


    constr_site, _ = ConstructionSite.objects.get_or_create(
        address='Спец. задание',
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
    foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman'])
    app_list = []
    for _fman in foreman_list:
        _app = ApplicationToday.objects.filter(date=current_day, construction_site__foreman=_fman.user_post)
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
                                                     technicdriver__status=True).distinct().order_by('driver__last_name')
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
    out['tech_app_list'] = tech_app_list.order_by('technic_driver__driver__driver__last_name')
    out['conflicts_vehicles_list'] = get_conflicts_vehicles_list(current_day, 1)
    out['work_TD_list'] = get_work_TD_list(current_day, 0)

    vehicle_and_driver = TechnicDriver.objects.filter(date=current_day, driver__isnull=False, status=True).values_list(
        'technic__name__name',
        'driver__driver__last_name',
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
                    driver__driver__last_name=request.POST.get(f"driver_{app_id}"),
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

    conflicts_vehicles_list_id = get_conflicts_vehicles_list(current_day, get_id=True)
    out['conflicts_vehicles_list_id'] = conflicts_vehicles_list_id

    today_technic_applications_list = []
    for v in conflict_list:
        today_technic_applications = ApplicationTechnic.objects.filter(app_for_day__date=current_day,
                                                                       technic_driver__technic__name__name=v,
                                                                       technic_driver__status=True).values(
            'id',
            'technic_driver__driver__driver__last_name',
            'description',
            'app_for_day__construction_site__foreman__last_name',
            'app_for_day__construction_site__address',
            'technic_driver_id'
        ).order_by('app_for_day__construction_site__foreman__last_name').exclude(var_aptech='supply_ok')
        today_technic_applications_list.append((v, today_technic_applications))
    out['today_technic_applications'] = today_technic_applications_list

    return render(request, 'conflict_resolution.html', out)


# CONSTRURTION SITE------------------------------------------------------------------------CONSTRURTION SITE------------
def show_construction_sites_view(request):
    out = {}
    get_prepare_data(out, request)

    all_constr_site_list = ConstructionSite.objects.all().order_by('address').exclude(address=None, foreman=None)

    if is_admin(request.user):
        construction_sites_list = all_constr_site_list
    elif is_foreman(request.user):
        construction_sites_list = all_constr_site_list.filter(foreman=request.user)
    elif is_master(request.user):
        foreman = Post.objects.get(user_post=request.user).supervisor
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
        staff_list = Post.objects.filter(
            post_name__name_post=POST_USER['foreman']).values_list('user_post_id', 'user_post__last_name', 'user_post__first_name')
    elif is_foreman(request.user):

        staff_list = Post.objects.filter(user_post=request.user).values_list('user_post_id', 'user_post__last_name', 'user_post__first_name')
    elif is_master(request.user):
        staff_list = Post.objects.filter(
            user_post=request.user).values_list('supervisor_id', 'supervisor__last_name', 'supervisor__first_name')
    else:
        return HttpResponseRedirect('/')

    out["staff_list"] = staff_list
    out["construction_sites"] = construction_sites

    if request.method == 'POST':
        construction_sites.address = request.POST['construction_site_address']
        construction_sites.foreman = User.objects.get(id=request.POST['foreman'])
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
        staff_list = Post.objects.filter(
            post_name__name_post=POST_USER['foreman']).values_list('user_post_id', 'user_post__last_name', 'user_post__first_name')
    elif is_foreman(request.user):
        staff_list = Post.objects.filter(user_post=request.user,
            post_name__name_post=POST_USER['foreman']).values_list('user_post_id', 'user_post__last_name',
                                                                   'user_post__first_name')
    elif is_master(request.user):
        staff_list = Post.objects.filter(user_post=request.user).values_list('supervisor_id', 'supervisor__last_name', 'supervisor__first_name')
    else:
        return HttpResponseRedirect('/')

    out["staff_list"] = staff_list
    if request.method == 'POST':
        construction_sites = ConstructionSite.objects.create()
        construction_sites.address = request.POST['construction_site_address']
        if request.POST.get('foreman'):
            foreman_id = request.POST.get('foreman')
            construction_sites.foreman = User.objects.get(id=foreman_id)
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
        if get_current_post(_user):
            _post = POST_USER[get_current_post(_user)]
        else:
            _post = None
        _tel = get_current_post(_user)
        _user_post.append((_user, _post, _tel))
    out['telecon'] = TeleBot.objects.all()
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

    current_post = Post.objects.get(user_post=id_staff)
    out['current_post'] = current_post

    post_list = PostName.objects.all()
    out['post_list'] = post_list

    foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman']).order_by('user_post__last_name')
    out['foreman_list'] = foreman_list

    if is_master(current_user):
        out['current_foreman'] = Post.objects.get(user_post=current_user).supervisor

    if request.method == 'POST':
        selected_user = User.objects.get(id=id_staff)
        selected_post = Post.objects.get(user_post=selected_user)

        post_id = request.POST.get('post')
        if post_id:
            selected_post_name = PostName.objects.get(id=post_id)
        else:
            selected_post_name = None
        supervisor_id = request.POST.get('foreman')
        if supervisor_id:
            supervisor = User.objects.get(id=supervisor_id)
        else:
            supervisor = None
        tel = request.POST.get('telephone')

        selected_post.post_name = selected_post_name
        selected_post.supervisor = supervisor
        selected_post.telephone = tel
        selected_post.save()

        selected_user.username = request.POST.get('username')
        selected_user.first_name = request.POST.get('first_name')
        selected_user.last_name = request.POST.get('last_name')
        if request.POST['new_password'] == 'true':
            selected_user.set_password(request.POST['password'])
        else:
            selected_user.password = request.POST['password']
        selected_user.save()
        if not get_current_post(selected_user):
            return HttpResponseRedirect('/')
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
    out['driver_list'] = driver_today_tabel.order_by('driver__last_name')


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
        out['message_status'] = True
        out['message'] = 'Сохранено'

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

    if WorkDayTabel.objects.filter(date=current_week[0]).count() == 0:
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
        out['message_status'] = True
        out['message'] = 'Сохранено'
        # return HttpResponseRedirect(f'/tabel_workday/{ch_week}')

    return render(request, 'tabel_workday.html', out)


def Technic_Driver_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    if DriverTabel.objects.filter(date=current_day, status=True).count() == 0:
        prepare_driver_table(day)

    if TechnicDriver.objects.filter(date=current_day).count() == 0:
        prepare_technic_driver_table(day)
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

    work_driver_list = DriverTabel.objects.filter(date=current_day, status=True)
    technic_driver_list = TechnicDriver.objects.filter(date=current_day)
    out['technic_driver_list'] = technic_driver_list.order_by('technic__name__name')
    out['work_driver_list'] = work_driver_list.order_by('driver__last_name')

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
        out['message_status'] = True
        out['message'] = 'Сохранено'

    if 'tech_list' in request.path:
        return render(request, 'tech_list.html', out)
    else:
        return render(request, 'technic_driver.html', out)

#-----------------------------------------------------TABEL-------------------------------------------------------------


def clear_application_view(request, id_application):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    current_application = ApplicationToday.objects.get(id=id_application)
    app_tech = ApplicationTechnic.objects.filter(app_for_day=current_application)

    for _app in app_tech:
        if _app.var_aptech:
            try:
                _a_tmp = ApplicationTechnic.objects.get(id=_app.var_aptech)
                _a_tmp.var_aptech = None
                _a_tmp.save()
            except:
                pass
        _app.delete()

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
        out['conflicts_vehicles_list_id'] = get_conflicts_vehicles_list(current_day, get_id=True)
        if ApplicationToday.objects.filter(date=current_day,
                                           status=ApplicationStatus.objects.get(
                                               status=STATUS_AP['submitted'])).count() != 0:
            out['submitted_app_list'] = True
        if ApplicationToday.objects.filter(date=current_day,
                                           status=ApplicationStatus.objects.get(
                                               status=STATUS_AP['approved'])).count() != 0:
            out['send_app_list'] = True

        driver_table_list = DriverTabel.objects.filter(date=current_day)

        var_sort_driver_panel = get_var('var_sort_driver_panel', user=request.user)
        if var_sort_driver_panel and var_sort_driver_panel.value:
            dr_tab_l_ord = driver_table_list.order_by(f'{var_sort_driver_panel.value}')

        else:
            dr_tab_l_ord = driver_table_list.order_by('driver__last_name')

        l_out = []
        try:
            for _drv in dr_tab_l_ord:
                app = ApplicationTechnic.objects.filter(technic_driver__driver=_drv)
                tech_drv = TechnicDriver.objects.filter(driver=_drv)
                attach_drv = Technic.objects.filter(attached_driver=_drv.driver).values_list('name__name')
                count = app.count()
                if not _drv in [_[0] for _ in l_out]:
                    l_out.append((_drv, count, attach_drv, tech_drv))
        except:
            for _drv in driver_table_list.order_by('driver__last_name'):
                app = ApplicationTechnic.objects.filter(technic_driver__driver=_drv)
                tech_drv = TechnicDriver.objects.filter(driver=_drv)
                attach_drv = Technic.objects.filter(attached_driver=_drv.driver).values_list('name__name')
                count = app.count()
                if not _drv in [_[0] for _ in l_out]:
                    l_out.append((_drv, count, attach_drv, tech_drv))

        out["DRV_LIST"] = l_out

        out["priority_list"] = get_priority_list(current_day)

        if request.POST.get('panel'):
            _flag = request.POST.get('panel')
            _flag = str(_flag).capitalize()
            set_var('hidden_panel', value=request.user.id, flag=_flag, user=request.user)
        out['var_drv_panel'] = get_var('hidden_panel', user=request.user)

    elif is_foreman(current_user):
        # _foreman = StaffForeman.objects.get(user=current_user).user
        app_for_day = ApplicationToday.objects.filter(construction_site__foreman=current_user, date=current_day)
        out['saved_app_list'] = app_for_day.filter(status=ApplicationStatus.objects.get(status=STATUS_AP['saved']))

    elif is_master(current_user):
        _foreman = Post.objects.get(user_post=current_user).supervisor
        app_for_day = ApplicationToday.objects.filter(construction_site__foreman=_foreman, date=current_day)
        out['saved_app_list'] = app_for_day.filter(status=ApplicationStatus.objects.get(status=STATUS_AP['saved']))

    elif is_employee_supply(current_user):  #TODO:del
        app_for_day = ApplicationToday.objects.filter(construction_site__foreman=None,
                                                      date=current_day,
                                                      construction_site__address='Снабжение')
        out['saved_app_list'] = app_for_day.filter(status=ApplicationStatus.objects.get(status=STATUS_AP['saved']))
    else:
        return HttpResponseRedirect('/')

    out['style_font_color'] = get_var('style_font_color', user=request.user)

    out['today_applications_list'] = []
    for appToday in app_for_day.order_by('construction_site__address'):
        appTech = ApplicationTechnic.objects.filter(app_for_day=appToday)

        out['today_applications_list'].append({'app_today': appToday, 'apps_tech': appTech})

        if appTech.count() == 0:
            appToday.status = ApplicationStatus.objects.get(status=STATUS_AP['absent'])
    out['count_app_list'] = get_count_app_for_driver(current_day)

    if id_user:
        return render(request, "extend/admin_application_foreman.html", out)
    else:
        return render(request, "main.html", out)


def show_application_for_driver(request, day, id_user):
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
                                                     technic_driver__driver__driver=current_user,
                                                     app_for_day__status=ApplicationStatus.objects.get(
                                                         status=STATUS_AP['send'])).order_by('priority')

    out['applications'] = applications

    if is_admin(request.user) or is_master(request.user) or is_foreman(request.user):
        return render(request, 'extend/admin_app_for_driver.html', out)
    return render(request, 'applications_for_driver.html', out)

def show_today_applications(request, day, id_foreman=None):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    current_day = convert_str_to_date(day)
    out = {}
    get_prepare_data(out, request, current_day)
    out["date_of_target"] = current_day
    foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman'])
    out['foreman_list'] = foreman_list

    if is_admin(request.user):
        out['conflicts_list'] = get_conflicts_vehicles_list(current_day)

    _filter = get_var('filter_today_app', value=True, user=request.user)


    if id_foreman == 0:
        _app = ApplicationTechnic.objects.filter(app_for_day__date=current_day)
        set_var('filter_today_app', value=None, user=request.user)
    elif id_foreman:
        _app = ApplicationTechnic.objects.filter(app_for_day__construction_site__foreman=id_foreman,
                                                 app_for_day__date=current_day)
        if id_foreman != _filter:
            set_var('filter_today_app', value=id_foreman, user=request.user)
    else:
        if _filter:
            _app = ApplicationTechnic.objects.filter(app_for_day__construction_site__foreman_id=_filter,
                                                     app_for_day__date=current_day)
        else:
            _app = ApplicationTechnic.objects.filter(app_for_day__date=current_day)


    app_tech_day = _app.filter(
        # Q(app_for_day__date=current_day),
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['submitted'])) |
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['approved'])) |
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['send']))
    ).exclude(var_aptech='supply_ok')

    driver_technic = app_tech_day.values_list('technic_driver__driver__driver__last_name',
                                              'technic_driver__technic__name__name').order_by(
        'technic_driver__driver__driver__last_name').distinct()
    app_list = []
    for _drv, _tech in driver_technic:
        desc = app_tech_day.filter(technic_driver__driver__driver__last_name=_drv,
                                   technic_driver__technic__name__name=_tech).order_by('priority')
        _id_list = [_[0] for _ in desc.values_list('id')]
        if (_drv, _tech, desc, _id_list) not in app_list:
            app_list.append((_drv, _tech, desc, _id_list))

    out["today_technic_applications"] = app_list
    out["priority_list"] = get_priority_list(current_day)
    out['conflicts_vehicles_list_id'] = get_conflicts_vehicles_list(current_day, get_id=True)

    if request.method == 'POST':
        prior_id_list = request.POST.getlist('prior_id')
        priority_list = request.POST.getlist('priority')
        description_list = request.POST.getlist('descr')

        for id_p, pr, desc in zip(prior_id_list, priority_list, description_list):
            app = ApplicationTechnic.objects.get(id=id_p)
            app.priority = pr
            app.description = desc
            app.save()
        out['message_status'] = True
        out['message'] = 'Сохранено'
        # return HttpResponseRedirect(f'/today_app/{day}')
    return render(request, "today_applications.html", out)


def show_info_application(request, id_application):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_application = ApplicationToday.objects.get(id=id_application)

    out["application_id"] = id_application

    out["construction_site"] = current_application.construction_site
    out["date_of_target"] = current_application.date
    get_prepare_data(out, request, current_day=current_application.date)

    list_of_vehicles = ApplicationTechnic.objects.filter(app_for_day=current_application)
    out["list_of_vehicles"] = list_of_vehicles.order_by('technic_driver__technic__name')
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
    check_table(str(current_date))
    get_prepare_data(out, request, current_day=current_date)
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
        t_d = tech_driver_list.filter(technic__name=_tech_name, driver__isnull=False, status=True, driver__status=True).values_list('id', 'driver__driver__last_name').order_by('driver__driver__last_name')
        _n = _tech_name.name.replace(' ', '').replace('.', '')
        if (_n, _tech_name.name, t_d) not in _tech_drv:
            _tech_drv.append((_n, _tech_name.name, t_d))
    out['D'] = _tech_drv

    _tech_drv2 = []
    for _t_d in tech_driver_list.filter(driver__isnull=False).values_list('id', 'technic__name__name','driver__driver__last_name').order_by('driver__driver__last_name'):
        _srt_name = _t_d[1].replace(' ', '').replace('.', '')
        _des = (_t_d[0], _srt_name, _t_d[1], _t_d[2])
        if _des not in _tech_drv2:
            _tech_drv2.append(_des)
    out['D2'] = _tech_drv2

    list_of_vehicles = ApplicationTechnic.objects.filter(app_for_day=current_application)
    out["list_of_vehicles"] = list_of_vehicles.order_by('technic_driver__technic__name')

    if request.method == "POST":  # ----------------POST
        id_app_tech = request.POST.getlist('io_id_app_tech')
        id_tech_drv_list = request.POST.getlist('io_id_tech_driver')
        vehicle_list = request.POST.getlist('io_technic')
        driver_list = request.POST.getlist('io_driver')###
        description_app_list = request.POST.getlist('description_app_list')

        ##------------delete--------------

        for i in get_difference(set([i[0] for i in list_of_vehicles.filter().values_list('id')]), set(int(i) for i in id_app_tech)):
            _app = ApplicationTechnic.objects.get(app_for_day=current_application, id=i)
            if _app.var_aptech:
                try:
                    _a_tmp = ApplicationTechnic.objects.get(id=_app.var_aptech)
                    _a_tmp.var_aptech = None
                    _a_tmp.save()
                except: pass
            _app.delete()
        ##--------------------------------

        work_TD_list_F_saved = get_work_TD_list(current_application.date, 0, True)
        for n, _id in enumerate(id_tech_drv_list):
            if _id == '' and driver_list[n] == '':
                _td = tech_driver_list.filter(technic__name__name=vehicle_list[n], driver__isnull=False).values_list(
                    'id', 'driver__driver__last_name')
                if _td.exclude(id__in=work_TD_list_F_saved).count() == 0:   #if not free td
                    _td_ch = rand_choice(_td)
                    id_tech_drv_list[n] = _td_ch[0]
                    driver_list[n] = _td_ch[1]

                else:
                    _tmp = rand_choice(_td.exclude(id__in=work_TD_list_F_saved))
                    id_tech_drv_list[n] = _tmp[0]
                    driver_list[n] = _tmp[1]
                    work_TD_list_F_saved.append(id_tech_drv_list[n])

        _len__id_app_list = len(id_app_tech)
        for i, _id in enumerate(id_app_tech):
            l_of_v = ApplicationTechnic.objects.get(id=int(_id))
            v_d_app = TechnicDriver.objects.get(id=id_tech_drv_list[i])

            l_of_v.technic_driver = v_d_app
            l_of_v.description = description_app_list[i]
            l_of_v.save()

        if len(id_app_tech) < len(vehicle_list):
            n = len(vehicle_list) - _len__id_app_list
            for i in range(0, n):
                tech_drv = TechnicDriver.objects.get(
                    driver__driver__last_name=driver_list[_len__id_app_list + i],
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
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    out = {
        'TODAY': TODAY,
        'WEEKDAY_TODAY': WEEKDAY[TODAY.weekday()],

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
            out['message_status'] = True
            out['message'] = 'Неверный логин или пороль'
    return render(request, 'signin.html', out)


def del_staff(request, id_staff):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    user = User.objects.get(id=id_staff)
    post = Post.objects.get(user_post=user)
    post.delete()
    user.delete()
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    return HttpResponseRedirect('/show_staff/')


def signup_view(request):
    out = {
        'TODAY': TODAY,
        'WEEKDAY_TODAY': WEEKDAY[TODAY.weekday()],
    }

    foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman'])
    out['foreman_list'] = foreman_list
    if request.user.is_anonymous:
        post_list = None
    else:
        post_list = PostName.objects.all()
    out['post_list'] = post_list
    if not request.user.is_anonymous:
        get_prepare_data(out, request)

    if request.method == 'POST':
        username = request.POST['username']
        if User.objects.filter(username=username).count() == 0:

            password = request.POST['password']
            first_name = request.POST['first_name']
            telephone = request.POST['telephone']
            last_name = request.POST['last_name']
            post_id = request.POST.get('post')
            foreman_id = request.POST.get('foreman')

            new_user = User.objects.create_user(username=username, password=password,
                                                first_name=first_name, last_name=last_name,
                                                is_staff=False, is_superuser=False)


            if post_id:
                post_name = PostName.objects.get(id=post_id)
            else:
                post_name = None
            if foreman_id:
                foreman = User.objects.get(id=foreman_id)
            else:
                foreman = None
            _count_post = Post.objects.all().count()+1
            Post.objects.create(id=_count_post,
                                user_post=new_user,
                                post_name=post_name,
                                telephone=telephone,
                                supervisor=foreman)

            if request.user.is_anonymous:
                login(request, new_user)

            if not post_id and not is_admin(request.user):
                return HttpResponseRedirect('/')
            return HttpResponseRedirect('/show_staff/')
        else:
            out['message_status'] = True
            out['message'] = 'Такой пользователь уже существует'
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
        send_task_for_drv(day)#####################
        send_status_app_for_foreman(day)#######
        send_message_for_admin(day)
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
    app_tech = ApplicationTechnic.objects.filter(
        app_for_day__date=current_day).values_list('priority', 'technic_driver_id', 'id').order_by('technic_driver_id').exclude(
        var_aptech='supply_ok')
    ll = [(int(a[0]), a[1]) for a in app_tech]
    for _app in set(ll):
        count = ll.count(_app)
        if count > 1:
            _l = [q[0] for q in ApplicationTechnic.objects.filter(app_for_day__date=current_day,
                                                    priority=_app[0],
                                                    technic_driver_id=_app[1]).exclude(
        var_aptech='supply_ok').distinct().values_list('id')]
            l.extend(_l)
    print(l)
    return l


def get_work_TD_list(current_day, c_in=1, F_saved=False):
    out = []
    tech_app_status = ApplicationTechnic.objects.filter(
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['submitted'])) |
        Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['approved']))
    )
    if F_saved: #if ApplicationTechnic have status = 'saved'
        tech_app_status = ApplicationTechnic.objects.filter(
            Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['submitted'])) |
            Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['approved'])) |
            Q(app_for_day__status=ApplicationStatus.objects.get(status=STATUS_AP['saved'])))


    app_list_day = tech_app_status.filter(app_for_day__date=current_day)
    app_list_priority = app_list_day#.filter(priority=1)
    tech_app_today = app_list_priority.values_list('technic_driver')
    _out = [_[0] for _ in tech_app_today]
    for _i in set(_out):
        if _out.count(_i)>c_in:
            out.append(_i)
    return out


def get_conflicts_vehicles_list(current_day, c_in=0, all=False, lack=False, get_id=False):   #applicationtech
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
                                                            technic__name__name=f.name.name,
                                                            driver__status=True).count()#################
    # excl_const_site = ConstructionSite.objects.get(address=None, foreman=None)

    # app_list_today = ApplicationTechnic.objects.filter(app_for_day__date=current_day).exclude(technic_driver__status=False)
    app_list_today = ApplicationTechnic.objects.filter(app_for_day__date=current_day).exclude(
        Q(technic_driver__status=False) |
        Q(var_aptech='supply_ok'))

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

    if get_id:
        l_id = []
        for _app in app_list_today:
            if _app.technic_driver.technic.name.name in l:
                l_id.append(_app.id)
        return l_id
    return l


def get_count_app_for_driver(current_day):
    out = []
    _status_approved = ApplicationStatus.objects.get(status=STATUS_AP['approved'])
    _status_send = ApplicationStatus.objects.get(status=STATUS_AP['send'])
    _tech_drv = [_[0] for _ in TechnicDriver.objects.filter(date=current_day, status=True, driver__status=True).values_list('id')]
    _app = [_[0] for _ in ApplicationTechnic.objects.filter(Q(app_for_day__date=current_day),
                                                            Q(app_for_day__status=_status_approved) |
                                                            Q(app_for_day__status=_status_send)
                                                            ).values_list('technic_driver_id')]
    for _td in set(_tech_drv):
        _coun = _app.count(_td)
        out.append((_td, _coun))
    return out

def get_current_post(user):
    if is_admin(user):
        post = 'admin'
    elif is_foreman(user):
        post = 'foreman'
    elif is_master(user):
        post = 'master'
    elif is_driver(user):
        post = 'driver'
    elif is_mechanic(user):
        post = 'mechanic'
    elif is_employee_supply(user):
        post = 'employee_supply'
    else:
        post = None

    return post


def is_admin(user):
    if Post.objects.filter(user_post=user, post_name__name_post=POST_USER['admin']):
        return True
    return False


def is_foreman(user):
    if Post.objects.filter(user_post=user, post_name__name_post=POST_USER['foreman']):
        return True
    return False


def is_master(user):
    if Post.objects.filter(user_post=user, post_name__name_post=POST_USER['master']):
        return True
    return False


def is_driver(user):
    if Post.objects.filter(user_post=user, post_name__name_post=POST_USER['driver']):
        return True
    return False


def is_mechanic(user):
    if Post.objects.filter(user_post=user, post_name__name_post=POST_USER['mechanic']):
        return True
    return False


def is_employee_supply(user):
    if Post.objects.filter(user_post=user, post_name__name_post=POST_USER['employee_supply']):
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
            # return HttpResponseRedirect(f"supply_app/{get_current_day('next_day')}")
            return HttpResponseRedirect(f"applications/{get_current_day('next_day')}")
        else:
            return HttpResponseRedirect(f"/today_app/{get_current_day('last_day')}")


def get_prepare_data(out: dict, request, current_day=TOMORROW):
    if isinstance(current_day, str):
        current_day = convert_str_to_date(current_day)
    out['message_status'] = False
    out['nw_day'] = str(get_current_day('next_day'))
    out['cw_day'] = str(get_current_day(get_CH_day(current_day)))
    out['lw_day'] = str(get_current_day('last_day'))
    out["WEEKDAY_TODAY"] = WEEKDAY[TODAY.weekday()]
    out['TODAY'] = f'{TODAY.day} {MONTH[TODAY.month-1]}'
    out["DAY"] = f'{current_day.day} {MONTH[current_day.month-1]}'
    out["WEEKDAY"] = WEEKDAY[current_day.weekday()]
    out["post"] = get_current_post(request.user)
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
    driver_list = Post.objects.filter(post_name__name_post=POST_USER['driver'])
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


def prepare_technic_driver_table(day):
    current_day = convert_str_to_date(day)
    work_driver_list = DriverTabel.objects.filter(date=current_day, status=True)
    tech_drv_list_today = TechnicDriver.objects.filter(date=TODAY)

    if get_CH_day(day) == 'next_day':
        for _tech in Technic.objects.all():
            _drv = tech_drv_list_today.filter(technic=_tech).values_list('driver__driver__last_name', 'status')
            driver = _drv[0][0]
            status = _drv[0][1]

            c_drv = work_driver_list.filter(driver__last_name=driver)

            if c_drv.count() != 0:
                TechnicDriver.objects.create(technic=_tech,
                                             driver=DriverTabel.objects.get(date=current_day,
                                                                            driver__last_name=driver),
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


# ---------------------------------------------------------------


def get_var(var, value=False, flag=False, user=None):
    try:
        _var = Variable.objects.get(name=var, user=user)
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


def set_var(name, value=None, flag=False, user=None):
    _var, _ = Variable.objects.get_or_create(name=name,user=user)
    _var.value = value
    _var.flag = flag
    _var.save()
    return _var

def connect_bot_view(request, id_user):
    out = {}
    get_prepare_data(out, request)
    current_user = User.objects.get(id=id_user)
    out['current_user'] = current_user
    telebot, _ = TeleBot.objects.get_or_create(user_bot=current_user)
    if not _:
        _result = get_json()
        key = f"kp{id_user}"
        id_chat = get_id_chat(key=key, result=_result)
        if id_chat:
            telebot.id_chat = id_chat
            telebot.save()


    out['telebot'] = telebot
    return render(request, 'bot_connect.html', out)

def test_bot(request, id_user):
    tel_bot = TeleBot.objects.get(user_bot=id_user)
    id_chat = tel_bot.id_chat
    BOT.send_message(id_chat, 'test message')
    return HttpResponseRedirect(f'/connect_bot_view/{id_user}')

def send_message(id_user, message):
    if TeleBot.objects.filter(user_bot=id_user).count() != 0:
        chat_id = TeleBot.objects.get(user_bot=id_user)
        if chat_id and chat_id.id_chat:
            BOT.send_message(chat_id.id_chat, message)


def send_task_for_drv(current_day):
    out = []
    _status = ApplicationStatus.objects.get(status=STATUS_AP['send'])
    _driver_list = DriverTabel.objects.filter(date=current_day, status=True)

    for _id_drv in _driver_list:
        _app = ApplicationTechnic.objects.filter(app_for_day__date=current_day,
                                                 technic_driver__driver__driver=_id_drv.driver.id,
                                                 app_for_day__status=_status).order_by('priority')
        out.append((_id_drv, _app))

    for drv, app in out:
        mss = f"{drv.driver.last_name} {drv.driver.first_name}\nЗаявка на {current_day}\n\n"
        for s in app:
            mss += f"\t{s.priority}) {s.app_for_day.construction_site.address} ({s.app_for_day.construction_site.foreman})\n"
            mss += f"{s.description}\n\n"

        send_message(drv.driver.id, mss)

def send_status_app_for_foreman(current_day):
    out = []
    _status = ApplicationStatus.objects.get(status=STATUS_AP['send'])
    id_list = Post.objects.filter(
        Q(post_name__name_post=POST_USER['foreman']) |
        Q(post_name__name_post=POST_USER['master']) |
        Q(post_name__name_post=POST_USER['employee_supply'])
    ).values_list('user_post_id', flat=True)

    _app = ApplicationToday.objects.filter(date=current_day, status=_status)


    for _id in id_list:
        _a = _app.filter(construction_site__foreman_id=_id)
        if _a:
            out.append((_id, _a))

    for _id, app in out:
        mss = f"{current_day}\n\n"
        for a in app:
            mss += f"Заявка на [ {a.construction_site.address} ] одобрена\n"

        send_message(_id, mss)


def send_message_for_admin(current_day):
    admin_id_list = Post.objects.filter(post_name__name_post=POST_USER['admin']).values_list('user_post_id', flat=True)
    mess = f"Заявки на {current_day}\n\n отправлены"
    for _id in admin_id_list:
        send_message(_id, mess)

def setting_view(request):
    out = {}
    get_prepare_data(out, request)
    current_user = request.user
    setting_list = Variable.objects.filter(user=current_user)
    out['setting_list'] = setting_list
    if request.method == 'POST':
        setting_id_list = request.POST.getlist('setting_id')
        if setting_id_list:
            for n, _id in enumerate(setting_id_list, 1):
                var = Variable.objects.get(id=_id, user=current_user)
                value = request.POST.get(f"setting_value_{n}")
                if request.POST.get(f"setting_flag_{n}"):
                    flag = True
                else:
                    flag = False
                var.value = value
                var.flag = flag
                var.save()

    return render(request, 'setting_page.html', out)


def check_table(day):
    date = convert_str_to_date(day)

    if DriverTabel.objects.filter(date=date).count() == 0:
        prepare_driver_table(day)

    if TechnicDriver.objects.filter(date=date).count() == 0:
        prepare_technic_driver_table(day)
