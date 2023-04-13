import os
import csv
import time
import random
import logging

from django.conf import settings
from django.db.models import F
from django.template.loader import render_to_string
from django.core.mail import send_mail

from celery import shared_task

from server.celery import app
from .utils import create_periodic_task, delete_periodic_task
from .models import Info, Task, File, Email
from .bot import Bot

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {'ENGLISH': 'en', 'ARABIC': 'ar'}


@app.task
def account_distributor(only_registration, video_url, tasks_per_day):
    info = Info.objects.create(task_limit=tasks_per_day)
    file_path = File.objects.first().file
    bulk_accounts = []

    with open(os.path.join(settings.MEDIA_ROOT, str(file_path)), newline='',
              encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row['LANGUAGE'] == '' or row['EMAIL'] == '' or row['FIRSTNAME'] == '' or \
                    row['LAST NAME'] == '' or row['DATE OF BIRTH'] == '' or \
                    row['MOBILE NUMBER'] == '' or row['PASSWORD'] == '':
                continue

            if not row['MOBILE NUMBER'].isdigit():
                continue

            language = LANGUAGE_MAP[row['LANGUAGE']]

            bulk_accounts.append(
                Task(
                    language=language,
                    over_18=row['OVER 18'].lower(),
                    smoker=row['SMOKER'].lower(),
                    firstname=row['FIRSTNAME'],
                    lastname=row['LAST NAME'],
                    birthday=row['DATE OF BIRTH'],
                    email=row['EMAIL'],
                    phone_number=row['MOBILE NUMBER'],
                    password=row['PASSWORD'],
                    preference=row['SMOKING PREFERENCE'].lower(),
                    referral_code=row['REFERRAL CODE'],
                    only_registration=only_registration,
                    video_url=video_url,
                    info=info,
                )
            )

    saved_accounts = Task.objects.bulk_create(bulk_accounts)

    last_task = Task.objects.last()

    periodic_task = create_periodic_task(
        task='bot.tasks.auto_run', params=[info.id, tasks_per_day, last_task.id]
    )

    tasks = list(Task.objects.filter(info_id=info.id)[0:tasks_per_day])

    info.total = len(saved_accounts)
    info.periodic_task = periodic_task.id
    info.status = settings.WORKING_STATUS
    info.save()

    for task in tasks:
        if task == tasks[-1]:
            run_task.delay(task.id, last_task.id, True)
        else:
            run_task.delay(task.id)


@shared_task
def auto_run(info_id, tasks_per_day, last_task_id):
    info = Info.objects.get(id=info_id)

    offset = info.task_offset + tasks_per_day
    limit = info.task_limit + tasks_per_day

    limit_tasks = list(Task.objects.filter(info_id=info.id)[offset:limit])

    if not limit_tasks:
        logger.error('Limit tasks does not exist!')
        return

    if limit_tasks[0].status == settings.STOPPED_STATUS:
        logger.info('Scheduler: tasks is stopped')
        return

    info.task_offset = F('task_offset') + tasks_per_day
    info.task_limit = F('task_limit') + tasks_per_day
    info.save()

    for task in limit_tasks:
        if task == limit_tasks[-1]:
            run_task.delay(task.id, last_task_id, True)
        else:
            run_task.delay(task.id)


@app.task
def run_task(task_id, last_task_id: int = None, last_id: bool = False):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        logger.error('Task does not exist [run_task:1]')
        return

    if task.status == settings.ERROR_STATUS:
        return

    task.status = 'working'
    task.save()

    # random delay for bot
    random_delay = random.randint(30, 300)
    logger.info(f'Bot sleep {random_delay} seconds')
    time.sleep(random_delay)

    bot = Bot(
        language=task.language,
        over_18=task.over_18,
        smoker=task.smoker,
        firstname=task.firstname,
        lastname=task.lastname,
        birthday=task.birthday,
        email=task.email,
        phone_number=task.phone_number,
        password=task.password,
        preference=task.preference,
        referral_code=task.referral_code,
        only_registration=task.only_registration,
        video_url=task.video_url,
        proxy=settings.PROXY
    )

    response = bot.main()

    task.status = response['status']
    task.message = response['message']
    task.phone_number = response['phone_number']
    task.birthday = response['birthday']
    task.video_url = response['video_url']
    task.save()

    info = Info.objects.get(id=task.info_id)

    if response['status'] == settings.SUCCESS_STATUS:
        info.successful = F('successful') + 1

    if response['status'] == settings.ERROR_STATUS:
        info.failed = F('failed') + 1

    info.save()

    if last_id:
        logger.info('Sleep')
        if settings.DEBUG:
            time.sleep(5)
        else:
            time.sleep(120)

        info = Info.objects.get(id=task.info_id)

        logger.info(f'task_id: {task_id}, last_task_id: {last_task_id}')

        if last_task_id:
            if int(task_id) == int(last_task_id):
                delete_periodic_task(info.periodic_task)

                info.status = settings.SUCCESS_STATUS
                info.save()

        params = {
            'successful': info.successful,
            'failed': info.failed,
            'total': info.total,
            'sum': info.failed + info.successful
        }

        emails = [e.email for e in Email.objects.all()]

        email_verification_html = 'bot/fin_email_notification.html'
        subject = 'Bots notification'
        message = render_to_string(email_verification_html, params)
        send_mail(
            subject=subject,
            message=message,
            recipient_list=emails,
            from_email=''
        )
