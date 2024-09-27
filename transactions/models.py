from django.db import models
from django.contrib.auth.models import User

class SMSData(models.Model):
    username = models.CharField(max_length=255)
    user_reference = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=15)
    transaction_number = models.CharField(max_length=255, unique=True)
    transaction_type = models.CharField(max_length=50)
    current_amount = models.CharField(max_length=255)
    total_amount = models.CharField(max_length=255)
    date_time = models.TextField()
    comment = models.TextField()
    overpaid = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    gap = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.username} - {self.transaction_number}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    password=models.TextField(unique=True,max_length=30)
    mobile_number = models.CharField(max_length=15)

    

class UserStatus(models.Model):
    username = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default='Online')
    last_seen = models.DateTimeField(auto_now=True)

class MasterSMSData(models.Model):
    sender = models.CharField(max_length=255)
    message = models.TextField()
    received_time = models.TextField()   

