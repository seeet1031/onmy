from django import template
from datetime import datetime, timedelta
from datetime import date

register = template.Library()

@register.filter(name='dict_key')
def dict_key(d, key):
    try:
        return d.get(key)
    except (TypeError, AttributeError):
        return None

@register.filter(name='addtime')
def addtime(value, minutes):
    """時間文字列に指定された分数を加算して返す"""
    time_obj = datetime.strptime(value, "%H:%M")
    new_time = time_obj + timedelta(minutes=int(minutes))
    return new_time.strftime("%H:%M")

@register.filter
def calculate_age(birth_date):
    if birth_date:
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return ''

@register.filter
def dict_has_key(dict_data, key):
    """辞書にキーが存在するかを確認するカスタムフィルター"""
    return key in dict_data

@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_doctor_id(schedule):
    # スケジュールから医師のIDを取得するロジック
    return schedule.doctor.id if schedule and hasattr(schedule, 'doctor') else None

@register.filter
def get_doctor_id_for_time(all_schedules, day_time, time):
    """
    all_schedulesから指定された日付と時間のスケジュールに関連付けられた医師のIDを取得するフィルタ
    """
    schedules_for_day = all_schedules.get(day_time)
    if schedules_for_day:
        for schedule in schedules_for_day:
            if schedule['time'] == time:
                return schedule['doctor_id']
    return ''

@register.filter
def add_minutes(time, minutes):
    if isinstance(time, str):
        time = datetime.strptime(time, "%H:%M")
    return (datetime.combine(date.today(), time) + timedelta(minutes=minutes)).time()