import json

from django_celery_beat.models import IntervalSchedule, PeriodicTask


def format_phone_number(phone_number):
    """ function to cast a phone number to the desired format -> +2 (xxx) xxx-xxxxx """
    ctx = list(str(phone_number))
    ctx.insert(0, '(')
    ctx.insert(4, ')')
    ctx.insert(8, '-')
    ctx.insert(5, ' ')
    formatted_phone_number = ''.join(ctx)
    return f'+2 {formatted_phone_number}'


def format_birthday(birthday_text):
    """ function for ghosting in the desired birthday format """
    s_birthday_text = birthday_text.split('/')
    num1 = s_birthday_text[0]
    num2 = s_birthday_text[1]

    if int(num1) > int(num2):
        x1 = num2
        x2 = num1
    else:
        x1 = num1
        x2 = num2

    return f'{s_birthday_text[2]}-{x1}-{x2}'


def create_periodic_task(task: str, params: list):
    """ function for create periodic task run """
    schedule, created = IntervalSchedule.objects.get_or_create(
        period=IntervalSchedule.HOURS,
        every=24
    )
    periodic_task = PeriodicTask.objects.create(
        interval=schedule,
        name='periodic_task_run',
        task=task,
        args=json.dumps(params)
    )

    return periodic_task


def delete_periodic_task(periodic_task_id):
    PeriodicTask.objects.filter(id=periodic_task_id).delete()
