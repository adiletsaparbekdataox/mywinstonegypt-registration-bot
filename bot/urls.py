from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (StartBotView, RunningStatusView, StopBotView, ReCaptchaBalanceView,
                    ContinueBotTaskView, InfoListView, DeleteInfoView, GetTaskView)

urlpatterns = [
    path('start/', StartBotView.as_view()),
    path('stop/', StopBotView.as_view()),
    path('continue/', ContinueBotTaskView.as_view()),
    path('info/', InfoListView.as_view()),
    path('delete-info/<int:pk>/', DeleteInfoView.as_view()),
    path('tasks/<int:pk>/', GetTaskView.as_view()),
    path('recaptcha-balance/', ReCaptchaBalanceView.as_view()),
    path('running-status/', RunningStatusView.as_view())
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)