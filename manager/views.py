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
from manager.models import ApplicationMeterial

# from manager.forms import CreateNewApplicationForm

# --IMPORT CONST--
from manager.utilities import WEEKDAY
from manager.utilities import TODAY
from manager.utilities import TOMORROW
from manager.utilities import MONTH
from manager.utilities import dict_Staff as POST_USER
from manager.utilities import status_application as STATUS_AP
from manager.utilities import status_constr_site as STATUS_CS
from manager.utilities import variable as VAR
from manager.utilities import text_templates as TEXT_TEMPLATES
from manager.utilities import colors as COLOR_LIST
# -----------------
from manager.utilities import get_day_in_days
# from manager.utilities import get_difference
from manager.utilities import get_week
from manager.utilities import timedelta
from manager.utilities import choice as rand_choice
from manager.utilities import convert_str_to_date

from manager.utilities import check_time as NOW_IN_TIME
from manager.utilities import NOW
from manager.utilities import get_json
from manager.utilities import get_id_chat
from manager.utilities import BOT
# ----------------

# ----------PREPARE--------------

# STATUS application_today------------------------------------------------------------------
STATUS_APP_absent = ApplicationStatus.objects.get_or_create(status=STATUS_AP['absent'])[0]
STATUS_APP_saved = ApplicationStatus.objects.get_or_create(status=STATUS_AP['saved'])[0]
STATUS_APP_submitted = ApplicationStatus.objects.get_or_create(status=STATUS_AP['submitted'])[0]
STATUS_APP_approved = ApplicationStatus.objects.get_or_create(status=STATUS_AP['approved'])[0]
STATUS_APP_send = ApplicationStatus.objects.get_or_create(status=STATUS_AP['send'])[0]
# STATUS construction_site------------------------------------------------------------------
STATUS_CS_closed = ConstructionSiteStatus.objects.get_or_create(status=STATUS_CS['closed'])[0]
STATUS_CS_opened = ConstructionSiteStatus.objects.get_or_create(status=STATUS_CS['opened'])[0]
# ------------------------------------------------------------------------------------------



# ------FUNCTION VIEW----------------------


def notice_submitt(request, current_day):
    out = []
    id_foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman'])
    id_master_list = Post.objects.filter(post_name__name_post=POST_USER['master'])
    id_supply_list = Post.objects.filter(post_name__name_post=POST_USER['employee_supply'])

    _app = ApplicationToday.objects.filter(date=current_day, status=STATUS_APP_saved)

    for _id in id_foreman_list:
        _a = _app.filter(construction_site__foreman=_id.user_post)
        if _a:
            out.append((_id.user_post.id, _a))

    for _id in id_master_list:
        _a = _app.filter(construction_site__foreman=_id.supervisor)
        if _a:
            out.append((_id.user_post.id, _a))

    for _id, app in out:
        mss = f"НАПОМИНАНИЕ\n\n"
        for a in app:
            mss += f"У вас имеется не поданная заявка: [ {a.construction_site.address} ]\n"

        send_message(_id, mss)
    return HttpResponseRedirect('/')


def print_material_view(request, day):
    out = {}
    current_day = convert_str_to_date(day)
    current_application = ApplicationToday.objects.filter(
        Q(date=current_day),
        Q(status=STATUS_APP_submitted) |
        Q(status=STATUS_APP_approved) |
        Q(status=STATUS_APP_send)
    )
    app_material = ApplicationMeterial.objects.filter(app_for_day__in=current_application)

    _font_size = get_var(VAR['font_size'], user=request.user)
    if _font_size and _font_size.value.isnumeric():
        out['font_size'] = _font_size.value
    else:
        out['font_size'] = 10

    out['materials_list'] = app_material.values(
        'id',
        'app_for_day__construction_site__address',
        'app_for_day__construction_site__foreman__last_name',
        'description'
    )

    return render(request, 'print_page.html', out)


def supply_materials_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    current_application = ApplicationToday.objects.filter(
        Q(date=current_day),
        Q(status=STATUS_APP_submitted) |
        Q(status=STATUS_APP_approved) |
        Q(status=STATUS_APP_send)
    )

    app_material = ApplicationMeterial.objects.filter(app_for_day__in=current_application)
    if all(app_material.values_list('status_checked', flat=True)):
        _status0 = True

    else:
        _status0 = False
    out['status_checked'] = _status0

    out['materials_list'] = app_material.values(
        'id',
        'app_for_day__construction_site__address',
        'app_for_day__construction_site__foreman__last_name',
        'description',
        'status_checked'
    )

    if request.method == 'POST':
        try:
            _id_list = request.POST.getlist('materials_id')
            _desc_list = request.POST.getlist('materials_description')
            for _id, _desc in zip(_id_list, _desc_list):
                _app = ApplicationMeterial.objects.get(id=_id)
                _desc = str(_desc).strip()
                if _app.description != _desc:
                    if _desc == '':
                        _app.delete()
                    else:
                        _app.description = _desc
                        _app.status_checked = True
                        _app.save()
                elif _app.description == _desc:
                    _app.status_checked = True
                    _app.save()
                elif not _desc:
                    _app.delete()
        except ApplicationMeterial.DoesNotExist:
            pass

        return HttpResponseRedirect(request.path)
    return render(request, 'extend/supply_app_materials.html', out)


def supply_today_app_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    app_for_day = ApplicationToday.objects.get(
        construction_site__foreman=None,
        date=current_day,
        construction_site__address='Снабжение')
    _app = ApplicationTechnic.objects.filter(app_for_day=app_for_day)

    app_tech_day = _app.filter(
        Q(app_for_day__status=STATUS_APP_submitted) |
        Q(app_for_day__status=STATUS_APP_saved) |
        Q(app_for_day__status=STATUS_APP_approved) |
        Q(app_for_day__status=STATUS_APP_send)
    )

    driver_technic = app_tech_day.values_list(
        'technic_driver__driver__driver__last_name',
        'technic_driver__technic__name__name').order_by('technic_driver__driver__driver__last_name').distinct()

    app_list = []
    for _drv, _tech in driver_technic:
        desc = app_tech_day.filter(
            technic_driver__driver__driver__last_name=_drv,
            technic_driver__technic__name__name=_tech).order_by('priority')
        _id_list = [_[0] for _ in desc.values_list('id')]

        if (_drv, _tech, desc, _id_list) not in app_list:
            app_list.append((_drv, _tech, desc, _id_list))

    out["today_technic_applications"] = app_list
    out["priority_list"] = get_priority_list(current_day)
    out['conflicts_vehicles_list_id'] = get_conflicts_vehicles_list(current_day)

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


def cancel_supply_app(request, id_app):
    temp_str = TEXT_TEMPLATES['dismiss']
    _app_tech = ApplicationTechnic.objects.get(id=id_app)
    if not _app_tech.var_check:
        _tmp_desc = _app_tech.description
        _app_tech.description = temp_str + _tmp_desc
        _app_tech.var_check = True
        _app_tech.save()
    elif temp_str in _app_tech.description:
        _tmp_desc = _app_tech.description
        _app_tech.description = _tmp_desc.replace(temp_str, '')
        _app_tech.var_check = False
        _app_tech.save()

    return HttpResponseRedirect('/')

def move_supply_app(request, day, id_app):
    current_day = convert_str_to_date(day)
    app_for_day = ApplicationToday.objects.get(
        construction_site__foreman=None,
        date=current_day,
        construction_site__address=TEXT_TEMPLATES['constr_site_supply_name'])

    supply_list = Post.objects.filter(
        post_name__name_post=POST_USER['employee_supply']).values_list('user_post', flat=True)

    cur_app_tech = ApplicationTechnic.objects.get(id=id_app)
    if not cur_app_tech.var_check:
        _id = cur_app_tech.id
        cur_app_tech.var_check = True
        cur_app_tech.save()
        cur_app_tech.pk = None
        cur_app_tech.var_check = False
        cur_app_tech.description = f'{cur_app_tech.app_for_day.construction_site.address} ({cur_app_tech.app_for_day.construction_site.foreman.last_name})\r\n{cur_app_tech.description}'
        cur_app_tech.app_for_day = app_for_day
        cur_app_tech.var_ID_orig = _id
        cur_app_tech.save()
        app_for_day.status = STATUS_APP_saved
        app_for_day.save()
    else:
        if TEXT_TEMPLATES['dismiss'] in cur_app_tech.description:
            cur_app_tech.description = cur_app_tech.description.replace(TEXT_TEMPLATES['dismiss'], '')
        cur_app_tech.var_check = False
        cur_app_tech.save()

    return HttpResponseRedirect('/')


def supply_app_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    check_table(day)
    out = {}
    current_day = convert_str_to_date(day)
    current_user = request.user
    get_prepare_data(out, request, current_day)
    status_day = check_table(current_day)
    out['status_day'] = status_day

    app_for_day = ApplicationToday.objects.filter(
        construction_site__foreman=None,
        date=current_day,
        construction_site__address=TEXT_TEMPLATES['constr_site_supply_name'])

    out['apps_today'] = app_for_day

    # if request.POST.get('panel'):
    #     _flag = request.POST.get('panel')
    #     _flag = str(_flag).capitalize()
    #     set_var('supply_panel', value=request.user.id, flag=_flag, user=request.user)

    out['var_supply_panel'] = get_var(VAR['panel_for_supply'], user=request.user)

    apps_tech = ApplicationTechnic.objects.filter(app_for_day__in=app_for_day)
    out['apps_tech'] = apps_tech.order_by('technic_driver__technic__name__name')

    # -------------------------------------------

    supply_list = Post.objects.filter(
        post_name__name_post=POST_USER['employee_supply']).values_list('user_post', flat=True)

    app_today_list = ApplicationToday.objects.filter(
        Q(date=current_day),
        Q(status=STATUS_APP_approved) |
        Q(status=STATUS_APP_submitted)
    ).exclude(construction_site__foreman=None, construction_site__address=TEXT_TEMPLATES['constr_site_supply_name'])

    tech_drv = TechnicDriver.objects.filter(
        date=current_day,
        status=True,
        driver__status=True,
        technic__supervisor__in=supply_list
    ).values_list('id', flat=True)

    app_technic = ApplicationTechnic.objects.filter(
        app_for_day__in=app_today_list,
        technic_driver__in=tech_drv)

    out['count_app_list'] = get_count_app_for_driver(current_day)
    out['conflicts_vehicles_list_id'] = get_conflicts_vehicles_list(current_day)

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
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    get_prepare_data(out, request)
    all_technic_list = Technic.objects.all()
    out['all_technic_list'] = all_technic_list.order_by('name__name')

    return render(request, 'show_technic_list.html', out)


def edit_technic_view(request, id_tech=None):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    get_prepare_data(out, request)

    if id_tech:
        _technic = Technic.objects.get(id=id_tech)
        out['tech'] = _technic

    _attach_drv = Post.objects.filter(post_name__name_post=POST_USER['driver'])
    out['attach_drv'] = _attach_drv.order_by('user_post__last_name')

    _director_drv_list = Post.objects.filter(
        post_name__name_post=POST_USER['mechanic']).values_list('user_post_id', flat=True)
    out['director_drv'] = User.objects.filter(id__in=_director_drv_list)

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
        _status = STATUS_APP_submitted
    else:
        _status = STATUS_APP_saved

    if current_day != get_current_day('next_day'):
        next_app_for_day, _ = ApplicationToday.objects.get_or_create(
            date=get_current_day('next_day'),
            construction_site=_app_for_day.construction_site)
        next_app_for_day.status = _status
        next_app_for_day.save()

        for _apptech in _app_technic:
            if DriverTabel.objects.filter(
                    date=get_current_day('next_day'),
                    status=True,
                    driver=_apptech.technic_driver.driver.driver).count() != 0:
                _drv_tab = DriverTabel.objects.get(
                    date=get_current_day('next_day'),
                    status=True,
                    driver=_apptech.technic_driver.driver.driver)

                if TechnicDriver.objects.filter(
                        status=True,
                        date=get_current_day('next_day'),
                        driver=_drv_tab,
                        technic=_apptech.technic_driver.technic).count() != 0:
                    _technic_driver = TechnicDriver.objects.get(
                        status=True,
                        technic=_apptech.technic_driver.technic,
                        date=get_current_day('next_day'),
                        driver=_drv_tab)
                    _td, _ = ApplicationTechnic.objects.get_or_create(
                        app_for_day=next_app_for_day,
                        description=_apptech.description,
                        technic_driver=_technic_driver)
                    _td.save()
                else:
                    continue
            else:
                continue
    return HttpResponseRedirect(f'/applications/{current_day}')


def append_in_spec_tech(request, id_drv):
    _driver_table = DriverTabel.objects.get(id=id_drv)
    status = _driver_table.status
    date = _driver_table.date
    driver = _driver_table.driver

    var_message, _ = Variable.objects.get_or_create(name='DEF_MESS_FOR_SPEC')
    if not var_message.value:
        message = TEXT_TEMPLATES['default_mess_for_spec']
    else:
        message = var_message.value

    if not status:
        return HttpResponseRedirect(f'/applications/{date}')


    constr_site, _ = ConstructionSite.objects.get_or_create(
        address=TEXT_TEMPLATES['constr_site_spec_name'],
        foreman=None)
    constr_site.status = STATUS_CS_opened
    constr_site.save()

    app_for_day, _ = ApplicationToday.objects.get_or_create(
        construction_site=constr_site,
        date=date)
    app_for_day.status = STATUS_APP_submitted
    app_for_day.save()

    technic_driver = TechnicDriver.objects.filter(
        driver=_driver_table,
        date=date,
        driver__status=True
    ).first()

    ApplicationTechnic.objects.get_or_create(
        app_for_day=app_for_day,
        technic_driver=technic_driver,
        description=message
    )

    return HttpResponseRedirect(f"/applications/{date}")


def foreman_app_list_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
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
        app_for_day__status=STATUS_APP_send).exclude(var_check=True)

    current_driver_list = DriverTabel.objects.filter(
        status=True,
        date=current_day,
        technicdriver__status=True).distinct().order_by('driver__last_name')

    app_list = []
    for drv in current_driver_list:
        _app = current_app_tech.filter(technic_driver__driver=drv).order_by('priority')
        app_list.append((drv, _app))

    out['app_list'] = app_list

    return render(request, 'driver_app_list.html', out)


def get_id_app_from_tech_name(request, day, id_tech_name):
    if is_admin(request.user):
        current_day = convert_str_to_date(day)

        _technic_name = TechnicName.objects.get(id=id_tech_name)
        id_applications = ApplicationTechnic.objects.filter(
            app_for_day__date=current_day,
            technic_driver__status=True,
            # technic_driver__driver__status=True,
            var_check=False,
            technic_driver__technic__name=_technic_name
        ).values_list('id', flat=True)

        return conflict_correction_view(request, day, id_applications)
    return HttpResponseRedirect('/')


def conflict_correction_view(request, day, id_applications):
    if not is_admin(request.user):
        return HttpResponseRedirect('/')
    out = {}
    if isinstance(id_applications, str):
        id_application_list = id_applications.split(',')[:-1]
    else:
        id_application_list = id_applications
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    driver_table_list = DriverTabel.objects.filter(date=current_day)
    technic_driver_table = TechnicDriver.objects.filter(date=current_day)
    _Application_technic = ApplicationTechnic.objects.filter(id__in=id_application_list)
    _Tech_driver_list = technic_driver_table.filter(
        status=True,
        driver__status=True
    )
    _tech_driver_name_id_list = _Tech_driver_list.values_list('technic__name_id', flat=True).distinct()
    _Technic_name_list = TechnicName.objects.filter(id__in=_tech_driver_name_id_list)
    out['technic_name_list'] = _Technic_name_list.order_by('name')

    out['tech_driver_list'] = []
    for _tn in _Technic_name_list:
        _td = _Tech_driver_list.filter(technic__name=_tn).values('id', 'driver__driver__last_name')
        out['tech_driver_list'].append((_tn, _td))

    tech_name_list = _Application_technic.values_list(
        'technic_driver__technic__name_id',
        'technic_driver__technic__name__name').distinct()


    for tn in tech_name_list:
        all_t = technic_driver_table.filter(technic__name__id=tn[0])
        work_t = all_t.filter(status=True)
        all_c = all_t.count()
        work_c = work_t.count()
        free_td_id = get_free_tech_driver_list(current_day=current_day, technic_name=tn[0])
        free_td = technic_driver_table.filter(id__in=free_td_id).values_list('driver__driver__last_name', 'driver__driver__first_name')
        out['tech_inf'] = (tn[1], all_c, work_c, all_c - work_c, free_td)


    out["date_of_target"] = current_day
    out['conflicts_vehicles_list'] = get_conflicts_vehicles_list(current_day, c_in=1)
    out['conflicts_list'] = get_conflicts_vehicles_list(current_day, c_in=0)
    priority_list = get_priority_list(current_day)
    out['priority_list'] = priority_list
    out['work_TD_list'] = get_work_TD_list(current_day, c_in=0)
    out['free_tech_name'] = get_free_tech_driver_list(current_day=current_day)
    out['tech_app_list'] = _Application_technic.order_by('technic_driver__driver__driver__last_name')

    out['prior_color'] = {}
    ds = _Application_technic.filter(
        technic_driver_id__in=get_priority_list(current_day, get_td_id=True)).values_list('technic_driver_id', flat=True)
    for pr in ds:
        clr = rand_choice(COLOR_LIST)
        if clr not in out['prior_color'].values():
            out['prior_color'][pr] = clr
        else:
            COLOR_LIST.remove(clr)
            out['prior_color'][pr] = rand_choice(COLOR_LIST)

    l_out = []

    for _drv in driver_table_list.order_by('driver__last_name'):
        app = ApplicationTechnic.objects.filter(technic_driver__driver=_drv)
        tech_drv = technic_driver_table.filter(driver=_drv)
        if not tech_drv:
            tech_drv = technic_driver_table.filter(technic__attached_driver=_drv.driver.id)
        attach_drv = Technic.objects.filter(attached_driver=_drv.driver).values_list('name__name')
        count = app.count()

        if not _drv in [_[0] for _ in l_out]:
            l_out.append((_drv, count, attach_drv, tech_drv))

    out["DRV_LIST"] = l_out

    if request.method == 'POST':
        app_technic_id_list = request.POST.getlist('id_list')

        for _id_app_tech in app_technic_id_list:
            _app = ApplicationTechnic.objects.get(id=_id_app_tech)
            if request.POST.get(f"technic_driver_{_id_app_tech}"):
                _app.technic_driver = TechnicDriver.objects.get(id=request.POST.get(f"technic_driver_{_id_app_tech}"))
                _app.var_check = request.POST.get(f"io_app_tech_var_chack_{_id_app_tech}")
                if request.POST.get(f"description_{_id_app_tech}"):
                    _app.description = str(request.POST.get(f"description_{_id_app_tech}")).strip()
                else:
                    _app.description = None
                _app.priority = request.POST.get(f"priority_{_id_app_tech}")
                _app.save()
            else:
                _app.delete()
        if out['conflicts_vehicles_list']:
            return HttpResponseRedirect(f'/conflict_resolution/{day}')
        else:
            return HttpResponseRedirect(f'/applications/{day}')
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
        tech_name = TechnicName.objects.get(id=v).name
        today_technic_applications = ApplicationTechnic.objects.filter(
            app_for_day__date=current_day,
            technic_driver__technic__name__id=v,
            technic_driver__status=True).values(
            'id',
            'technic_driver__driver__driver__last_name',
            'description',
            'app_for_day__construction_site__foreman__last_name',
            'app_for_day__construction_site__address',
            'technic_driver_id',
            'technic_driver__technic__name__name'
        ).order_by('technic_driver__driver__driver__last_name').exclude(var_check=True)

        today_technic_applications_list.append((tech_name, today_technic_applications))
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
        status=STATUS_CS_opened)

    out["constr_sites_list_close"] = construction_sites_list.filter(
        status=STATUS_CS_closed)

    return render(request, 'construction_sites.html', out)


def edit_construction_sites_view(request, id_construction_sites):
    out = {}
    get_prepare_data(out, request)
    construction_sites = ConstructionSite.objects.get(id=id_construction_sites)

    if is_admin(request.user):
        staff_list = Post.objects.filter(
            post_name__name_post=POST_USER['foreman']).values_list(
            'user_post_id',
            'user_post__last_name',
            'user_post__first_name')

    elif is_foreman(request.user):
        staff_list = Post.objects.filter(user_post=request.user).values_list(
            'user_post_id',
            'user_post__last_name',
            'user_post__first_name')

    elif is_master(request.user):
        staff_list = Post.objects.filter(user_post=request.user).values_list(
            'supervisor_id',
            'supervisor__last_name',
            'supervisor__first_name')

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

    if constr_site.status == STATUS_CS_opened:
        constr_site.status = STATUS_CS_closed
    else:
        constr_site.status = STATUS_CS_opened
    constr_site.save()
    return HttpResponseRedirect('/construction_sites/')


def add_construction_sites_view(request):
    out = {}
    get_prepare_data(out, request)

    if is_admin(request.user):
        staff_list = Post.objects.filter(
            post_name__name_post=POST_USER['foreman']).values_list(
            'user_post_id',
            'user_post__last_name',
            'user_post__first_name')

    elif is_foreman(request.user):
        staff_list = Post.objects.filter(
            user_post=request.user,
            post_name__name_post=POST_USER['foreman']).values_list(
            'user_post_id',
            'user_post__last_name',
            'user_post__first_name')

    elif is_master(request.user):
        staff_list = Post.objects.filter(user_post=request.user).values_list(
            'supervisor_id',
            'supervisor__last_name',
            'supervisor__first_name')

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

        construction_sites.status = STATUS_CS_opened
        construction_sites.save()

        return HttpResponseRedirect('/construction_sites/')
    return render(request, 'edit_construction_site.html', out)

##-------------------------------------------------CONSTRURTION SITE--------------------------------------------------

# STAFF-------------------------------------------------------------------------------------STAFF--------------------


def show_staff_view(request):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    out = {}
    get_prepare_data(out, request)
    if is_mechanic(request.user):
        _post = Post.objects.filter(post_name__name_post=POST_USER['driver']).values_list('user_post_id', flat=True)
        staff_list = User.objects.filter(id__in=_post).order_by('last_name')
    else:
        staff_list = User.objects.all().order_by('last_name')

    _user_post = []
    for _user in staff_list:
        if get_current_post(_user):
            _post = POST_USER[get_current_post(_user)]
        else:
            _post = None
        try:
            _tel = Post.objects.get(user_post=_user).telephone#get_current_post(_user)
        except:
            _tel = ''
        _user_post.append((_user, _post, _tel))

    out['telecon'] = TeleBot.objects.all()
    out['user_post'] = _user_post
    out['staff_list'] = staff_list
    if is_mechanic(request.user):
        return render(request, 'show_driver_staff.html', out)

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

        if request.POST.get('telephone'):
            tel = str(request.POST.get('telephone')).strip()
        else:
            tel = ''

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

# STAFF-----------------------------------------------STAFF-------------------------------------------------------------

# TABEL----------------------------------------------------------------------------------------TABEL--------------------


def tabel_driver_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    # prepare_driver_table(day)
    _exc_post = Post.objects.filter(post_name__name_post=POST_USER['driver']).exclude(
        user_post__id__in=DriverTabel.objects.filter(date=TODAY).values_list('driver__id', flat=True)
    ).exists()

    if not DriverTabel.objects.filter(date=current_day).exists() or _exc_post:
        prepare_driver_table(day)

    if not TechnicDriver.objects.filter(date=current_day).exists():
        prepare_technic_driver_table(day)
    else:
        technic_driver_list = TechnicDriver.objects.filter(date=current_day)


    driver_today_tabel = DriverTabel.objects.filter(date=current_day)
    out['driver_list'] = driver_today_tabel.order_by('driver__last_name')

    if request.POST.getlist('staff_id'):
        id_driver_list = request.POST.getlist('staff_id')
        for n, staff_id in enumerate(id_driver_list, 1):
            if request.POST.get(f'staff_status_{n}'):
                st = DriverTabel.objects.get(id=staff_id)
                st.status = True
                _td = technic_driver_list.filter(driver=None, technic__attached_driver=st.driver)
                _td.update(driver=st)
                st.save()
            else:
                st = DriverTabel.objects.get(id=staff_id)
                st.status = False
                _td = technic_driver_list.filter(driver=staff_id)
                _td.update(driver=None)
                st.save()

        return HttpResponseRedirect(request.path)

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
    prepare_work_day_table(_day)

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

        return HttpResponseRedirect(request.path)
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
                if not _attach_drv:
                    continue
                _attach_drv_staff = DriverTabel.objects.get(driver=_attach_drv, date=current_day)
                if _attach_drv_staff.status:
                    _td.driver = _attach_drv_staff
                    _td.save()
                else:
                    _td.driver = None
                    _td.save()

    work_driver_list = DriverTabel.objects.filter(date=current_day, status=True)
    out['work_driver_list'] = work_driver_list.order_by('driver__last_name')
    technic_driver_list = TechnicDriver.objects.filter(date=current_day)
    out['technic_driver_list'] = technic_driver_list.order_by('technic__name__name')

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

        return HttpResponseRedirect(request.path)

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
    current_day = convert_str_to_date(current_application.date)

    for _app in app_tech:
        try:
            _a_tmp = ApplicationTechnic.objects.get(id=_app.var_ID_orig)
            _a_tmp.var_check = False
            _a_tmp.save()
        except ApplicationTechnic.DoesNotExist:
            pass
        _app.delete()
    try:
        ApplicationMeterial.objects.get(app_for_day=current_application).delete()
    except ApplicationMeterial.DoesNotExist:
        pass
    current_application.description = ''
    current_application.status = STATUS_APP_absent
    current_application.save()

    return HttpResponseRedirect(f'/applications/{current_day}')

# ===============================================================================================
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
    status_day = check_table(current_day)
    out['status_day'] = status_day
    # ---------------------------------------
    _Application_today = ApplicationToday.objects.filter(date=current_day)
    _Application_technic = ApplicationTechnic.objects.filter(app_for_day__date=current_day)
    _Application_material = ApplicationMeterial.objects.filter(app_for_day__date=current_day)
    # ---------------------------------------

    if request.POST.get('filter'):
        # technics, all, materials
        _filter = request.POST.get('filter')
        set_var(VAR['FILTER_main_page'], value=_filter, user=request.user)
    var_filter_apps = get_var(VAR['FILTER_main_page'], user=request.user)
    out['var_filter_apps'] = var_filter_apps

    _var_reload_main_page = get_var(VAR['TIMEOUT_main_page'])
    out["var_reload_main_page"] = _var_reload_main_page

    _var_cache = get_var(VAR['cache'])
    out["var_cache"] = _var_cache.flag

    _var_sent_app = Variable.objects.filter(name=VAR['sent_app'], date=current_day)
    if _var_sent_app.exists():
        out['var_sent_app'] = _var_sent_app.first()

    if request.POST.get('td_from') and request.POST.get('td_to'):
        td_from = request.POST.get('td_from')
        td_to = request.POST.get('td_to')

        _app = _Application_technic.filter(technic_driver_id=td_from)
        _app_td = _Application_today.filter(applicationtechnic__technic_driver_id=td_from)
        _app_td.update(status=STATUS_APP_submitted)
        _app.update(technic_driver=td_to)

    else:
        print('NONE')

    if is_admin(current_user):
        app_for_day = _Application_today.filter(
            Q(Q(status=STATUS_APP_submitted) |
                Q(status=STATUS_APP_approved) |
                Q(status=STATUS_APP_send)
              ))

        # out['conflicts_technic_name'] = get_conflicts_vehicles_list(current_day)
        out['conflicts_vehicles_list_id'] = get_conflicts_vehicles_list(current_day)

        if _Application_today.filter(status=STATUS_APP_submitted).exists():
            out['submitted_app_list'] = True

        if _Application_today.filter(status=STATUS_APP_approved).exists():
            out['send_app_list'] = True

        driver_table_list = DriverTabel.objects.filter(date=current_day)
        technic_driver_table = TechnicDriver.objects.filter(date=current_day)
        var_sort_driver_panel = get_var(VAR['sort_drv_panel'], user=request.user)

        if var_sort_driver_panel and var_sort_driver_panel.value:
            dr_tab_l_ord = driver_table_list.order_by(f'{var_sort_driver_panel.value}')
        else:
            dr_tab_l_ord = driver_table_list.order_by('driver__last_name')

        l_out = []
        try:
            for _drv in dr_tab_l_ord:
                app = _Application_technic.filter(technic_driver__driver=_drv)
                tech_drv = technic_driver_table.filter(driver=_drv)
                if not tech_drv:
                    tech_drv = technic_driver_table.filter(technic__attached_driver=_drv.driver)
                attach_drv = Technic.objects.filter(attached_driver=_drv.driver).values_list('name__name')
                count = app.count()

                if not _drv in [_[0] for _ in l_out]:
                    l_out.append((_drv, count, attach_drv, tech_drv))
        except:
            for _drv in driver_table_list.order_by('driver__last_name'):
                app = _Application_technic.filter(technic_driver__driver=_drv)
                tech_drv = technic_driver_table.filter(driver=_drv)
                if not tech_drv:
                    tech_drv = technic_driver_table.filter(technic__attached_driver=_drv.driver.id)
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

        saved_ap_list = _Application_today.filter(
            status=STATUS_APP_saved).order_by('construction_site__foreman__last_name')

        if saved_ap_list.exists():
            out['inf_btn_status'] = True
            out['inf_btn_content'] = TEXT_TEMPLATES['message_not_submitted']
            out['saved_ap_list'] = saved_ap_list

        materials_list = _Application_material.filter(status_checked=True)

        out['technic_driver_table_TT'] = technic_driver_table.filter(
            status=True, driver__status=True).order_by('driver__driver__last_name')

        out['app_technic_today'] = _Application_technic.values(
            'technic_driver_id',
            'technic_driver__driver__driver__last_name',
            'technic_driver__technic__name__name'
        ).distinct().order_by('technic_driver__driver__driver__last_name')

    elif is_foreman(current_user):
        app_for_day = _Application_today.filter(construction_site__foreman=current_user)
        out['saved_app_list'] = app_for_day.filter(status=STATUS_APP_saved)
        materials_list = _Application_material.filter(app_for_day__in=app_for_day)

    elif is_master(current_user):
        _foreman = Post.objects.get(user_post=current_user).supervisor
        app_for_day = _Application_today.filter(construction_site__foreman=_foreman)
        out['saved_app_list'] = app_for_day.filter(status=STATUS_APP_saved)
        materials_list = _Application_material.filter(app_for_day__in=app_for_day)

    else:
        return HttpResponseRedirect('/')

    out['style_font_color'] = get_var(VAR['font_color_main_page'], user=request.user)
    out['today_applications_list'] = []

    if var_filter_apps:
        filtr = var_filter_apps.value
    else:
        filtr = 'all'
    if 'technics' in filtr:
        for appToday in app_for_day.order_by('construction_site__address'):
            appTech = _Application_technic.filter(app_for_day=appToday)
            out['today_applications_list'].append({'app_today': appToday, 'apps_tech': appTech})

    elif 'materials' in filtr:
        for appToday in app_for_day.order_by('construction_site__address'):
            appMater = materials_list.filter(
                app_for_day=appToday).values_list('description', flat=True).first()
            out['today_applications_list'].append({'app_today': appToday, 'app_mater': appMater})
    else:
        for appToday in app_for_day.order_by('construction_site__address'):
            appTech = _Application_technic.filter(app_for_day=appToday)
            appMater = materials_list.filter(
                app_for_day=appToday).values_list('description', flat=True).first()
            out['today_applications_list'].append({'app_today': appToday, 'apps_tech': appTech, 'app_mater': appMater})


    out['count_app_list'] = get_count_app_for_driver(current_day)

    if id_user:
        return render(request, "extend/admin_application_foreman.html", out)
    else:
        return render(request, "main.html", out)

# ===============================================================================================
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

    id_supply_list = Post.objects.filter(
        post_name__name_post=POST_USER['employee_supply']).values_list('user_post_id', flat=True)

    supply_driver_id_list = Post.objects.filter(supervisor_id__in=id_supply_list).values_list('user_post_id', flat=True)

    if current_user.id in supply_driver_id_list:
        app_material_list = ApplicationMeterial.objects.filter(
            app_for_day__date=current_day,
            status_checked=True
        )
        out['material_list'] = app_material_list
    else:
        print('no')

    out["current_user"] = current_user
    out["date_of_target"] = current_day.strftime('%d %B')
    applications = ApplicationTechnic.objects.filter(
        app_for_day__date=current_day,
        technic_driver__driver__driver=current_user,
        app_for_day__status=STATUS_APP_send).order_by('priority').exclude(var_check=True)
    out['applications'] = applications

    _var_reload_drv_page = get_var('reload_drv_page')
    out["var_reload_drv_page"] = _var_reload_drv_page

    if is_admin(request.user) or is_master(request.user) or is_foreman(request.user):
        return render(request, 'extend/admin_app_for_driver.html', out)

    return render(request, 'applications_for_driver.html', out)


def show_today_applications(request, day, filter_foreman=None, filter_csite=None):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    current_day = convert_str_to_date(day)
    out = {}
    get_prepare_data(out, request, current_day)
    out["date_of_target"] = current_day

    _FILTER = get_var(VAR['FILTER_APP_TODAY'], value=True, user=request.user)
    if not _FILTER:
        _FILTER = ['all', 'all']    # foreman, constr_site
    else:
        _FILTER = _FILTER.split(',')

    if filter_foreman:
        if filter_foreman == 'current':
            pass
        elif filter_foreman != _FILTER[0]:
            _FILTER[0] = filter_foreman
        if filter_csite != _FILTER[1]:
            _FILTER[1] = filter_csite
        set_var(VAR['FILTER_APP_TODAY'], value=f"{_FILTER[0]},{_FILTER[1]}", user=request.user)

    foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman'])
    out['foreman_list'] = foreman_list

    _application_today = ApplicationToday.objects.filter(date=current_day)

    if str(_FILTER[0]) == 'supply':
        application_today = _application_today.filter(
            construction_site__address=TEXT_TEMPLATES['constr_site_supply_name'])
        out['filter'] = TEXT_TEMPLATES['constr_site_supply_name']

    elif str(_FILTER[0]).isnumeric():
        _id_foreman = int(_FILTER[0])
        application_today = _application_today.filter(construction_site__foreman_id=_id_foreman)
        out['filter'] = User.objects.get(id=_id_foreman).last_name

        constr_site = application_today.exclude(
            status=STATUS_APP_absent).values(
            'construction_site_id',
            'construction_site__address'
        )
        out['constr_site'] = constr_site

        try:
            id_constr_site = int(_FILTER[1])
            application_today = application_today.filter(construction_site_id=id_constr_site)
            out['filter_constr_site'] = application_today.values_list('construction_site__address', flat=True)[0]
        except ValueError:
            out['filter_constr_site'] = 'Все'

    else:
        application_today = _application_today
        out['filter'] = 'Все'

    if 'materials' in request.path:
        _application_materials = ApplicationMeterial.objects.filter(
            app_for_day__in=application_today,
            status_checked=True)
        out['materials_list'] = _application_materials
        return render(request, "extend/material_today_app.html", out)

    _application_technic = ApplicationTechnic.objects.filter(app_for_day__in=application_today)
    _app = _application_technic

    if is_admin(request.user):
        app_tech_day = _app.filter(
            Q(app_for_day__status=STATUS_APP_submitted) |
            Q(app_for_day__status=STATUS_APP_approved) |
            Q(app_for_day__status=STATUS_APP_send)
        ).exclude(var_check=True)
    else:
        app_tech_day = _app.filter(app_for_day__status=STATUS_APP_send).exclude(var_check=True)

    driver_technic = app_tech_day.values_list(
        'technic_driver__driver__driver__last_name',
        'technic_driver__technic__name__name').order_by(
        'technic_driver__driver__driver__last_name').distinct()

    # ----------------------------------------------------------

    app_list = []
    for _drv, _tech in driver_technic:
        desc = app_tech_day.filter(
            technic_driver__driver__driver__last_name=_drv,
            technic_driver__technic__name__name=_tech).order_by('priority')
        _id_list = [_[0] for _ in desc.values_list('id')]

        if (_drv, _tech, desc, _id_list) not in app_list:
            app_list.append((_drv, _tech, desc, _id_list))

    out["today_technic_applications"] = app_list
    if is_admin(request.user):
        out["priority_list"] = get_priority_list(current_day)
        out['conflicts_vehicles_list_id'] = get_conflicts_vehicles_list(current_day)
        out['conflicts_list'] = get_conflicts_vehicles_list(current_day)

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
    out['applications_today_desc'] = current_application.description
    get_prepare_data(out, request, current_day=current_application.date)

    list_of_vehicles = ApplicationTechnic.objects.filter(app_for_day=current_application)
    out["list_of_vehicles"] = list_of_vehicles.order_by('technic_driver__technic__name')

    list_of_materials = ApplicationMeterial.objects.filter(
        app_for_day=current_application,
        status_checked=True).values_list('description', flat=True).first()
    out['list_of_materials'] = list_of_materials

    if is_admin(request.user):
        return render(request, 'extend/admin_show_inf_app.html', out)

    return render(request, "show_info_application.html", out)


def create_new_application(request, id_application):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    out = {}
    current_application = ApplicationToday.objects.get(id=id_application)
    current_date = current_application.date

    check_table(current_date)
    get_prepare_data(out, request, current_day=current_date)

    var_submit_mat_app = get_var(VAR['LIMIT_for_submission'])
    if var_submit_mat_app:
        _limit = var_submit_mat_app.time
        out['check_time'] = NOW_IN_TIME(_limit)
        out['LIMIT_for_submission'] = _limit
    else:
        out['check_time'] = NOW_IN_TIME()

    out["construction_site"] = current_application.construction_site
    out['applications_today_desc'] = current_application.description
    out["date_of_target"] = current_application.date

    conflicts_vehicles_list = get_conflicts_vehicles_list(current_date, c_in=1)
    out['conflicts_vehicles_list'] = conflicts_vehicles_list
    out['work_TD_list'] = get_work_TD_list(current_date, 0, F_saved=True)
    out['free_tech_name'] = get_free_tech_driver_list(current_day=current_date)

    Tech_driver_list = TechnicDriver.objects.filter(date=current_date, status=True, driver__status=True)
    Tech_name_list = TechnicName.objects.all().order_by('name')

    work_tech_name_list = Tech_driver_list.values_list('id', flat=True).distinct()
    out['work_tech_name_list'] = work_tech_name_list

    current_application_technic = ApplicationTechnic.objects.filter(app_for_day=current_application)
    out["list_of_vehicles"] = current_application_technic.order_by('technic_driver__technic__name')

    technic_name_id_list = Tech_driver_list.values_list('technic__name_id', flat=True).distinct()
    technic_names = Tech_name_list.filter(id__in=technic_name_id_list)
    out['technic_names'] = technic_names

    out['tech_driver_list'] = []
    for tn in technic_names:
        _td = Tech_driver_list.filter(technic__name=tn).values('id', 'driver__driver__last_name')
        out['tech_driver_list'].append((tn, _td))

    _materials = ApplicationMeterial.objects.filter(app_for_day=current_application)
    if _materials.exists():
        out['material_list_raw'] = _materials.values_list('description', flat=True).first()

    if request.method == "POST":
        IOL_id_application_technic = request.POST.getlist('io_id_app_tech')
        IOL_id_technic_name = request.POST.getlist('io_id_tech_name')
        IOL_id_technic_driver = request.POST.getlist('io_id_tech_driver')

        IO_desc_application_today = request.POST.get('app_today_desc')
        IO_desc_application_technic = request.POST.getlist('description_app_list')
        IO_desc_application_materiial = request.POST.get('desc_meterials')
        IO_app_var_check = request.POST.getlist('io_app_tech_var_chack')

        if IO_desc_application_today:
            IO_desc_application_today = str(IO_desc_application_today).strip()

        if IO_desc_application_materiial:
            IO_desc_application_materiial = str(IO_desc_application_materiial).strip()

        # ------------delete------------------------------------------------
        current_application_technic.exclude(id__in=IOL_id_application_technic).delete()
        # ------------------------------------------------------------------

        work_TD_list_F_saved = get_work_TD_list(current_date, 0, True)

        # --------- --choosing a free driver ---------------------------------------------------------
        for n, _id_td in enumerate(IOL_id_technic_driver):
            if _id_td == '':
                if work_TD_list_F_saved:
                    free_driver_of_tech_id = Tech_driver_list.exclude(id__in=work_TD_list_F_saved).filter(
                        technic__name=IOL_id_technic_name[n]).values_list('id', flat=True)
                else:
                    free_driver_of_tech_id = Tech_driver_list.filter(
                        technic__name=IOL_id_technic_name[n]).values_list('id', flat=True)

                if free_driver_of_tech_id.exists():
                    _choice = rand_choice(free_driver_of_tech_id)
                    IOL_id_technic_driver[n] = str(_choice)
                    work_TD_list_F_saved.append(_choice)
                else:
                    _tmp_td_list = Tech_driver_list.filter(
                        technic__name=IOL_id_technic_name[n]).values_list('id', flat=True)

                    _choice = rand_choice(_tmp_td_list)
                    IOL_id_technic_driver[n] = str(_choice)
            else:
                work_TD_list_F_saved.append(_id_td)
        # ---------------------------------------------------------------------------------------------

        # --------saving modified applications-------------------------------------------------------
        for i, _id_app_tech in enumerate(IOL_id_application_technic):
            _app_technic = ApplicationTechnic.objects.get(id=_id_app_tech)
            _app_technic.technic_driver = TechnicDriver.objects.get(id=IOL_id_technic_driver[i])
            _app_technic.var_check = IO_app_var_check[i]
            if IO_desc_application_technic[i]:
                _app_technic.description = str(IO_desc_application_technic[i]).strip()
            else:
                _app_technic.description = ''
            _app_technic.save()
        # --------------------------------------------------------------------------------------------

        # --------saving new applications-------------------------------------------------------
        if len(IOL_id_application_technic) < len(IOL_id_technic_driver):
            count_app_technic = len(IOL_id_application_technic)
            count_technic_driver = len(IOL_id_technic_driver)
            for i in range(count_app_technic, count_technic_driver):
                tech_drv = Tech_driver_list.get(id=IOL_id_technic_driver[i])

                ApplicationTechnic.objects.create(
                    app_for_day=current_application,
                    technic_driver=tech_drv,
                    description=IO_desc_application_technic[i]
                ).save()
        # --------------------------------------------------------------------------------------

        # -----materials app -------------------------------------------------------------------------
        _material, _ = ApplicationMeterial.objects.get_or_create(app_for_day=current_application)
        if IO_desc_application_materiial:
            if IO_desc_application_materiial != _material.description:
                _material.description = IO_desc_application_materiial
                _material.status_checked = False
                _material.save()
        else:
            _material.delete()
        # --------------------------------------------------------------------------------------------

        current_application.description = IO_desc_application_today
        current_application.save()

        # ---- set status app --------------------------------------------------------------------------
        if not ApplicationTechnic.objects.filter(app_for_day=current_application).exists() and \
                not ApplicationMeterial.objects.filter(app_for_day=current_application).exists() \
                and not IO_desc_application_today:
            _status = STATUS_APP_absent
        elif is_admin(request.user):
            _status = STATUS_APP_submitted
        else:
            _status = STATUS_APP_saved

        current_application.status = _status
        current_application.save()
        # --------------------------------------------------------------------------------------------

        if is_employee_supply(request.user):
            return HttpResponseRedirect(f'/supply_app/{current_date}')

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
            out['message'] = TEXT_TEMPLATES['message_invalid_password']

    return render(request, 'signin.html', out)


def del_staff(request, id_staff):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    user = User.objects.get(id=id_staff)
    post = Post.objects.get(user_post=user)
    tech_drv = TechnicDriver.objects.filter(
        driver__driver=user,
        date__lt=TODAY
    )
    tech_drv.delete()
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
    elif is_mechanic(request.user):
        post_list = PostName.objects.filter(name_post=POST_USER['driver'])
    else:
        post_list = PostName.objects.all()

    out['post_list'] = post_list

    if not request.user.is_anonymous:
        get_prepare_data(out, request)

    if request.method == 'POST':
        username = request.POST['username']

        if not User.objects.filter(username=username).exists():
            password = request.POST['password']
            first_name = request.POST['first_name']
            telephone = request.POST['telephone']
            last_name = request.POST['last_name']
            post_id = request.POST.get('post')
            foreman_id = request.POST.get('foreman')
            new_user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=False,
                is_superuser=False)

            if post_id:
                post_name = PostName.objects.get(id=post_id)
            else:
                post_name = None

            if foreman_id:
                foreman = User.objects.get(id=foreman_id)
            else:
                foreman = None

            _count_post = Post.objects.all().count()+1
            Post.objects.create(
                id=_count_post,
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
            out['message'] = TEXT_TEMPLATES['user_exists']

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
            status=STATUS_APP_approved,
            date=current_day)

        for app in current_applications:
            app.status = STATUS_APP_send
            app.save()

        send_task_for_drv(current_day)
        send_status_app_for_foreman(current_day)
        send_message_for_admin(current_day)

        _var, _ = Variable.objects.get_or_create(name=VAR['sent_app'], date=current_day)
        _var.time = NOW.isoformat(timespec='minutes')
        _var.flag = True
        _var.value = TODAY
        _var.save()

    return HttpResponseRedirect(f'/applications/{day}')


def approv_all_applications(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    if is_admin(request.user):
        current_day = convert_str_to_date(day)
        current_applications = ApplicationToday.objects.filter(
            status=STATUS_APP_submitted, date=current_day)

        for app in current_applications:
            app.status = STATUS_APP_approved
            app.save()

    return HttpResponseRedirect(f'/applications/{day}')


def submitted_all_applications(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    current_day = convert_str_to_date(day)
    _Application_today = ApplicationToday.objects.filter(date=current_day)

    if is_admin(request.user):
        pass

    elif is_foreman(request.user):
        app_for_day = _Application_today.filter(construction_site__foreman=request.user)

    elif is_master(request.user):
        _foreman = Post.objects.get(user_post=request.user).supervisor
        app_for_day = _Application_today.filter(construction_site__foreman=_foreman)

    elif is_employee_supply(request.user):
        app_for_day = _Application_today.filter(
            construction_site__foreman=None,
            construction_site__address=TEXT_TEMPLATES['constr_site_supply_name']
        )

    current_applications = app_for_day.filter(
        status=STATUS_APP_saved,
        date=current_day)

    for app in current_applications:
        app.status = STATUS_APP_submitted
        app.save()
    count_apps = current_applications.count()
    if count_apps > 0:
        try:
            _var = Variable.objects.get(name='status_sended_app', date=current_day)
            if _var.flag:
                mess = f'Подана {count_apps} заявки(а) требующих рассмотрение!'
                send_message_for_admin(current_day, mess)
        except Variable.DoesNotExist:
            pass

    return HttpResponseRedirect(f'/applications/{day}')


def get_priority_list(current_day, get_td_id=False):
    """
    return ApplicationTechnic_id
    """
    _Application_technic = ApplicationTechnic.objects.filter(
        app_for_day__date=current_day).exclude(app_for_day__status=STATUS_APP_saved)
    l = []
    app_tech = _Application_technic.values_list(
        'priority',
        'technic_driver_id',
        'id').order_by('technic_driver_id').exclude(var_check=True)

    ll = [(int(a[0]), a[1]) for a in app_tech]
    for _app in set(ll):
        count = ll.count(_app)
        if count > 1:
            if get_td_id:
                _l = [q[0] for q in _Application_technic.filter(
                    priority=_app[0],
                    technic_driver_id=_app[1]).exclude(var_check=True).distinct().values_list('technic_driver_id')]
                l.extend(_l)
            else:
                _l = [q[0] for q in _Application_technic.filter(
                    priority=_app[0],
                    technic_driver_id=_app[1]).exclude(var_check=True).distinct().values_list('id')]
                l.extend(_l)
    return l


def get_work_TD_list(current_day, c_in=1, F_saved=False):
    out = []

    if F_saved: #if ApplicationTechnic have status = 'saved'
        tech_app_status = ApplicationTechnic.objects.filter(
            Q(app_for_day__status=STATUS_APP_send) |
            Q(app_for_day__status=STATUS_APP_submitted) |
            Q(app_for_day__status=STATUS_APP_approved) |
            Q(app_for_day__status=STATUS_APP_saved)
        )
    else:
        tech_app_status = ApplicationTechnic.objects.filter(
            Q(app_for_day__status=STATUS_APP_send) |
            Q(app_for_day__status=STATUS_APP_submitted) |
            Q(app_for_day__status=STATUS_APP_approved)
        )

    app_list_day = tech_app_status.filter(app_for_day__date=current_day)
    tech_app_today = list(app_list_day.values_list('technic_driver', flat=True))
    for _i in set(tech_app_today):
        if tech_app_today.count(_i) > c_in:
            out.append(_i)
    return out


def get_free_tech_driver_list(current_day, technic_name=None):
    out = []

    _app_tech = ApplicationTechnic.objects.filter(
        app_for_day__date=current_day
    ).values_list('technic_driver_id', flat=True)

    _technic_driver_free = TechnicDriver.objects.filter(
        date=current_day,
        status=True,
        driver__status=True
    ).exclude(id__in=_app_tech)
    if not technic_name:
        out = list(_technic_driver_free.values_list('technic__name_id', flat=True))
    else:
        out = list(_technic_driver_free.filter(technic__name=technic_name).values_list('id', flat=True))

    return out


def get_conflicts_vehicles_list(current_day, all_app=False, lack=False, c_in=0):
    """
        c_in - количество тех. которое может быть заказано, прежде чем попасть в список
        all - сравнение с всей в том числе нероботающей техникой
        lack - получить количество недостоющей техники
    """
    count_technics = {}
    out = []

    if all_app:
        for _a in Technic.objects.all():
            count_technics[_a.name.id] = Technic.objects.filter(name=_a.name).count()
    else:
        for f in Technic.objects.all():
            count_technics[f.name.id] = TechnicDriver.objects.filter(
                status=True,
                driver__status=True,
                date=current_day,
                technic__name=f.name
            ).count()

    app_list_today = ApplicationTechnic.objects.filter(
        app_for_day__date=current_day).exclude(
        Q(technic_driver__status=False) |
        Q(var_check=True))

    app_list_submit_approv = app_list_today.filter(
        Q(app_for_day__status=STATUS_APP_send) |
        Q(app_for_day__status=STATUS_APP_submitted) |
        Q(app_for_day__status=STATUS_APP_approved)
        )

    list_of_work_tech = list(app_list_submit_approv.filter(priority=1).values_list(
        'technic_driver__technic__name_id', flat=True))

    for i in set(list_of_work_tech):
        if list_of_work_tech.count(i)+c_in > count_technics[i]:
            if lack:
                _c = list_of_work_tech.count(i) - count_technics[i]
                _name = TechnicName.objects.get(id=i).name
                out.append((_name, _c))
            else:
                out.append(i)
    return out


def get_count_app_for_driver(current_day):
    out = []
    _tech_drv = [_[0] for _ in TechnicDriver.objects.filter(
        date=current_day,
        status=True,
        driver__status=True).values_list('id')]
    _app = [_[0] for _ in ApplicationTechnic.objects.filter(
        Q(app_for_day__date=current_day),
        Q(app_for_day__status=STATUS_APP_approved) |
        Q(app_for_day__status=STATUS_APP_submitted) |
        Q(app_for_day__status=STATUS_APP_send)
    ).values_list('technic_driver_id')]

    for _td in set(_tech_drv):
        _count = _app.count(_td)
        out.append((_td, _count))
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
            return HttpResponseRedirect(f"supply_app/{get_current_day('next_day')}")
        else:
            id_supply_list = Post.objects.filter(
                post_name__name_post=POST_USER['employee_supply']).values_list('user_post_id', flat=True)
            supply_driver_id_list = Post.objects.filter(supervisor_id__in=id_supply_list).values_list('user_post_id',
                                                                                                      flat=True)
            if request.user.id in supply_driver_id_list:
                return HttpResponseRedirect(f"/today_app/{get_current_day('last_day')}/materials")
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
    out['tense'] = current_day >= TODAY
    out['referer'] = request.headers.get('Referer')
    out['weekend_flag'] = TODAY.weekday() == 4 and get_current_day('next_day').weekday() == 5 and current_day.weekday() == 0


    return out


def success_application(request, id_application):
    """изменение статуса заявки"""
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    current_application = ApplicationToday.objects.get(id=id_application)
    current_day = convert_str_to_date(current_application.date)

    send_flag = Variable.objects.filter(name=VAR['sent_app'], date=current_day, flag=True).exists()
    _day = f"{WEEKDAY[current_day.weekday()]}, {current_day.day} {MONTH[current_day.month.numerator]}"


    if is_admin(request.user):
        _status = current_application.status

        if _status == STATUS_APP_submitted:
            current_application.status = STATUS_APP_approved
        elif _status == STATUS_APP_approved:
            current_application.status = STATUS_APP_send

            send_task_for_drv(current_day, id_app_today=id_application)
            send_status_app_for_foreman(current_day, id_app_today=id_application)
            send_message_for_admin(current_day, id_app_today=id_application)

    else:
        current_application.status = STATUS_APP_submitted
        if send_flag:
            mess = f'Подана заявка требующая рассмотрение!'
            send_message_for_admin(current_day, mess)


    current_application.save()

    return HttpResponseRedirect(f'/applications/{current_day}')


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


def prepare_work_day_table(day):
    current_week = list(get_week(day))
    if WorkDayTabel.objects.filter(date__in=current_week).count() < 7:
        for n, _day in enumerate(current_week, 1):
            if n in (6, 7):
                WorkDayTabel.objects.get_or_create(date=_day, status=False)
            else:
                WorkDayTabel.objects.get_or_create(date=_day)


def prepare_driver_table(day):
    current_day = convert_str_to_date(day)
    driver_list = Post.objects.filter(post_name__name_post=POST_USER['driver'])
    _ex_td = driver_list.exclude(
        user_post__id__in=DriverTabel.objects.filter(date=TODAY).values_list('driver__id', flat=True))

    if current_day > TODAY:
        try:
            if _ex_td.exists():
                for dr in _ex_td:
                    DriverTabel.objects.create(driver=dr.user_post, date=current_day)
            _driver_table = DriverTabel.objects.filter(date=TODAY)
            for _dt in _driver_table:
                _dt.pk = None
                _dt.date = current_day
            DriverTabel.objects.bulk_create(_driver_table)
        except DriverTabel.DoesNotExist:
            for drv in driver_list:
                DriverTabel.objects.create(driver=drv, date=current_day)

    elif current_day == TODAY:
        if not _ex_td.exists():
            for drv in driver_list:
                DriverTabel.objects.create(driver=drv.user_post, date=current_day)
        else:
            for dr in _ex_td:
                DriverTabel.objects.create(driver=dr.user_post, date=current_day)
    else:
        pass


def prepare_technic_driver_table(day):
    current_day = convert_str_to_date(day)
    work_driver_list = DriverTabel.objects.filter(date=current_day, status=True)
    tech_drv_list_today = TechnicDriver.objects.filter(date=TODAY)

    if current_day > TODAY:
        for _tech in Technic.objects.all():
            _drv = tech_drv_list_today.filter(technic=_tech).values_list('driver__driver__last_name', 'status')
            driver = _drv[0][0]
            status = _drv[0][1]

            c_drv = work_driver_list.filter(driver__last_name=driver)

            if c_drv.exists():
                TechnicDriver.objects.create(
                    technic=_tech,
                    driver=DriverTabel.objects.get(date=current_day, driver__last_name=driver),
                    date=current_day,
                    status=status)
            else:
                TechnicDriver.objects.create(
                    technic=_tech,
                    driver=None,
                    date=current_day,
                    status=status)
    else:
        for tech in Technic.objects.all():
            TechnicDriver.objects.create(technic=tech, date=TODAY, status=True)


def prepare_application_today(day):
    current_day = convert_str_to_date(day)
    construction_site_list = ConstructionSite.objects.filter(status=STATUS_CS_opened)

    applications_today_list_all = ApplicationToday.objects.filter(date=current_day)

    if applications_today_list_all.count() < construction_site_list.count():
        for constr_site in construction_site_list:
            _app, _ = ApplicationToday.objects.get_or_create(construction_site=constr_site, date=current_day)
            if _:
                _app.status = STATUS_APP_absent
                _app.save()
        print('AP created')
    else:
        if construction_site_list.count() < applications_today_list_all.count():
            applications_today_list_all.exclude(construction_site__in=construction_site_list).delete()
        else:
            print("AP OK")


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


def set_var(name, value=None, time=None, date=None, flag=False, user=None):
    _var, _ = Variable.objects.get_or_create(name=name, user=user)
    _var.value = value
    _var.flag = flag
    _var.time = time
    _var.date = date
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
    if TeleBot.objects.filter(user_bot=id_user).exists():
        chat_id = TeleBot.objects.get(user_bot=id_user)

        if chat_id and chat_id.id_chat:
            BOT.send_message(chat_id.id_chat, message)


def send_task_for_drv(current_day, messages=None, id_app_today=None):
    out = []
    _driver_list = DriverTabel.objects.filter(date=current_day, status=True)
    send_flag = Variable.objects.filter(name=VAR['sent_app'], date=current_day, flag=True).exists()
    _day = f"{WEEKDAY[current_day.weekday()]}, {current_day.day} {MONTH[current_day.month.real-1]}"

    if id_app_today:
        _App = ApplicationTechnic.objects.filter(app_for_day_id=id_app_today)
        for _a in _App:
            if send_flag:
                mss = f"{_a.technic_driver.driver.driver.last_name} {_a.technic_driver.driver.driver.first_name}\nОбновленная заявка на:\n {_day}\n\n"
            else:
                mss = f"{_a.technic_driver.driver.driver.last_name} {_a.technic_driver.driver.driver.first_name}\nЗаявка на {_day}\n\n"
            if _a.app_for_day.construction_site.address == TEXT_TEMPLATES['constr_site_supply_name']:
                mss += f"\t{_a.priority})\n"
            else:
                mss += f"\t{_a.priority}) {_a.app_for_day.construction_site.address} ({_a.app_for_day.construction_site.foreman}):\n"

            mss += f"{_a.description}\n\n"
            send_message(_a.technic_driver.driver.driver.id, mss)
        return

    for _id_drv in _driver_list:
        _app = ApplicationTechnic.objects.filter(
            app_for_day__date=current_day,
            app_for_day__status=STATUS_APP_send,
            technic_driver__driver__driver=_id_drv.driver.id).order_by('priority').exclude(var_check=True)
        out.append((_id_drv, _app))

    for drv, app in out:
        if send_flag:
            mss = f"{drv.driver.last_name} {drv.driver.first_name}\nОбновленная заявка на:\n {_day}\n\n"
        else:
            mss = f"{drv.driver.last_name} {drv.driver.first_name}\nЗаявка на {_day}\n\n"
        for s in app:
            if s.app_for_day.construction_site.address == TEXT_TEMPLATES['constr_site_supply_name']:
                mss += f"\t{s.priority})\n"
            else:
                mss += f"\t{s.priority}) {s.app_for_day.construction_site.address} ({s.app_for_day.construction_site.foreman})\n"

            mss += f"{s.description}\n\n"
        if messages:
            mss = messages
        print(mss)
        send_message(drv.driver.id, mss)


def send_status_app_for_foreman(current_day, messages=None, id_app_today=None):
    out = []

    id_foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman'])
    id_master_list = Post.objects.filter(post_name__name_post=POST_USER['master'])
    id_supply_list = Post.objects.filter(post_name__name_post=POST_USER['employee_supply'])

    if id_app_today:
        _app = ApplicationToday.objects.filter(id=id_app_today)
    else:
        _app = ApplicationToday.objects.filter(date=current_day, status=STATUS_APP_send)

    send_flag = Variable.objects.filter(name=VAR['sent_app'], date=current_day, flag=True).exists()
    _day = f"{WEEKDAY[current_day.weekday()]}, {current_day.day} {MONTH[current_day.month.real-1]}"

    for _id in id_foreman_list:
        _a = _app.filter(construction_site__foreman=_id.user_post)
        if _a:
            out.append((_id.user_post.id, _a))

    for _id in id_master_list:
        _a = _app.filter(construction_site__foreman=_id.supervisor)
        if _a:
            out.append((_id.user_post.id, _a))

    for _id, app in out:
        if send_flag:
            mss = f"Повторное уведомление:\n{_day}\n\n"
        else:
            mss = f"{_day}\n\n"
        for a in app:
            mss += f"Заявка на [ {a.construction_site.address} ] одобрена\n"
        if messages:
            mss = messages
        send_message(_id, mss)


def send_message_for_admin(current_day, messages=False, id_app_today=None):
    admin_id_list = Post.objects.filter(
        post_name__name_post=POST_USER['admin']).values_list('user_post_id', flat=True)
    send_flag = Variable.objects.filter(name=VAR['sent_app'], date=current_day, flag=True).exists()
    _day = f"{WEEKDAY[current_day.weekday()]}, {current_day.day} {MONTH[current_day.month.real-1]}"
    if id_app_today:
        _app = ApplicationToday.objects.get(id=id_app_today)
        if send_flag:
            messages = f"Заявка на:\n{_day}\nобъект: {_app.construction_site.address} ({_app.construction_site.foreman.last_name}) отправлена повторно"
        else:
            messages = f"Заявка на:\n{_day}\nобъект: {_app.construction_site.address} ({_app.construction_site.foreman.last_name}) отправлена"

    if messages:
        mess = messages
    else:
        if send_flag:
            mess = f"Заявки на:\n{_day} отправлены повторно"
        else:
            mess = f"Заявки на:\n{_day} отправлены"

    for _id in admin_id_list:
        send_message(_id, mess)


def setting_view(request):
    out = {}
    get_prepare_data(out, request)
    current_user = request.user
    if is_admin(request.user):
        setting_list = Variable.objects.filter(Q(user=current_user) | Q(user=None))
    else:
        setting_list = Variable.objects.filter(user=current_user)
    out['setting_list'] = setting_list

    if request.method == 'POST':
        setting_id_list = request.POST.getlist('setting_id')

        if setting_id_list:
            for n, _id in enumerate(setting_id_list, 1):
                var = Variable.objects.get(id=_id)
                value = request.POST.get(f"setting_value_{n}")
                _time = request.POST.get(f"setting_time_{n}")
                if not _time:
                    _time = None
                _date = request.POST.get(f"setting_date_{n}")
                if not _date:
                    _date = None

                if request.POST.get(f"setting_flag_{n}"):
                    flag = True
                else:
                    flag = False

                if value == 'None':
                    var.value = None
                else:
                    var.value = value
                var.time = _time
                var.date = _date
                var.flag = flag
                var.save()

    return render(request, 'setting_page.html', out)


def check_table(day):
    date = convert_str_to_date(day)

    if not WorkDayTabel.objects.filter(date=date).exists():
        prepare_work_day_table(day)

    _today = WorkDayTabel.objects.get(date=date)
    if _today.status and _today.date >= TODAY:
        if not DriverTabel.objects.filter(date=date).exists():
            prepare_driver_table(day)

        if not TechnicDriver.objects.filter(date=date).exists():
            prepare_technic_driver_table(day)

        prepare_application_today(day)
        print('workday')
    elif _today.date < TODAY:
        app = ApplicationToday.objects.filter(date__lt=date, status=STATUS_APP_absent)
        if app.exists():
            app.delete()
        _var = Variable.objects.filter(name=VAR['sent_app'], date__lt=date)
        if _var.exists():
            _var.delete()

    else:
        print('weekend')
        return False
    return True


def send_debug_messages(messages='Test'):
    admin_id_list = User.objects.filter(is_superuser=True)
    mess = f"{TODAY}\n{messages}"

    for _id in admin_id_list:
        send_message(_id, mess)


def find_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    application_today = ApplicationToday.objects.filter(date=current_day)
    application_technic = ApplicationTechnic.objects.filter(app_for_day__in=application_today)
    technic_driver = TechnicDriver.objects.filter(date=current_day)
    driver = DriverTabel.objects.filter(date=current_day)
    construction_site = ConstructionSite.objects.filter(status=STATUS_CS_opened)

    if request.method == 'POST':
        str_find = request.POST.get('find_input')
        # str_find = str(str_find).strip()
        out['str_find'] = str_find
        post = Post.objects.filter(
            Q(user_post__last_name__icontains=str_find) |
            Q(user_post__last_name__icontains=str(str_find).capitalize())
        )
        post_list = [u.supervisor.id if u.supervisor else u.user_post.id for u in post]
        out['post_list'] = post.exclude(
            Q(post_name__name_post=POST_USER['driver']) |
            Q(post_name__name_post=POST_USER['admin'])
        )

        out['application_today'] = application_today.filter(
            construction_site__foreman__in=post_list).order_by('construction_site__address')

        technic = technic_driver.filter(
            Q(technic__tech_type__name__icontains=str_find) |
            Q(technic__tech_type__name__icontains=str(str_find).capitalize()) |
            Q(technic__tech_type__short_name__icontains=str_find) |
            Q(technic__tech_type__short_name__icontains=str(str_find).capitalize()) |
            Q(driver__driver__last_name__icontains=str_find) |
            Q(driver__driver__last_name__icontains=str(str_find).capitalize()) |
            Q(technic__name__name__icontains=str_find) |
            Q(technic__name__name__icontains=str(str_find).capitalize())
        )
        out['technic_driver'] = technic

        out['drivers'] = driver.filter(
            Q(driver__last_name__icontains=str_find) |
            Q(driver__last_name__icontains=str(str_find).capitalize())
            )


        app_tech = application_technic.filter(
            Q(technic_driver__technic__name__name__icontains=str_find) |
            Q(technic_driver__driver__driver__last_name__icontains=str_find) |
            Q(app_for_day__construction_site__foreman__in=post_list)
        ).order_by('app_for_day__construction_site__address')

        out['application_technic'] = []
        for a_t in app_tech.values_list(
                'app_for_day__construction_site__address',
                'app_for_day__construction_site__foreman__last_name').distinct():
            _app = app_tech.filter(app_for_day__construction_site__address=a_t[0])
            out['application_technic'].append((a_t, _app))

        tech_name_list = list(technic.values_list('technic__name__name', flat=True).distinct())
        out['tech_inf'] = []

        for tn in tech_name_list:
            all_t = technic_driver.filter(technic__name__name=tn)
            work_t = all_t.filter(status=True)
            all_c = all_t.count()
            work_c = work_t.count()
            out['tech_inf'].append((tn, all_c, work_c, all_c - work_c))

    return render(request, 'find.html', out)


def change_workday(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    current_day = convert_str_to_date(day)
    try:
        work_day = WorkDayTabel.objects.get(date=current_day)
        work_day.status = True
        work_day.save()
    except WorkDayTabel.DoesNotExist:
        print('this day DoesNotExist')
    return HttpResponseRedirect(f'/applications/{day}')
