from django.contrib import admin
from .models import SMSData, UserProfile, UserStatus, MasterSMSData
from .models import UserStatus

@admin.register(SMSData)
class SMSDataAdmin(admin.ModelAdmin):
    list_display = ('username', 'user_reference', 'category', 'mobile_number', 'transaction_number', 'transaction_type', 'current_amount', 'total_amount', 'date_time', 'status')
    search_fields = ('username', 'mobile_number', 'transaction_number', 'category')
    list_filter = ('category', 'transaction_type', 'status', 'date_time')
    ordering = ('-date_time',)
    readonly_fields = ('date_time',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'password')  # Ensure these fields are present in the model
    search_fields = ('user__username', 'mobile_number')  # Optionally add search fields
    readonly_fields = ('password',) 



@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ('username', 'status', 'last_seen')  # Ensure these fields are present in the model
    search_fields = ('username', 'status')  # Optionally add search fields


@admin.register(MasterSMSData)
class MasterSMSDataAdmin(admin.ModelAdmin):
    list_display = ('sender', 'message', 'received_time')
    search_fields = ('sender', 'message')
    list_filter = ('received_time',)
    ordering = ('-received_time',)
