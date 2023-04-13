from django.conf import settings
from django_celery_beat.models import PeriodicTask
from django.db.models import Q

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from server.celery import app
from .models import Info, Task
from .services import ReCaptchaService
from .serializers import FileSerializer, TaskSerializer, InfoSerializer
from .tasks import account_distributor, run_task
from .utils import delete_periodic_task


class StartBotView(APIView):
    """ view for create start task with params """

    BOOL_CONVERTER = {'true': True, 'false': False}

    def post(self, request):

        working_tasks = Info.objects.filter(
            Q(status=settings.WORKING_STATUS) | Q(status=settings.STOPPED_STATUS)
        )
        if working_tasks:
            return Response({'message': 'Bots are already processing tasks or stopped'}, status=400)

        file = request.data.get('file')
        if not file:
            return Response({'message': 'Required field [file]'})

        only_registration = request.data.get('only_registration')
        if not only_registration:
            return Response({'message': 'Required field [only_registration]'})

        tasks_per_day = request.data.get('tasks_per_day')
        if not tasks_per_day:
            return Response({'message': 'Required field [tasks_per_day]'})

        if int(tasks_per_day) > settings.LIMIT_TASKS_PER_DAY:
            return Response({'message': f'Max tasks per day: {settings.LIMIT_TASKS_PER_DAY}'},
                            status=400)

        video_url = request.data.get('video_url')

        serializer = FileSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            account_distributor.delay(
                only_registration=self.BOOL_CONVERTER[only_registration],
                video_url=video_url,
                tasks_per_day=int(tasks_per_day)
            )

            return Response({'message': 'Bots successfully started'}, status=200)
        return Response({'message': 'Error bots start'}, status=400)


class StopBotView(APIView):
    """  """

    @staticmethod
    def post(request):
        with app.connection_for_write() as connection:
            connection.default_channel.queue_purge('celery')
        info = Info.objects.order_by('-id').first()
        if not info:
            return Response({'message': 'Info table does not exist'}, status=400)
        info.status = settings.STOPPED_STATUS
        info.save()
        return Response({'message': 'Tasks successfully stopped, bots started to stop'})


class TasksView(ListAPIView):
    """ view for return tasks log """

    pagination_class = PageNumberPagination

    def list(self, request, pk, *args, **kwargs):
        queryset = Task.objects.filter(info_id=pk).order_by('id')
        serializer = TaskSerializer(queryset, many=True)
        page = self.paginate_queryset(serializer.data)
        return self.get_paginated_response(page)


class ContinueBotTaskView(APIView):
    """ View for continue stopped bot tasks """

    @staticmethod
    def post(request):

        info = Info.objects.order_by('-id').first()
        tasks = Task.objects.filter(info_id=info.id)[info.task_offset:info.task_limit]
        info.status = settings.WORKING_STATUS
        info.save()
        last_task = Task.objects.last()

        for task in tasks:
            if task == tasks[-1]:
                run_task.delay(task.id, last_task.id, True)
            else:
                run_task.delay(task.id)

        return Response({'message': 'Tasks successfully resumed, bots start working'}, status=200)


class ReCaptchaBalanceView(APIView):
    """ View for get recaptcha service balance """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.recaptcha = ReCaptchaService()

    def get(self, request):
        recaptcha_balance = self.recaptcha.balance()
        return Response({'balance': recaptcha_balance}, status=200)


class InfoListView(ListAPIView):
    """ Tasks info """
    serializer_class = InfoSerializer
    queryset = Info.objects.all()


class DeleteInfoView(APIView):
    """ view for delete task global info """

    @staticmethod
    def delete(request, pk):
        try:
            info = Info.objects.get(id=pk)
        except Info.DoesNotExist:
            return Response({'message': 'Invalid info pk'}, status=400)

        if info.status == settings.WORKING_STATUS:
            return Response({'message': 'Bots is running, stop the bots first'}, status=400)

        info.delete()
        delete_periodic_task(info.periodic_task)

        return Response({'message': 'Column successfully deleted'}, status=200)


class GetTaskView(ListAPIView):
    """  """

    pagination_class = PageNumberPagination

    def get(self, request, pk, *args, **kwargs):
        queryset = Task.objects.filter(info_id=pk).order_by('id')
        serializer = TaskSerializer(queryset, many=True)
        page = self.paginate_queryset(serializer.data)
        return self.get_paginated_response(page)


class RunningStatusView(APIView):
    """ view for return running status """

    @staticmethod
    def get(request):
        info = Info.objects.order_by('-id').first()
        if not info:
            return Response({'message': 'Info table does not exist'}, status=400)

        return Response({'bots_status': info.status})
