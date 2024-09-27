from django.urls import path
from .views import (
    sms_dashboard,
    SMSDataCreate,
    update_sms_data,
    delete_sms_data,
    restore_sms_data,
    UserProfileListCreate,
    UserStatusListCreate,
    MasterSMSDataListCreate,
    live_status,
    AuthenticateUser,
)

urlpatterns = [
    path('', sms_dashboard, name='sms_dashboard'),
    path('create_sms/', SMSDataCreate.as_view(), name='create_sms'),
    path('update_sms_data/<int:sms_id>/', update_sms_data, name='update_sms_data'),
    path('delete_sms_data/<int:sms_id>/', delete_sms_data, name='delete_sms_data'),
    path('restore_sms_data/<int:sms_id>/', restore_sms_data, name='restore_sms_data'),
    path('user_profiles/', UserProfileListCreate.as_view(), name='user_profiles'),
    path('user_statuses/', UserStatusListCreate.as_view(), name='user_statuses'),
    path('master_sms_data/', MasterSMSDataListCreate.as_view(), name='master_sms_data'),
    path('live/', live_status, name='live_status'),  # Correct URL pattern for live status
    path('userprofile/', AuthenticateUser.as_view(), name='userprofile_create_unique'),
]
