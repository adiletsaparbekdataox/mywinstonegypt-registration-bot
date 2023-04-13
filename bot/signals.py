from django.dispatch import receiver
from django.db.models.signals import pre_save

from .models import File


@receiver(pre_save, sender=File)
def post_save_user(**kwargs):
    File.objects.all().delete()
