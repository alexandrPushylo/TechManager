# import os, shutil, sys
# from datetime import date, timedelta, datetime
# import telebot
# import requests
# from TechManager.settings import TELEGRAM_BOT_TOKEN as TOKEN
import os
import shutil
import sys
from datetime import date, timedelta, datetime, timezone
from random import choice
import requests
import telebot
from telebot.apihelper import ApiTelegramException
from manager.models import Variable

from TechManager.settings import TELEGRAM_BOT_TOKEN as TOKEN

# ---------------------------------------------------
NOW = datetime.now().time()
NOW_DATETIME = datetime.now().replace(microsecond=0).isoformat()
ONE_DAY = timedelta(days=1)
STATUS_APPLICATION = {"Подтвержден", "Не подтвержден", "Отменен"}
WEEKDAY = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
MONTH = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября','декабря')
TODAY = date.today()
TOMORROW = TODAY + ONE_DAY
dict_Staff = {'admin': 'Администратор', 'foreman': 'Прораб', 'master': 'Мастер', 'driver': 'Водитель', 'mechanic': 'Механик', 'employee_supply': 'Снабжение'}
status_application = {'absent': 'Отсутствует', 'saved': 'Сохранена', 'submitted': 'Подана', 'approved': 'Одобрена', 'send': 'Отправлена'}
status_constr_site = {'closed': 'Закрыт', 'opened': 'Открыт'}
PLATFORM = sys.platform
name_db = 'db.sqlite3'
archive_db = 'archive'
path_backup_db = f"..{os.sep}..{os.sep}temp_backup"

variable = {
    'sent_app': 'STATUS_sended_app',
    'font_size': 'font_size',
    'panel_for_supply': 'supply_panel',
    'FILTER_main_page': 'filter_main_apps',
    'cache': 'no_cache',
    'TIMEOUT_main_page': 'reload_main_page',
    'sort_drv_panel': 'var_sort_driver_panel',
    'font_color_main_page': 'style_font_color',
    'FILTER_APP_TODAY': 'FILTER_APP_TODAY',
    'LIMIT_for_submission': 'time_limit_for_submission',
    'LIMIT_for_apps': 'day_limit_before_del_apps',
    'last_clean_db': 'date_of_last_clean_db',
}
text_templates = {
    'dismiss': 'ОТКЛОНЕНА\r\n',
    'constr_site_supply_name': 'Снабжение',
    'constr_site_spec_name': 'Спец. задание',
    'default_mess_for_spec': 'Хоз. работы или за свой счет',
    'message_not_submitted': 'Имеются не поданные заявки',
    'message_invalid_password': 'Неверный логин или пороль',
    'user_exists': 'Такой пользователь уже существует',
    'filter_sorting_list': {
        'driver': 'Водители',
        'technic': 'Техника'
    }
}

TELE_URL = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
BOT = telebot.TeleBot(TOKEN, parse_mode=None)
# --FUNCTIONS-------------------------------------------------


def get_day_in_days(day: date, count_days: int):
    return day + timedelta(count_days)


# def get_difference(a: set, b: set):
#     return list(a.difference(b))


def get_week(c_date, week=None):
    if week == 'l':
        curr_date = c_date - timedelta(7)
    elif week == 'n':
        curr_date = c_date + timedelta(7)
    else:
        curr_date = c_date
    day_idx = (curr_date.weekday()) % 7
    sunday = curr_date - timedelta(days=day_idx)
    curr_date = sunday
    for n in range(7):
        yield curr_date
        curr_date += ONE_DAY


def convert_str_to_date(str_date: str) -> date:
    """конвертация str в datetime.date"""
    try:
        if isinstance(str_date, str):
            _day = datetime.strptime(str_date, '%Y-%m-%d').date()
            return _day
        elif isinstance(str_date, date):
            return str_date
    except:
        print('Error date')


def get_json():
    get_data = requests.get(TELE_URL)
    data_json = get_data.json()
    STATUS = data_json['ok']
    result = data_json['result']
    return result


def get_id_chat(key, result):
    for upd in result:
        if upd.get('message'):
            if upd.get('message').get('text') == key:
                return (upd['message']['chat']['id'])


def check_time(stop_time=None):
    if not stop_time:
        stop_time = datetime.now().time().replace(hour=16, minute=00)

    NOW = datetime.now().time()
    if NOW < stop_time:
        return stop_time

def is_backup_time():
    start = datetime.now().time().replace(hour=15, minute=00)
    stop = datetime.now().time().replace(hour=18, minute=00)
    if start < NOW < stop:
        return True
    else:
        return False

colors = [
    '#15b03e',
    '#5a9e6c',
    '#85d633',
    '#2b5403',
    '#f0dc05',
    '#fa9600',
    '#fa4f00',
    '#fa0400',
    '#00fae1',
    '#008efa',
    '#001dfa',
    '#9600fa',
    '#fa00ed',
]


def create_backup_db():
    target = f'{path_backup_db}{os.sep}{date.today()}_{datetime.now().time().strftime("%H-%M-%S")}.sqlite3'

    if not os.path.exists(path_backup_db):
        os.makedirs(path_backup_db)
    if PLATFORM == 'win32':
        os.popen(f"copy {name_db} {target}")
    else:
        os.popen(f"cp {name_db} {target}")


def get_list_db_backup():
    if not os.path.exists(path_backup_db):
        os.makedirs(path_backup_db)
    file_list = os.listdir(path_backup_db)
    out = []
    for iv in file_list:
        str_date = iv.replace('.sqlite3', '')
        _date = datetime.strptime(str_date, '%Y-%m-%d_%H-%M-%S')
        out.append(_date)

    return out


def restore_db_backup(backup, undo=False):
    if not os.path.exists(path_backup_db):
        os.makedirs(path_backup_db)
    file_list = os.listdir(path_backup_db)
    for iv in file_list:
        if iv == backup:
            target = f"{path_backup_db}{os.sep}{iv}"
            if undo:
                shutil.move(f"{target}", f"{name_db}")
            else:
                if PLATFORM == 'win32':
                    os.popen(f"copy {target} {name_db}")
                else:
                    os.popen(f"cp {target} {name_db}")



def delete_db_backup(backup):
    if not os.path.exists(path_backup_db):
        os.makedirs(path_backup_db)
    file_list = os.listdir(path_backup_db)
    for iv in file_list:
        if iv == backup:
            target = f"{path_backup_db}{os.sep}{iv}"
            os.remove(f"{target}")


def clear_db_backup():
    if not os.path.exists(path_backup_db):
        os.makedirs(path_backup_db)
    file_list = os.listdir(path_backup_db)

    for iv in file_list:
        str_date = iv.replace('.sqlite3', '')
        _date = datetime.strptime(str_date, '%Y-%m-%d_%H-%M-%S')
        if _date < datetime.now():# - timedelta(seconds=1):
            os.remove(f"{path_backup_db}{os.sep}{iv}")


def back24H(param: str='list', backup=None):
    name_db = 'db.sqlite3'
    path_backup24_db = f"..{os.sep}..{os.sep}backup"
    if not os.path.exists(path_backup24_db):
        os.makedirs(path_backup24_db)
    file_list = os.listdir(path_backup24_db)
    out = []
    for iv in file_list:
        str_date = iv.replace('.sqlite3', '')
        _date = datetime.strptime(str_date, '%Y-%m-%d_%H-%M')
        if param == 'list':
            out.append(_date)
        elif param == 'restore' and backup is not None:
            if backup == iv:
                target = f"{path_backup24_db}{os.sep}{iv}"
                if PLATFORM == 'win32':
                    os.popen(f"copy {target} {name_db}")
                else:
                    os.popen(f"cp {target} {name_db}")
    return out


def check_last_activity(_time: datetime):
    print(_time.time())
    print(datetime.now().time().replace(microsecond=0))
    if _time.time() < datetime.now().time():
        return True
    else:
        return False


def get_read_only_mode():
    var_name = 'read_only_mode'
    read_only_mode, created = Variable.objects.get_or_create(name=var_name, date=TODAY)
    # print(f'{created=}')
    if read_only_mode.time is None:
        read_only_mode.time = datetime.now().time().replace(hour=16, minute=0, second=0, microsecond=0)
        read_only_mode.save()

    if created:
        if read_only_mode.time < datetime.now().time():
            read_only_mode.flag = True
            read_only_mode.save()
        else:
            read_only_mode.flag = False
            read_only_mode.save()
    else:
        if read_only_mode.value is None or read_only_mode.value == '':
            if read_only_mode.time < datetime.now().time():
                read_only_mode.flag = True
                read_only_mode.save()
            else:
                read_only_mode.flag = False
                read_only_mode.save()

    Variable.objects.filter(name=var_name, date__lt=TODAY).delete()
    return read_only_mode.flag
