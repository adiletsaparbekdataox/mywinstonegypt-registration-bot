from rest_framework import serializers

from .models import File, Info, Task


class InfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Info
        fields = ['id', 'successful', 'failed', 'total', 'date_creation']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'language', 'over_18', 'smoker', 'firstname', 'lastname', 'birthday',
                  'email', 'phone_number', 'password', 'preference', 'referral_code',
                  'only_registration', 'video_url', 'status', 'message', 'date_creation']


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'
