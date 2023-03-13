import time
from datetime import date, timedelta, datetime
from random import choice
import telebot
import requests
from TechManager.settings import TELEGRAM_BOT_TOKEN as TOKEN
# ---------------------------------------------------

ONE_DAY = timedelta(days=1)
STATUS_APPLICATION = {"Подтвержден", "Не подтвержден", "Отменен"}
WEEKDAY = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
MONTH = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября','декабря')
TODAY = date.today()
TOMORROW = TODAY + ONE_DAY
dict_Staff = {'admin': 'Администратор', 'foreman': 'Прораб', 'master': 'Мастер', 'driver': 'Водитель', 'mechanic': 'Механик', 'employee_supply': 'Снабжение'}
status_application = {'absent': 'Отсутствует', 'saved': 'Сохранена', 'submitted': 'Подана', 'approved': 'Одобрена', 'send': 'Отправлена'}
status_constr_site = {'closed': 'Закрыт', 'opened': 'Открыт'}

TELE_URL = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
BOT = telebot.TeleBot(TOKEN, parse_mode=None)
# --FUNCTIONS-------------------------------------------------


def get_day_in_days(day: date, count_days: int):
    return day + timedelta(count_days)


def get_difference(a: set, b: set):
    return list(a.difference(b))


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
        _day = datetime.strptime(str_date, '%Y-%m-%d').date()
        return _day
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


def check_time(stop_time=16):
    if not stop_time:
        stop_time = 16
    else:
        stop_time = int(stop_time)
    now = datetime.now().time()
    if now.hour in range(8, stop_time):
        return stop_time
