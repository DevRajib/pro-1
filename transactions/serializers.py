from rest_framework import serializers
from .models import SMSData, UserProfile, UserStatus, MasterSMSData

class SMSDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSData
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStatus
        fields = '__all__'

class MasterSMSDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterSMSData
        fields = '__all__'
