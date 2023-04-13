from django.db import models
from django.conf import settings


class Info(models.Model):
    """  """

    id = models.AutoField(primary_key=True, db_index=True)
    successful = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    task_limit = models.IntegerField(default=0)
    task_offset = models.IntegerField(default=0)
    periodic_task = models.IntegerField(default=0)
    status = models.CharField(max_length=15)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']


class Task(models.Model):
    """  """

    id = models.AutoField(primary_key=True, db_index=True)
    language = models.CharField(max_length=30)
    over_18 = models.CharField(max_length=3)
    smoker = models.CharField(max_length=3)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    birthday = models.CharField(max_length=30)
    email = models.CharField(max_length=255, db_index=True)
    phone_number = models.CharField(max_length=50, db_index=True)
    password = models.CharField(max_length=255)
    preference = models.CharField(max_length=100)
    referral_code = models.CharField(max_length=255, blank=True, null=True)
    only_registration = models.BooleanField()
    video_url = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=10, default=settings.LOAD_STATUS)
    message = models.TextField(blank=True, null=True, default=None)
    info = models.ForeignKey(Info, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']


class File(models.Model):
    """  """

    id = models.AutoField(primary_key=True, db_index=True)
    file = models.FileField(upload_to='accounts/')
    date_creation = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']


class Email(models.Model):
    """  """

    id = models.AutoField(primary_key=True, db_index=True)
    email = models.EmailField()
    date_creation = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.email