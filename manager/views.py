import datetime

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

# ==================================
from archive.models import TTechnicDriver as aTTechnicDriver
from archive.models import TDriver as aTDriver
from archive.models import TWorkDay as aTWorkDay
from archive.models import ApplicationMeterial as aTApplicationMeterial
from archive.models import ApplicationTechnic as aApplicationTechnic
from archive.models import ApplicationToDay as aApplicationToDay

from archive.models import Technic as aTechnic
from archive.models import ConstructionSite as aConstructionSite
from archive.models import User as aUser

from archive.structures import get_application_today
from archive.structures import ATTechnicDriver
from archive.structures import ATDriver
from archive.structures import AConstructionSite
# ==================================

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
from manager.utilities import archive_db as ARCHIVE_DB
from manager.utilities import ApiTelegramException
# -----------------
from manager.utilities import get_day_in_days
# from manager.utilities import get_difference
from manager.utilities import get_week
from manager.utilities import timedelta
from manager.utilities import choice as rand_choice
from manager.utilities import convert_str_to_date
from manager.utilities import check_last_activity

from manager.utilities import check_time as NOW_IN_TIME
from manager.utilities import NOW
from manager.utilities import NOW_DATETIME
from manager.utilities import get_json
from manager.utilities import get_id_chat
from manager.utilities import BOT

# ----------------
from manager.utilities import is_backup_time

from manager.utilities import create_backup_db
from manager.utilities import get_list_db_backup
from manager.utilities import clear_db_backup
from manager.utilities import restore_db_backup
from manager.utilities import delete_db_backup
from manager.utilities import back24H
from manager.utilities import get_read_only_mode
# ----------------
from TechManager.settings import AUTO_CREATE_BACKUP_DB

# ----------------

AUTO_CLEAR_DB = True
# AUTO_CREATE_BACKUP_DB = False

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


def clear_db(request):
    if not is_admin(request.user):
        return HttpResponseRedirect('/')
    clear_db_backup()
    return HttpResponseRedirect(request.headers.get('Referer'))


def create_db_backup(request):
    create_backup_db()
    return HttpResponseRedirect(request.headers.get('Referer'))


def undo_change_db(request):
    list_backup = get_list_db_backup()
    backups = sorted(list_backup)  # reversed(list_backup)
    if backups:
        last_backup = backups.pop()
        curr_backup = str(last_backup).replace(' ', '_').replace(':', '-') + '.sqlite3'
        restore_db_backup(curr_backup, undo=True)

    return HttpResponseRedirect(request.headers.get('Referer'))


def restore_db(request, date_img):
    curr_backup = date_img.replace('T', '_').replace(':', '-') + '.sqlite3'
    restore_db_backup(curr_backup)
    return HttpResponseRedirect('/list_backup/')


def restore24_db(request, date_img):
    curr_backup = date_img[:-3].replace('T', '_').replace(':', '-') + '.sqlite3'
    back24H(param='restore', backup=curr_backup)
    return HttpResponseRedirect('/list_backup/')


def show_backup_list_view(request):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    get_prepare_data(out, request)

    list_backup = get_list_db_backup()
    out['list_backup'] = sorted(list_backup, reverse=True)  # reversed(list_backup)
    out['list_backup24'] = sorted(back24H(param='list'), reverse=True)[0:6]

    # --------------------------------------------------------------
    try:
        app_materials_count = aTApplicationMeterial.objects.using(ARCHIVE_DB).count()
        app_to_day_count = aApplicationToDay.objects.using(ARCHIVE_DB).count()
        app_technic_count = aApplicationTechnic.objects.using(ARCHIVE_DB).count()
        staff_count = aUser.objects.using(ARCHIVE_DB).count()
        construction_site_count = aConstructionSite.objects.using(ARCHIVE_DB).count()
        t_drivers_count = aTDriver.objects.using(ARCHIVE_DB).count()
        t_work_day_count = aTWorkDay.objects.using(ARCHIVE_DB).count()
        t_technic_count = aTTechnicDriver.objects.using(ARCHIVE_DB).count()
        technic_count = aTechnic.objects.using(ARCHIVE_DB).count()

        out['app_materials_count'] = (
            aTApplicationMeterial._meta.verbose_name_plural.title().capitalize(), app_materials_count)
        out['app_to_day_count'] = (
            aApplicationToDay._meta.verbose_name_plural.title().capitalize(), app_to_day_count)
        out['app_technic_count'] = (
            aApplicationTechnic._meta.verbose_name_plural.title().capitalize(), app_technic_count)
        out['staff_count'] = (
            aUser._meta.verbose_name_plural.title().capitalize(), staff_count)
        out['construction_site_count'] = (
            aConstructionSite._meta.verbose_name_plural.title().capitalize(), construction_site_count)
        out['t_drivers_count'] = (
            aTDriver._meta.verbose_name_plural.title().capitalize(), t_drivers_count)
        out['t_work_day_count'] = (
            aTWorkDay._meta.verbose_name_plural.title().capitalize(), t_work_day_count)
        out['t_technic_count'] = (
            aTTechnicDriver._meta.verbose_name_plural.title().capitalize(), t_technic_count)
        out['technic_count'] = (
            aTechnic._meta.verbose_name_plural.title().capitalize(), technic_count)
    except Exception as e:
        send_debug_messages('Error DB archive')


    # --------------------------------------------------------------

    return render(request, 'db_supply.html', out)


def test_bot(request, id_user):
    tel_bot = TeleBot.objects.get(user_bot=id_user)
    id_chat = tel_bot.id_chat
    BOT.send_message(id_chat, 'test message')

    return HttpResponseRedirect(f'/connect_bot_view/{id_user}')


def send_message(id_user, message):
    if TeleBot.objects.filter(user_bot=id_user).exists():
        chat_id = TeleBot.objects.get(user_bot=id_user)

        if chat_id and chat_id.id_chat:
            try:
                BOT.send_message(chat_id.id_chat, message)
            except ApiTelegramException as e:
                pass


def send_debug_messages(messages='Test'):
    admin_id_list = User.objects.filter(is_superuser=True)
    mess = f"{TODAY}\n{messages}"
    for _id in admin_id_list:
        send_message(_id, mess)


def testA(request):
    out = []

    id_foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman'])
    id_master_list = Post.objects.filter(post_name__name_post=POST_USER['master'])
    id_supply_list = Post.objects.filter(post_name__name_post=POST_USER['employee_supply'])

    msg = '''
        ВНИМАНИЕ!
     Время подачи заявок на технику ограниченно до 16.00
    '''
    for _id in id_foreman_list:
        out.append(_id.user_post.id)
    for _id in id_master_list:
        out.append(_id.user_post.id)
    for _id in out:
        send_message(_id, msg)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def make_full_archive(request):
    make_backup_app_materials()
    make_backup_app_to_day()
    make_backup_app_technics()
    make_backup_staff()
    make_backup_construction_site()
    make_backup_driver_table()
    make_backup_work_day_table()
    make_backup_technic_table()
    make_backup_technics()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def make_backup_technics(id_technic=None, action='add'):
    if id_technic is None:
        technics = Technic.objects.all()
    else:
        technics = Technic.objects.filter(pk=id_technic)
    _status = True if action == 'del' else False
    for _technic in technics:
        aTechnic.objects.using(ARCHIVE_DB).update_or_create(
            id_T=_technic.id, defaults={
                'name': _technic.name.name,
                'id_information': _technic.id_information,
                'tech_type': _technic.tech_type.name,
                'description': _technic.description,
                'attached_driver_i': _technic.attached_driver.pk if _technic.attached_driver is not None else None,
                'supervisor_i': _technic.supervisor.pk,
                'bd_status': _status
            }
        )


def make_backup_construction_site(id_constr_site=None, action='add'):
    if id_constr_site is None:
        constr_sites = ConstructionSite.objects.all()
    else:
        constr_sites = ConstructionSite.objects.filter(pk=id_constr_site)
    _status = True if action == 'del' else False
    for constr_site in constr_sites:
        aConstructionSite.objects.using(ARCHIVE_DB).update_or_create(
            id_C_S=constr_site.pk, defaults={
                'address': constr_site.address,
                'foreman_i': constr_site.foreman.pk if constr_site.foreman is not None else None,
                'bd_status': _status
            }
        )


def make_backup_staff(id_staff=None, action='add'):
    if id_staff is None:
        staff = Post.objects.all()
    else:
        staff = Post.objects.filter(user_post_id=id_staff)
    _status = True if action == 'del' else False
    for employee in staff:
        aUser.objects.using(ARCHIVE_DB).update_or_create(
            id_U=employee.user_post.pk, defaults={
                'username': employee.user_post.username,
                'first_name': employee.user_post.first_name,
                'last_name': employee.user_post.last_name,
                'post': employee.post_name.name_post if employee.post_name is not None else None,
                'date_joined': employee.user_post.date_joined,
                'telephone': employee.telephone,
                'bd_status': _status
            }
        )


def make_backup_technic_table(technic_driver_list: list = None):
    if technic_driver_list is None:
        technic_driver_list = TechnicDriver.objects.filter(date__lte=TODAY-timedelta(days=1))
    for _td in technic_driver_list:
        if _td.technic is not None:
            aTTechnicDriver.objects.using(ARCHIVE_DB).get_or_create(
                id_T_D=_td.pk,
                technic_i=_td.technic.pk,
                driver_i=_td.driver.pk if _td.driver is not None else None,
                date=_td.date,
                status=_td.status
            )


def make_backup_driver_table(driver_list: list = None):
    if driver_list is None:
        driver_list = DriverTabel.objects.filter(date__lte=TODAY-timedelta(days=1))
    for _td in driver_list:
        if _td.driver is not None:
            aTDriver.objects.using(ARCHIVE_DB).get_or_create(
                id_D=_td.pk,
                driver_i=_td.driver.pk,
                status=_td.status,
                date=_td.date
            )


def make_backup_work_day_table(work_day_list: list = None):
    if work_day_list is None:
        work_day_list = WorkDayTabel.objects.filter(date__lte=TODAY)
        # work_day_list = WorkDayTabel.objects.filter(date__lte=TODAY - timedelta(days=1))

    for _wd in work_day_list:
        aTWorkDay.objects.using(ARCHIVE_DB).update_or_create(
            id_W_D=_wd.pk, defaults={
                'date': _wd.date,
                'status': _wd.status
            }
        )


def make_backup_app_materials(app_materials_list: list = None):
    if app_materials_list is None:
        app_materials_list = ApplicationMeterial.objects.filter(app_for_day__date__lte=TODAY-timedelta(days=1))
    for _am in app_materials_list:
        if _am.app_for_day is not None:
            aTApplicationMeterial.objects.using(ARCHIVE_DB).get_or_create(
                id_A_M=_am.pk,
                date=_am.app_for_day.date,
                app_for_day_i=_am.app_for_day.pk,
                description=_am.description
            )


def make_backup_app_technics(app_technics_list: list = None):
    if app_technics_list is None:
        app_technics_list = ApplicationTechnic.objects.filter(app_for_day__date__lte=TODAY-timedelta(days=1))
    for _at in app_technics_list:
        if _at.technic_driver is not None:
            aApplicationTechnic.objects.using(ARCHIVE_DB).get_or_create(
                id_A_T=_at.pk,
                date=_at.app_for_day.date,
                app_for_day_i=_at.app_for_day.pk,
                technic_driver_i=_at.technic_driver.pk,
                description=_at.description,
                priority=_at.priority
            )


def make_backup_app_to_day(app_to_day_list: list = None):
    if app_to_day_list is None:
        app_to_day_list = ApplicationToday.objects.filter(date__lte=TODAY-timedelta(days=1))
    for _at in app_to_day_list:
        if _at.construction_site is not None:
            aApplicationToDay.objects.using(ARCHIVE_DB).get_or_create(
                id_A_T_D=_at.pk,
                date=_at.date,
                construction_site_i=_at.construction_site.pk,
                description=_at.description
            )


def clean_db(_flag_delete=False, send_mess=True, _flag_backup=False):
    var_date_clean = Variable.objects.get_or_create(name=VAR['last_clean_db'])[0]
    if var_date_clean.date is None:
        return "date_of_last_clean_db is not exists"
    if TODAY > var_date_clean.date:
        # var_comm_date = get_var(var=VAR['LIMIT_for_apps'])
        var_comm_date = Variable.objects.get_or_create(name=VAR['LIMIT_for_apps'])[0]
        if var_comm_date.value is None:
            comm_date = TODAY - timedelta(days=1)
        else:
            comm_date = TODAY - timedelta(days=int(var_comm_date.value))
        mess = {}
        application_today = ApplicationToday.objects.filter(date__lte=comm_date)
        application_technic = ApplicationTechnic.objects.filter(app_for_day__in=application_today)
        application_material = ApplicationMeterial.objects.filter(app_for_day__in=application_today)
        technic_driver = TechnicDriver.objects.filter(date__lte=comm_date)
        table_drivers = DriverTabel.objects.filter(date__lte=comm_date)
        work_day_table = WorkDayTabel.objects.filter(date__lte=comm_date)

        app = ApplicationToday.objects.filter(date__lte=comm_date).exclude(status=STATUS_APP_send)
        if app.exists():
            mess['app'] = app.count()
            if _flag_delete:
                app.delete()

        # make archive ------------------------------------------------------
        if _flag_backup:
            make_backup_technic_table(technic_driver_list=technic_driver)
            make_backup_driver_table(driver_list=table_drivers)
            make_backup_work_day_table(work_day_list=work_day_table)
            make_backup_app_materials(app_materials_list=application_material)
            make_backup_app_technics(app_technics_list=application_technic)
            make_backup_app_to_day(app_to_day_list=application_today)

        # sent messages ------------------------------------------------------

        if technic_driver.exists():
            mess['technic_driver'] = technic_driver.count()
        if table_drivers.exists():
            mess['table_drivers'] = table_drivers.count()
        if work_day_table.exists():
            mess['work_day_table'] = work_day_table.count()
        if application_material.exists():
            mess['application_material'] = application_material.count()
        if application_technic.exists():
            mess['application_technic'] = application_technic.count()
        if application_today.exists():
            mess['application_today'] = application_today.count()

        # delete db ---------------------------------------------------------
        if _flag_delete:
            technic_driver.delete()
            table_drivers.delete()
            work_day_table.filter(date__lt=comm_date-timedelta(days=30)).delete()
            application_material.delete()
            application_technic.delete()
            application_today.delete()

        # technic_driver----------------------------------------------------

        _var = Variable.objects.filter(name=VAR['sent_app'], date__lt=TODAY)
        if _var.exists():
            mess['sent_var'] = _var.count()
            if _flag_delete:
                _var.delete()

        var_date_clean.date = TODAY
        var_date_clean.time = NOW.isoformat('minutes')
        var_date_clean.value = application_today.count()
        var_date_clean.flag = True
        var_date_clean.save()

        if send_mess:
            send_debug_messages(mess)

        return f"status:CLR, time:{NOW.isoformat('minutes')}, date:{TODAY}"
    else:
        return f"status:CONT, t:{var_date_clean.time.isoformat('minutes')}, " \
               f"d:{var_date_clean.date}, " \
               f"t_check:{NOW.isoformat('minutes')}, a_back:{AUTO_CREATE_BACKUP_DB}, " \
               f"c_back:{len(get_list_db_backup())} "

    return f"status:BRK, time:{NOW}, date:{TODAY}"

# LOG_DB = clean_db(_flag_delete=AUTO_CLEAR_DB, _flag_backup=True)

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
    get_prepare_data(out, request, current_day)
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

    if current_day < TODAY:
        return HttpResponseRedirect(f'/archive_supply_materials/{day}')

    get_prepare_data(out, request, current_day)

    current_application = ApplicationToday.objects.filter(
        Q(date=current_day),
        Q(status=STATUS_APP_submitted) |
        Q(status=STATUS_APP_approved) |
        Q(status=STATUS_APP_send)
    )

    app_material = ApplicationMeterial.objects.filter(app_for_day__in=current_application)

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
                    _app.status_checked = False if _app.status_checked else True
                    # _app.status_checked = True
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

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def move_supply_app(request, day, id_app):
    current_day = convert_str_to_date(day)
    app_for_day = ApplicationToday.objects.get(
        construction_site__foreman=None,
        date=current_day,
        construction_site__address=TEXT_TEMPLATES['constr_site_supply_name'])

    supply_list = Post.objects.filter(
        post_name__name_post=POST_USER['employee_supply']).values_list('user_post', flat=True)
    cur_app_tech = ApplicationTechnic.objects.get(id=id_app)

    if cur_app_tech.app_for_day.construction_site.foreman:
        _TEMPLATE_for_app = f'{cur_app_tech.app_for_day.construction_site.address} ({cur_app_tech.app_for_day.construction_site.foreman.last_name})\r\n{cur_app_tech.description}'
    else:
        _TEMPLATE_for_app = f'{cur_app_tech.app_for_day.construction_site.address}\r\n{cur_app_tech.description}'

    if not cur_app_tech.var_check:
        _id = cur_app_tech.id
        cur_app_tech.var_check = True
        cur_app_tech.save()
        cur_app_tech.pk = None
        cur_app_tech.var_check = False
        cur_app_tech.description = _TEMPLATE_for_app
        cur_app_tech.app_for_day = app_for_day
        cur_app_tech.var_ID_orig = _id
        cur_app_tech.save()
        app_for_day.status = STATUS_APP_saved
        app_for_day.save()
    elif cur_app_tech.var_check:
        ApplicationTechnic.objects.filter(Q(app_for_day=app_for_day) and Q(var_ID_orig=cur_app_tech.id)).delete()

        cur_app_tech.var_check = False
        cur_app_tech.save()
        if not ApplicationTechnic.objects.filter(app_for_day=app_for_day).exists():
            app_for_day.status = STATUS_APP_absent
            app_for_day.save()


    else:
        if TEXT_TEMPLATES['dismiss'] in cur_app_tech.description:
            cur_app_tech.description = cur_app_tech.description.replace(TEXT_TEMPLATES['dismiss'], '')
        cur_app_tech.var_check = False
        cur_app_tech.save()

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def supply_app_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')


    check_table(day)
    out = {}
    current_day = convert_str_to_date(day)

    if current_day < TODAY:
        return HttpResponseRedirect(f'/archive_supply_app/{day}')

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


    count_app_mat_not_checked = ApplicationMeterial.objects.filter(
        Q(status_checked=False) &
        Q(app_for_day__date=current_day)
    )
    if count_app_mat_not_checked.exists():
        out['count_am_not_check'] = count_app_mat_not_checked.count()


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
        make_backup_technics(id_technic=id_tech, action='del')
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
        make_backup_technics(id_technic=_technic.pk, action='edit')
        send_debug_messages(
            messages=f'Added new tech:\n{t_name}\n{t_type}\n{t_attr_drv}\n{t_iden_inf}\n{t_desc}\n{t_direct} ')

        return HttpResponseRedirect('/technic_list/')

    return render(request, 'edit_technic.html', out)


def copy_app_view(request, id_application, day):
    out = {}
    _app_for_day = ApplicationToday.objects.get(id=id_application)
    current_day = _app_for_day.date
    get_prepare_data(out, request, current_day)
    _app_technic = ApplicationTechnic.objects.filter(app_for_day=_app_for_day)
    _app_materials = ApplicationMeterial.objects.filter(app_for_day=_app_for_day)
    if is_admin(request.user):
        _status = STATUS_APP_submitted
    else:
        _status = STATUS_APP_saved

    date_of_target = convert_str_to_date(day)
    if date_of_target > TODAY:
        new_app_today, _ = ApplicationToday.objects.get_or_create(
            date=date_of_target,
            construction_site=_app_for_day.construction_site)
        new_app_today.status = STATUS_APP_saved
        new_app_today.description = _app_for_day.description
        new_app_today.save()

        for app_tech in _app_technic:
            if app_tech.technic_driver.driver:
                if TechnicDriver.objects.filter(date=date_of_target,
                                                status=True,
                                                driver__date=date_of_target,
                                                driver__driver=app_tech.technic_driver.driver.driver).exists():
                    td = TechnicDriver.objects.get(date=date_of_target,
                                                   status=True,
                                                   driver__date=date_of_target,
                                                   driver__driver=app_tech.technic_driver.driver.driver)
                    new_app_tech, _ = ApplicationTechnic.objects.get_or_create(
                        technic_driver=td,
                        app_for_day=new_app_today,
                        description=app_tech.description,

                    )
                    new_app_tech.save()

        for app_mater in _app_materials:
            _app_m, _ = ApplicationMeterial.objects.get_or_create(
                app_for_day=new_app_today,
                description=app_mater.description,

            )
            _app_m.save()

    return HttpResponseRedirect(f'/applications/{date_of_target}')


def append_in_spec_tech(request, id_td):
    technic_driver = TechnicDriver.objects.get(id=id_td)
    current_day = technic_driver.date

    var_message, _ = Variable.objects.get_or_create(name='DEF_MESS_FOR_SPEC')
    if not var_message.value:
        message = TEXT_TEMPLATES['default_mess_for_spec']
    else:
        message = var_message.value

    if technic_driver.driver is None or not technic_driver.driver.status:
        return HttpResponseRedirect(f'/applications/{current_day}')

    constr_site, _ = ConstructionSite.objects.get_or_create(
        address=TEXT_TEMPLATES['constr_site_spec_name'],
        foreman=None)
    constr_site.status = STATUS_CS_opened
    constr_site.save()

    app_for_day, _ = ApplicationToday.objects.get_or_create(
        construction_site=constr_site,
        date=current_day)
    app_for_day.status = STATUS_APP_submitted
    app_for_day.save()

    if not technic_driver.technic.tech_type.name in ('Спец. техника', 'Экскаватор'):
        if not technic_driver.technic.name.name in ('Каток',):
            message = ''

    ApplicationTechnic.objects.get_or_create(
        app_for_day=app_for_day,
        technic_driver=technic_driver,
        description=message
    )

    return HttpResponseRedirect(f"/applications/{current_day}")


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
    technic_driver_table = TechnicDriver.objects.filter(date=current_day, technic__isnull=False)
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
        free_td = technic_driver_table.filter(id__in=free_td_id).values_list(
            'driver__driver__last_name', 'driver__driver__first_name', 'id')
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
        technic_driver_id__in=get_priority_list(current_day, get_td_id=True)).values_list('technic_driver_id',
                                                                                          flat=True)
    for pr in ds:
        clr = rand_choice(COLOR_LIST)
        if clr not in out['prior_color'].values():
            out['prior_color'][pr] = clr
        else:
            COLOR_LIST.remove(clr)
            out['prior_color'][pr] = rand_choice(COLOR_LIST)

    var_sort_driver_panel = get_var(VAR['sort_drv_panel'], user=request.user)
    technic_driver_table = TechnicDriver.objects.filter(date=current_day)
    #   --------------------------------------------------------------------------------------------------------------------
    if var_sort_driver_panel and var_sort_driver_panel.value:
        try:
            out["DRV_LIST"] = technic_driver_table.order_by(f'{var_sort_driver_panel.value}')
        except:
            out["DRV_LIST"] = technic_driver_table.order_by('driver__driver__last_name')
    else:
        out["DRV_LIST"] = technic_driver_table.order_by('driver__driver__last_name')
    out['work_drv'] = get_count_app_for_driver(current_day, just_list=True)

    if request.POST.get('panel'):
        _flag = request.POST.get('panel')
        _flag = str(_flag).capitalize()
        set_var('hidden_panel', value=request.user.id, flag=_flag, user=request.user)

    out['var_drv_panel'] = get_var('hidden_panel', user=request.user)

    #   --------------------------------------------------------------------------------------------------------------------

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
        if get_conflicts_vehicles_list(current_day, c_in=0):
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

    if "archive" in request.path:
        arch_constr_sites_list = []

        for site in aConstructionSite.objects.using(ARCHIVE_DB).all().exclude(address=None):
            arch_constr_sites_list.append(AConstructionSite(site.id_C_S))

        arch_constr_sites_list = sorted(arch_constr_sites_list, key=lambda x: x.address)
        out['arch_constr_sites'] = arch_constr_sites_list

        return render(request, 'archive/archive_construction_sites.html', out)

    all_constr_site_list = ConstructionSite.objects.all().order_by('address').exclude(address=None, foreman=None)

    #   Исключить объекты для Снабжения и Спец. задание
    all_constr_site_list = all_constr_site_list.exclude(foreman=None)

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
        make_backup_construction_site(id_constr_site=construction_sites.pk, action='edit')
        return HttpResponseRedirect('/construction_sites/')

    return render(request, 'edit_construction_site.html', out)


def delete_construction_sites_view(request, id_construction_sites):
    construction_sites = ConstructionSite.objects.get(id=id_construction_sites)
    make_backup_construction_site(id_constr_site=id_construction_sites, action='del')
    construction_sites.delete()  # TODO: Fix del
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
        make_backup_construction_site(id_constr_site=construction_sites.pk, action='add')

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
            _tel = Post.objects.get(user_post=_user).telephone  # get_current_post(_user)
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

        make_backup_staff(id_staff=selected_user.pk, action='edit')

        if is_admin(request.user) or is_mechanic(request.user):
            return HttpResponseRedirect('/show_staff/')
        else:
            return HttpResponseRedirect('/')
    return render(request, 'edit_staff.html', out)


# STAFF-----------------------------------------------STAFF-------------------------------------------------------------

# TABEL----------------------------------------------------------------------------------------TABEL--------------------


def tabel_driver_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    current_day = convert_str_to_date(day)

    if current_day < TODAY:
        return HttpResponseRedirect(f'/archive_driver/{current_day}')

    out = {}
    get_prepare_data(out, request, current_day)

    _exc_post = Post.objects.filter(post_name__name_post=POST_USER['driver']).exclude(
        user_post__id__in=DriverTabel.objects.filter(date=current_day).values_list('driver__id', flat=True)
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
        _day = TODAY + timedelta(7)
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

    current_day = convert_str_to_date(day)

    if current_day < TODAY:
        return HttpResponseRedirect(f'/archive_technic_driver/{current_day}')

    out = {}
    get_prepare_data(out, request, current_day)

    if DriverTabel.objects.filter(date=current_day, status=True).count() == 0:
        prepare_driver_table(day)

    if not TechnicDriver.objects.filter(date=current_day).exists():
        prepare_technic_driver_table(day)
    else:
        technic_driver_list = TechnicDriver.objects.filter(date=current_day, technic__isnull=False)

        if current_day >= TODAY and technic_driver_list.count() != Technic.objects.all().count():
            tech_exc = Technic.objects.filter().exclude(
                id__in=technic_driver_list.values_list('technic__id', flat=True))
            for _tech in tech_exc:
                TechnicDriver.objects.create(
                    date=current_day,
                    technic=_tech,
                    status=True
                )

        for _td in technic_driver_list:
            if not _td.driver:
                _attach_drv = _td.technic.attached_driver
                if not _attach_drv:
                    continue
                _attach_drv_staff = DriverTabel.objects.get(driver=_attach_drv, date=current_day)
                if _attach_drv_staff.status:
                    if not technic_driver_list.filter(driver__driver=_attach_drv_staff.driver).exists():
                        _td.driver = _attach_drv_staff
                        _td.save()
                else:
                    _td.driver = None
                    _td.save()

    work_driver_list = DriverTabel.objects.filter(date=current_day, status=True)
    technic_driver_list = TechnicDriver.objects.filter(date=current_day, technic__isnull=False)
    exclude_drv = DriverTabel.objects.filter(date=current_day, status=True).exclude(
        driver__in=list(TechnicDriver.objects.filter(
            date=current_day).exclude(technic=None).values_list('driver__driver', flat=True)))
    if exclude_drv.exists():
        for exc_drv in exclude_drv:
            _td, _ = TechnicDriver.objects.get_or_create(
                date=current_day,
                driver=exc_drv,
                technic=None
            )
            _td.status = False
            _td.save()
        TechnicDriver.objects.filter(date=current_day, technic__isnull=True).exclude(driver__in=exclude_drv).delete()
    else:
        TechnicDriver.objects.filter(date=current_day, technic__isnull=True).exclude(driver__in=exclude_drv).delete()

    out['work_driver_list'] = work_driver_list.order_by('driver__last_name')
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


# -----------------------------------------------------TABEL-------------------------------------------------------------


def clear_application_view(request, id_application):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    if AUTO_CREATE_BACKUP_DB and is_admin(request.user):
        create_backup_db()
    current_application = ApplicationToday.objects.get(id=id_application)
    app_tech = ApplicationTechnic.objects.filter(app_for_day=current_application)

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

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


# ===============================================================================================
def show_applications_view(request, day, id_user=None):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    current_day = convert_str_to_date(day)
    if not current_day:
        return HttpResponseRedirect('/')

    if current_day < TODAY:
        return HttpResponseRedirect(f'/archive/{current_day}')

    out = {"constr_site_list": []}

    if id_user:
        current_user = User.objects.get(id=id_user)
        out['current_user'] = current_user
    else:
        current_user = request.user

    get_prepare_data(out, request, current_day)
    status_day = check_table(current_day)
    out['status_day'] = status_day
    out['READ_ONLY_MODE'] = get_read_only_mode()
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

        out['conflicts_vehicles_list_id'] = get_conflicts_vehicles_list(current_day)

        if _Application_today.filter(status=STATUS_APP_submitted).exists():
            out['submitted_app_list'] = True

        if _Application_today.filter(status=STATUS_APP_approved).exists():
            out['send_app_list'] = True

        technic_driver_table = TechnicDriver.objects.filter(date=current_day)
        var_sort_driver_panel = get_var(VAR['sort_drv_panel'], user=request.user)
        #   --------------------------------------------------------------------------------------------------------------------
        if var_sort_driver_panel and var_sort_driver_panel.value:
            try:
                out["DRV_LIST"] = technic_driver_table.order_by(f'{var_sort_driver_panel.value}')
            except:
                out["DRV_LIST"] = technic_driver_table.order_by('driver__driver__last_name')
        else:
            out["DRV_LIST"] = technic_driver_table.order_by('driver__driver__last_name')
        out['work_drv'] = get_count_app_for_driver(current_day, just_list=True)

        #   --------------------------------------------------------------------------------------------------------------------
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

        materials_list = _Application_material

        out['technic_driver_table_TT'] = technic_driver_table.filter(
            status=True, driver__status=True).order_by('driver__driver__last_name')

        out['app_technic_today'] = _Application_technic.values(
            'technic_driver_id',
            'technic_driver__driver__driver__last_name',
            'technic_driver__technic__name__name'
        ).distinct().order_by('technic_driver__driver__driver__last_name')

        out['backups_list'] = get_list_db_backup()

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
                app_for_day=appToday).values_list('description', 'status_checked').first()
            out['today_applications_list'].append({'app_today': appToday, 'app_mater': appMater})
    else:
        for appToday in app_for_day.order_by('construction_site__address'):
            appTech = _Application_technic.filter(app_for_day=appToday)
            appMater = materials_list.filter(
                app_for_day=appToday).values_list('description', 'status_checked').first()

            out['today_applications_list'].append({'app_today': appToday, 'apps_tech': appTech, 'app_mater': appMater})

    # out['apps_today_save'] = app_for_day.filter(status=STATUS_APP_saved)
    out['apps_today_save'] = app_for_day.exclude(status=STATUS_APP_absent)

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

    if is_driver(current_user) and current_day < TODAY:
        return HttpResponseRedirect(f"/archive_personal_app/{current_day}/{request.user.id}")

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

    if current_day < TODAY:
        return HttpResponseRedirect(f'/archive_all_app/{day}')

    out = {}
    get_prepare_data(out, request, current_day)
    out["date_of_target"] = current_day

    app_today = ApplicationToday.objects.filter(date=current_day).exclude(status=STATUS_APP_absent)

    foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman'])
    out['foreman_list'] = foreman_list

    out['filter_group_by_list'] = sorted(set(Technic.objects.filter().values_list(
        'name_id', 'name__name')), key=lambda x: x[1])

    out['filter_sorting_list'] = TEXT_TEMPLATES['filter_sorting_list']

    _FILTER = get_var(VAR['FILTER_APP_TODAY'], value=True, user=request.user)
    try:
        F_foreman, F_constr_site, F_group, F_sort = _FILTER.split(',')
    except ValueError:
        F_foreman = 'all'
        F_constr_site = 'all'
        F_group = 'all'
        F_sort = 'all'

    if F_foreman == 'all':
        constr_site_list = app_today.values('construction_site_id', 'construction_site__address')
    else:
        constr_site_list = app_today.filter(construction_site__foreman_id=F_foreman).values(
            'construction_site_id',
            'construction_site__address'
        )
    out['constr_site'] = constr_site_list

    if request.method == "POST":
        fil_foreman = request.POST.get('foreman')
        fil_constr_site = request.POST.get('constr_site')
        fil_group = request.POST.get('group')
        fil_sort = request.POST.get('sort')

        v = ['all', 'all', 'all', 'all']

        if fil_foreman is not None:
            v[0] = fil_foreman
        elif fil_foreman == 'None':
            v[0] = 'all'
        else:
            v[0] = F_foreman

        if fil_constr_site is not None:
            v[1] = fil_constr_site
        elif fil_constr_site == 'None':
            v[1] = 'all'
        else:
            v[1] = F_constr_site

        if fil_group is not None:
            v[2] = fil_group
        elif fil_group == 'None':
            v[2] = 'all'
        else:
            v[2] = F_group

        if fil_sort is not None:
            v[3] = fil_sort
        elif fil_sort == 'None':
            v[3] = 'all'
        else:
            v[3] = F_sort
        set_var(VAR['FILTER_APP_TODAY'], value=f"{v[0]},{v[1]},{v[2]},{v[3]}", user=request.user)

        # return HttpResponseRedirect(request.META['HTTP_REFERER'])

#   ============================================================================

    if F_foreman == 'all':
        _app_today = app_today
    elif F_foreman == 'supply':
        _app_today = app_today.filter(construction_site__address=TEXT_TEMPLATES['constr_site_supply_name'])
        out['filter_foreman'] = TEXT_TEMPLATES['constr_site_supply_name']
    elif F_foreman is not None:
        _app_today = app_today.filter(construction_site__foreman_id=F_foreman)
        out['filter_foreman'] = User.objects.get(pk=F_foreman).last_name
    else:
        _app_today = app_today

    if F_constr_site != 'all':
        _app_today = _app_today.filter(construction_site_id=F_constr_site)
        out['filter_constr_site'] = ConstructionSite.objects.get(pk=F_constr_site).address

    _app = ApplicationTechnic.objects.filter(app_for_day__in=_app_today)

    if is_admin(request.user):
        app_tech_day = _app.filter(
            Q(app_for_day__status=STATUS_APP_submitted) |
            Q(app_for_day__status=STATUS_APP_approved) |
            Q(app_for_day__status=STATUS_APP_send)
        ).exclude(var_check=True)
    else:
        app_tech_day = _app.filter(app_for_day__status=STATUS_APP_send).exclude(var_check=True)

    if F_group != 'all':
        app_tech_day = app_tech_day.filter(technic_driver__technic__name_id=F_group)
        for gby in out['filter_group_by_list']:
            if f'{gby[0]}' == F_group:
                out['filter_group_by'] = gby[1]
    else:
        pass

    if F_sort == 'driver':
        driver_technic = app_tech_day.values_list(
            'technic_driver__driver__driver__last_name',
            'technic_driver__technic__name__name').order_by(
            'technic_driver__driver__driver__last_name').distinct()
        out['filter_sorting'] = TEXT_TEMPLATES['filter_sorting_list']['driver']

    elif F_sort == 'technic':
        driver_technic = app_tech_day.values_list(
            'technic_driver__driver__driver__last_name',
            'technic_driver__technic__name__name').order_by(
            'technic_driver__technic__name__name').distinct()
        out['filter_sorting'] = TEXT_TEMPLATES['filter_sorting_list']['technic']

    # elif F_sort == 'constr_site':
        # driver_technic = app_tech_day.values_list(
        #     'technic_driver__driver__driver__last_name',
        #     'technic_driver__technic__name__name').order_by(
        #     'technic_driver__technic__name__name').distinct()
        # out['filter_sorting'] = TEXT_TEMPLATES['filter_sorting_list']['constr_site']
        # pass

    else:
        driver_technic = app_tech_day.values_list(
            'technic_driver__driver__driver__last_name',
            'technic_driver__technic__name__name').order_by(
            'technic_driver__technic__name__name').distinct()

    app_list = []
    for _drv, _tech in driver_technic:
        desc = app_tech_day.filter(
            technic_driver__driver__driver__last_name=_drv,
            technic_driver__technic__name__name=_tech).order_by('priority')

        _id_list = [_[0] for _ in desc.values_list('id')]

        if (_drv, _tech, desc, _id_list) not in app_list:
            app_list.append((_drv, _tech, desc, _id_list))



    out["today_technic_applications"] = app_list

#   ======================================================================

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


def show_today_materials(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    current_day = convert_str_to_date(day)
    if current_day < TODAY:
        return HttpResponseRedirect(f'/archive_all_materials/{day}')
    # elif current_day < TODAY:
    #     return HttpResponseRedirect(f'/archive_all_app/{day}')
    out = {}
    get_prepare_data(out, request, current_day)
    out["date_of_target"] = current_day

    app_today = ApplicationToday.objects.filter(date=current_day).exclude(status=STATUS_APP_absent)

    foreman_list = Post.objects.filter(post_name__name_post=POST_USER['foreman'])
    out['foreman_list'] = foreman_list

    _FILTER = get_var(VAR['FILTER_APP_TODAY'], value=True, user=request.user)
    try:
        F_foreman, F_constr_site, F_group, F_sort = _FILTER.split(',')
    except ValueError:
        F_foreman = 'all'
        F_constr_site = 'all'
        F_group = 'all'
        F_sort = 'all'

    if F_foreman == 'all':
        constr_site_list = app_today.values('construction_site_id', 'construction_site__address')
    else:
        constr_site_list = app_today.filter(construction_site__foreman_id=F_foreman).values(
            'construction_site_id',
            'construction_site__address'
        )
    out['constr_site'] = constr_site_list

    if request.method == "POST":
        fil_foreman = request.POST.get('foreman')
        fil_constr_site = request.POST.get('constr_site')
        fil_group = request.POST.get('group')
        fil_sort = request.POST.get('sort')

        v = ['all', 'all', 'all', 'all']

        if fil_foreman is not None:
            v[0] = fil_foreman
        elif fil_foreman == 'None':
            v[0] = 'all'
        else:
            v[0] = F_foreman

        if fil_constr_site is not None:
            v[1] = fil_constr_site
        elif fil_constr_site == 'None':
            v[1] = 'all'
        else:
            v[1] = F_constr_site

        if fil_group is not None:
            v[2] = fil_group
        elif fil_group == 'None':
            v[2] = 'all'
        else:
            v[2] = F_group

        if fil_sort is not None:
            v[3] = fil_sort
        elif fil_sort == 'None':
            v[3] = 'all'
        else:
            v[3] = F_sort
        set_var(VAR['FILTER_APP_TODAY'], value=f"{v[0]},{v[1]},{v[2]},{v[3]}", user=request.user)

        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    if F_foreman != 'all':
        _app_today = app_today.filter(
            construction_site__foreman_id=F_foreman
        )
        out['filter_foreman'] = User.objects.get(pk=F_foreman).last_name
    else:
        _app_today = app_today

    if F_constr_site != 'all':
        _app_today = _app_today.filter(
            construction_site_id=F_constr_site
        )
        out['filter_constr_site'] = ConstructionSite.objects.get(pk=F_constr_site).address

    app_materials = ApplicationMeterial.objects.filter(
        app_for_day__in=_app_today,
        status_checked=True
    )

    out['materials_list'] = app_materials

    return render(request, 'extend/material_today_app.html', out)


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

    out['READ_ONLY_MODE'] = get_read_only_mode()

    flag = check_table(current_date)
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
    # print(Tech_driver_list.count())
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
        if AUTO_CREATE_BACKUP_DB and is_admin(request.user):
            create_backup_db()
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
    driver_tab = DriverTabel.objects.filter(
        driver=user,
        # date__lt=TODAY
    )
    make_backup_staff(id_staff=id_staff, action='del')
    driver_tab.delete()
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

            send_debug_messages(
                messages=f'created new user: \nun {username}\npwd {password}\nfn {first_name}\nln {last_name}')

            if post_id:
                post_name = PostName.objects.get(id=post_id)
            else:
                post_name = None

            if foreman_id:
                foreman = User.objects.get(id=foreman_id)
            else:
                foreman = None

            # _count_post = Post.objects.all().count()+1
            _count_post = max(Post.objects.values_list('id', flat=True)) + 1
            Post.objects.create(
                id=_count_post,
                user_post=new_user,
                post_name=post_name,
                telephone=telephone,
                supervisor=foreman)
            make_backup_staff(id_staff=new_user.pk, action='add')

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

        clear_db_backup()

    return HttpResponseRedirect(f'/applications/{day}')


def approv_all_applications(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    if AUTO_CREATE_BACKUP_DB and is_admin(request.user):
        create_backup_db()
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

    if F_saved:  # if ApplicationTechnic has status = 'saved'
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
        if list_of_work_tech.count(i) + c_in > count_technics[i]:
            if lack:
                _c = list_of_work_tech.count(i) - count_technics[i]
                _name = TechnicName.objects.get(id=i).name
                out.append((_name, _c))
            else:
                out.append(i)
    return out


def get_count_app_for_driver(current_day, just_list=False):
    out = []
    _tech_drv = [_[0] for _ in TechnicDriver.objects.filter(
        date=current_day,
        driver__status=True).values_list('id')]
    _app = [_[0] for _ in ApplicationTechnic.objects.filter(
        Q(var_check=False),
        Q(app_for_day__date=current_day),
        Q(app_for_day__status=STATUS_APP_approved) |
        Q(app_for_day__status=STATUS_APP_submitted) |
        Q(app_for_day__status=STATUS_APP_send)
    ).values_list('technic_driver_id')]

    if just_list:
        for _td in set(_tech_drv):
            if _app.count(_td) > 0:
                out.append(_td)
    else:
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
            return HttpResponseRedirect(f"personal_application/{get_current_day('current_day')}/{request.user.id}")
        elif is_mechanic(request.user):
            return HttpResponseRedirect(f"tech_list/{get_current_day('next_day')}")
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
    # print(request.user.last_name)
    # print(check_last_activity(request.user.last_login))

    out['message_status'] = False
    out['nw_day'] = str(get_current_day('next_day'))
    out['cw_day'] = str(get_current_day(get_CH_day(current_day)))
    out['lw_day'] = str(get_current_day('last_day'))
    out["WEEKDAY_TODAY"] = WEEKDAY[TODAY.weekday()]
    out['TODAY'] = f'{TODAY.day} {MONTH[TODAY.month - 1]}'
    out["DAY"] = f'{current_day.day} {MONTH[current_day.month - 1]}'
    out["WEEKDAY"] = WEEKDAY[current_day.weekday()]
    out["post"] = get_current_post(request.user)
    out['tense'] = current_day >= TODAY
    out['referer'] = request.headers.get('Referer')
    out['weekend_flag'] = TODAY.weekday() == 4 and get_current_day(
        'next_day').weekday() == 5 and current_day.weekday() == 0
    out['LOG_DB'] = clean_db(_flag_delete=AUTO_CLEAR_DB, _flag_backup=True)

    out['server_time'] = datetime.datetime.now().time()
    out['server_datetime_now'] = datetime.datetime.now()

    return out


def success_application(request, id_application):
    """Изменение статуса заявки"""
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    if AUTO_CREATE_BACKUP_DB and is_admin(request.user):
        create_backup_db()

    current_application = ApplicationToday.objects.get(id=id_application)
    current_day = convert_str_to_date(current_application.date)

    send_flag = Variable.objects.filter(name=VAR['sent_app'], date=current_day, flag=True).exists()
    #  _day = f"{WEEKDAY[current_day.weekday()]}, {current_day.day} {MONTH[current_day.month.numerator]}"

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
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def __get_current_day(selected_day: str):  # TODO: for del
    """Получить (следующий, текущий, прошлый) рабочий день """
    if selected_day == 'next_day':
        for n in range(1, 14):
            try:
                _day = WorkDayTabel.objects.get(date=TODAY + timedelta(n))
                if _day.status:
                    return _day.date
            except WorkDayTabel.DoesNotExist:
                prepare_work_day_table(TODAY + timedelta(n))

            # if _day.status:
            #     return _day.date
    elif selected_day == 'last_day':
        for n in range(14):
            _day = WorkDayTabel.objects.get(date=TODAY - timedelta(n))
            if _day.status:
                return _day.date
    else:
        return selected_day


def get_current_day(selected_day: str):
    """Получить (следующий, текущий, прошлый) рабочий день """
    if selected_day == 'next_day':
        _day = WorkDayTabel.objects.filter(date__gt=TODAY, status=True).first()
        if _day:
            return _day.date
        else:
            prepare_work_day_table(TODAY)

    elif selected_day == 'last_day':
        _day = WorkDayTabel.objects.filter(date__lte=TODAY, status=True).last()
        if _day:
            return _day.date
    elif selected_day == 'current_day':
        _day = WorkDayTabel.objects.get(date=TODAY)
        if _day is not None and _day.status:
            return _day.date
        else:
            _day = WorkDayTabel.objects.filter(date__gt=TODAY, status=True).first()
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

    if not WorkDayTabel.objects.get(date=current_day).status:
        return None

    driver_list = Post.objects.filter(post_name__name_post=POST_USER['driver'])
    _ex_td = driver_list.exclude(
        user_post__id__in=DriverTabel.objects.filter(date=current_day).values_list('driver__id', flat=True))
    if current_day > TODAY:
        try:
            if _ex_td.exists():
                for dr in _ex_td:
                    DriverTabel.objects.create(driver=dr.user_post, date=current_day)
            else:
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
    tech_drv_list_today = TechnicDriver.objects.filter(date=TODAY, technic__isnull=False)

    if not WorkDayTabel.objects.get(date=current_day).status:
        return None

    if current_day > TODAY:

        for _tech in Technic.objects.all():
            _drv = tech_drv_list_today.filter(technic=_tech).values_list('driver__driver', 'status').first()
            if _drv is not None:
                driver = _drv[0]
                status = _drv[1]
            else:
                driver = _tech.attached_driver
                status = False

            c_drv = work_driver_list.filter(driver=driver)

            if c_drv.exists():
                TechnicDriver.objects.create(
                    technic=_tech,
                    driver=work_driver_list.get(date=current_day, driver=driver),
                    date=current_day,
                    status=status)
            else:
                TechnicDriver.objects.create(
                    technic=_tech,
                    driver=None,
                    date=current_day,
                    status=status
                )

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


def send_task_for_drv(current_day, messages=None, id_app_today=None):
    out = []
    _driver_list = DriverTabel.objects.filter(date=current_day, status=True)
    send_flag = Variable.objects.filter(name=VAR['sent_app'], date=current_day, flag=True).exists()
    _day = f"{WEEKDAY[current_day.weekday()]}, {current_day.day} {MONTH[current_day.month.real - 1]}"

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
                if _a.app_for_day.construction_site.foreman is not None:
                    mss += f"\t{_a.priority}) {_a.app_for_day.construction_site.address} ({_a.app_for_day.construction_site.foreman}):\n"
                else:
                    mss += f"\t{_a.priority}) {_a.app_for_day.construction_site.address}:\n"

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
                if s.app_for_day.construction_site.foreman is not None:
                    mss += f"\t{s.priority}) {s.app_for_day.construction_site.address} ({s.app_for_day.construction_site.foreman})\n"
                else:
                    mss += f"\t{s.priority}) {s.app_for_day.construction_site.address}\n"

            mss += f"{s.description}\n\n"
        if messages:
            mss = messages
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
    _day = f"{WEEKDAY[current_day.weekday()]}, {current_day.day} {MONTH[current_day.month.real - 1]}"

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
    _day = f"{WEEKDAY[current_day.weekday()]}, {current_day.day} {MONTH[current_day.month.real - 1]}"
    if id_app_today:
        _app = ApplicationToday.objects.get(id=id_app_today)
        if _app.construction_site.foreman is not None:
            foreman = f'({_app.construction_site.foreman.last_name})'
        else:
            foreman = ''
        if send_flag:
            messages = f"Заявка на:\n{_day}\nобъект: {_app.construction_site.address} {foreman} отправлена повторно"
        else:
            messages = f"Заявка на:\n{_day}\nобъект: {_app.construction_site.address} {foreman} отправлена"

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

        technic_driver_list = TechnicDriver.objects.filter(date=date, technic__isnull=False)
        if technic_driver_list.count() != Technic.objects.all().count():
            tech_exc = Technic.objects.filter().exclude(
                id__in=technic_driver_list.values_list('technic__id', flat=True))
            for _tech in tech_exc:
                TechnicDriver.objects.create(
                    date=date,
                    technic=_tech,
                    status=True
                )

        prepare_application_today(day)
        print('workday')
    elif _today.date < TODAY:
        pass

    else:
        print('weekend')
        return False
    return True


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


def restore_pwd_view(request, id_user=None):
    MESSAGES = (
        'Данный пользователь является администратором, чтобы сбросить пароль обратитесь к другому администратору',
        'Ваш пароль был сброшен на стандартный: 1234 '
    )

    if request.user.is_authenticated:
        return HttpResponseRedirect('/')

    out = {
        'TODAY': TODAY,
        'WEEKDAY_TODAY': WEEKDAY[TODAY.weekday()],
    }

    if id_user:
        out['id_user'] = id_user
        cur_user = User.objects.get(id=id_user)
        cur_post = Post.objects.get(user_post=cur_user)

        if cur_post.post_name is not None and cur_post.post_name.name_post == POST_USER['admin']:
            out['id_user_mess'] = MESSAGES[0]
        else:
            cur_user.set_password('1234')
            cur_user.save()
            send_debug_messages(f"Chande password:\n\t{cur_user.last_name}")
            out['id_user_mess'] = MESSAGES[1]

    personals = Post.objects.filter()  # .exclude(post_name=PostName.objects.get(name_post=POST_USER['admin']))
    if request.method == 'POST':
        found_user = request.POST['last_name']
        found_user = str(found_user).strip(' ')

        if found_user:
            fu = personals.filter(
                user_post__last_name__icontains=found_user
            ).values_list(
                'user_post__last_name', 'user_post__first_name', 'post_name__name_post', 'user_post__id').order_by(
                'user_post__last_name')
            if not fu.exists():
                fu = personals.filter(
                    user_post__last_name__icontains=found_user.capitalize()
                ).values_list(
                    'user_post__last_name', 'user_post__first_name', 'post_name__name_post', 'user_post__id').order_by(
                    'user_post__last_name')
                if not fu.exists():
                    out['message_status'] = True
                    out['message'] = 'Данный пользователь не найден!'

        else:
            fu = ''
            out['message_status'] = True
            out['message'] = 'Данный пользователь не найден!'
        out['fu'] = fu

    return render(request, 'restore_pwd.html', out)


def show_archive_page_view(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    work_day = aTWorkDay.objects.using(ARCHIVE_DB).get(date=day)
    out['status_day'] = work_day.status

    apps = get_application_today(work_day.date)
    out['apps'] = apps

    return render(request, 'archive/archive_page.html', out)


def show_archive_all_app(request, day, filter_foreman=None, filter_csite=None):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')
    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    work_day = aTWorkDay.objects.using(ARCHIVE_DB).get(date=day)

    apps = get_application_today(work_day.date)
    out['apps'] = apps

    if 'materials' in request.path:
        return render(request, 'archive/archive_material_today_app.html', out)

    def filter_app(_apps: list):
        # (priority, last_name, technic.name, address, description)
        _tmp = _apps.copy()
        for i in range(len(_apps)-1):
            if _apps[i][1:3] == _apps[i+1][1:3]:
                if TEXT_TEMPLATES['constr_site_supply_name'] in _apps[i][3]:
                    _tmp.remove(_apps[i+1])
                elif TEXT_TEMPLATES['constr_site_supply_name'] in _apps[i+1][3]:
                    _tmp.remove(_apps[i])
        return _tmp

    driver_technic = []
    for app in apps:
        for tech in app.applications_technic:
            if TEXT_TEMPLATES['dismiss'] not in tech.description:
                driver_technic.append((
                    int(tech.priority),
                    tech.technic_driver.driver.driver.last_name if tech.technic_driver.driver is not None else '',
                    tech.technic_driver.technic.name,
                    app.construction_site.address,
                    tech.description
                ))

    driver_technic = set(driver_technic)
    driver_technic = sorted(driver_technic, key=lambda x: (x[1], x[0]),)
    driver_technic = filter_app(driver_technic)

    out['driver_technic'] = driver_technic

    return render(request, 'archive/archive_today_applications.html', out)


def show_archive_technic_driver(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    technic_driver_list = []

    for technic_driver in aTTechnicDriver.objects.using(ARCHIVE_DB).filter(date=day):
        technic_driver_list.append(ATTechnicDriver(technic_driver.id_T_D))

    technic_driver_list = sorted(technic_driver_list, key=lambda x: x.technic.name)
    out['technic_driver_list'] = technic_driver_list

    return render(request, 'archive/archive_technic_driver.html', out)


def show_archive_driver(request, day):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/')

    out = {}
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    driver_list = []

    for technic_driver in aTDriver.objects.using(ARCHIVE_DB).filter(date=day):
        driver_list.append(ATDriver(technic_driver.id_D))

    driver_list = sorted(driver_list, key=lambda x: x.driver.last_name)
    out['driver_list'] = driver_list

    return render(request, 'archive/archive_driver.html', out)


def change_status_technic_driver(request):
    if request.method == 'POST':
        if request.POST.get('technic_driver_id'):
            _td = TechnicDriver.objects.get(pk=request.POST.get('technic_driver_id'))
            _td.status = False if _td.status else True
            _td.save()
        if request.POST.get('driver_id'):
            _d = DriverTabel.objects.get(pk=request.POST.get('driver_id'))
            _d.status = False if _d.status else True
            _d.save()
        # print(request.POST)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def show_personal_app_for_driver(request, day, id_user):
    out = {}
    current_user = request.user
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    out["current_user"] = current_user

    _driver = aTDriver.objects.using(ARCHIVE_DB).get(date=current_day, driver_i=current_user.pk)
    _technic_driver = aTTechnicDriver.objects.using(ARCHIVE_DB).get(driver_i=_driver.id_D)

    id_supply_list = Post.objects.filter(
        post_name__name_post=POST_USER['employee_supply']).values_list('user_post_id', flat=True)

    supply_driver_id_list = Post.objects.filter(supervisor_id__in=id_supply_list).values_list('user_post_id', flat=True)

    applications = []
    material_list = []

    apps = get_application_today(current_day)

    for app in apps:
        for at in app.applications_technic:
            if at.technic_driver.id == _technic_driver.id_T_D and at.technic_driver.driver.id == _driver.id_D:
                applications.append({
                    'address': app.construction_site.address,
                    'foreman': app.construction_site.foreman.last_name if app.construction_site.foreman is not None else None,
                    'technic': at.technic_driver.technic.name,
                    'description': at.description,
                    'priority': at.priority
                })

        if current_user.id in supply_driver_id_list:
            for am in app.applications_material:
                material_list.append({
                    'address': app.construction_site.address,
                    'foreman': app.construction_site.foreman.last_name if app.construction_site.foreman is not None else None,
                    'description': am.description
                })

    applications = sorted(applications, key=lambda x: x['priority'])
    out['applications'] = applications
    out['material_list'] = material_list

    return render(request, 'archive/archive_applications_for_driver.html', out)


def show_archive_supply_app(request, day):
    out = {}
    current_user = request.user
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)

    _day = aTWorkDay.objects.using(ARCHIVE_DB).get(date=current_day)
    out['status_day'] = _day.status
    app_for_day = []

    if _day.status:
        apps = get_application_today(_day.date)
        for app in apps:
            if TEXT_TEMPLATES['constr_site_supply_name'] in app.construction_site.address:
                app_for_day.append(app)

    out['apps_today'] = app_for_day

    return render(request, 'archive/archive_supply_app.html', out)


def show_archive_supply_materials(request, day):
    out = {}
    current_user = request.user
    current_day = convert_str_to_date(day)
    get_prepare_data(out, request, current_day)


    app_for_day = []
    apps = get_application_today(current_day)

    # for app in apps:
    #     if TEXT_TEMPLATES['constr_site_supply_name'] in app.construction_site.address:
    #         app_for_day.append(app)

    out['apps'] = apps

    return render(request, 'archive/archive_supply_app_materials.html', out)


def change_read_only_mode(request):
    if is_admin(request.user):
        if request.GET.get('readonly_mode') == 'change':
            # print(request.GET.get('readonly_mode'))
            try:
                read_only_mode = Variable.objects.get(name='read_only_mode', date=TODAY)
                if read_only_mode.flag:
                    read_only_mode.flag = False
                    read_only_mode.value = 'custom_false'
                    read_only_mode.save()
                else:
                    read_only_mode.flag = True
                    read_only_mode.value = 'custom_true'
                    read_only_mode.save()
            except Variable.DoesNotExist:
                pass
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
