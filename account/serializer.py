from django.urls import reverse
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from account.models import StudentAccount

class StudentAccountSerializer(ModelSerializer):
    class Meta:
        model = StudentAccount
        fields = "__all__"