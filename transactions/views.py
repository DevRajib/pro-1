from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect 
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal, InvalidOperation 
import json
import requests
from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import SMSData, UserProfile, UserStatus, MasterSMSData
from .serializers import SMSDataSerializer, UserProfileSerializer, UserStatusSerializer, MasterSMSDataSerializer

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile
from .serializers import UserProfileSerializer
# SMS API configuration
greenweburl = "https://api.bdbulksms.net/api.php"
token = "6985405a653273b170c4293dab4cbb3a"  # Replace with your actual token
sms_message = "You have been offline for more than 5 minutes."

class AuthenticateUser(APIView):
    def post(self, request):
        # Retrieve username and password from request data
        username = request.data.get('username')  # Correct way to access POST data
        password = request.data.get('password')  # Correct way to access POST data

        # Authenticate user
        user = authenticate(username=username, password=password)

        if user is not None:
            # If authentication is successful
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        else:
            # If authentication fails
            return Response({'status': 'failure', 'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
# Dashboard view with pagination and search functionality
def sms_dashboard(request):
    query = request.GET.get('q', '')

    # Filtering the SMS data based on query
    if query:
        sms_data_list = SMSData.objects.filter(
            Q(mobile_number__icontains=query) |
            Q(transaction_number__icontains=query) |
            Q(date_time__icontains=query) |
            Q(username__icontains=query) |
            Q(category__icontains=query) |
            Q(transaction_type__icontains=query)
        ).order_by('-id')
    else:
        sms_data_list = SMSData.objects.all().order_by('-id')

    # Paginator for handling large data sets
    paginator = Paginator(sms_data_list, 200)
    page_number = request.GET.get('page')
    sms_data = paginator.get_page(page_number)

    return render(request, 'dashboard.html', {'sms_data': sms_data, 'query': query})

# Class-based view to create SMS data
class SMSDataCreate(generics.CreateAPIView):
    queryset = SMSData.objects.all()
    serializer_class = SMSDataSerializer

    @transaction.atomic  # Ensure atomicity for database operations
    def perform_create(self, serializer):
        previous_entry = SMSData.objects.filter(
            username=serializer.validated_data.get('username')
        ).last()

        try:
            # Remove commas and convert current_amount and total_amount from TextField to Decimal
            current_amount = Decimal(serializer.validated_data['current_amount'].replace(',', ''))
            total_amount = Decimal(serializer.validated_data['total_amount'].replace(',', ''))
        except (InvalidOperation, ValueError) as e:
            # Raise validation error if conversion fails
            raise serializers.ValidationError(f"Invalid numeric value: {e}")

        if previous_entry:
            try:
                previous_total = Decimal(previous_entry.total_amount.replace(',', ''))
                expected_amount = previous_total + current_amount
                gap = total_amount - expected_amount
                serializer.save(gap=gap)
            except (InvalidOperation, ValueError) as e:
                # Raise validation error if conversion of previous entry fails
                raise serializers.ValidationError(f"Invalid numeric value in previous entry: {e}")
        else:
            serializer.save(gap=0)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View to update SMS data
def update_sms_data(request, sms_id):
    sms_data = get_object_or_404(SMSData, id=sms_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Update overpaid and note fields
            overpaid = data.get('overpaid')
            note = data.get('note')
            if overpaid is not None:
                sms_data.overpaid = overpaid
            if note is not None:
                sms_data.note = note

            sms_data.save()
            return JsonResponse({'status': 'success'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

# View to delete SMS data and move it to savings
def delete_sms_data(request, sms_id):
    sms_data = get_object_or_404(SMSData, id=sms_id)

    # Save the deleted data to savings or temporary storage
    try:
        # Move to a temporary storage or savings
        sms_data.status = 'Deleted'
        sms_data.save()  # This is where you modify the data instead of deleting it

        return JsonResponse({'status': 'success', 'message': 'SMS data moved to savings'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# View to restore SMS data from savings
def restore_sms_data(request, sms_id):
    sms_data = get_object_or_404(SMSData, id=sms_id, status='Deleted')

    if request.method == 'POST':
        try:
            # Restore from savings to active data
            sms_data.status = 'Active'
            sms_data.save()
            return JsonResponse({'status': 'success', 'message': 'SMS data restored'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

# Function to check user status and send notifications
def check_user_status():
    current_time = timezone.now()
    user_statuses = UserStatus.objects.all()

    for user_status in user_statuses:
        if not user_status.is_online:
            offline_duration = current_time - user_status.last_online_time

            if offline_duration > timedelta(minutes=5):
                user_mobile_number = user_status.user.mobile_number
                if user_mobile_number:
                    data = {
                        'token': token,
                        'to': user_mobile_number,
                        'message': sms_message
                    }
                    try:
                        response = requests.post(url=greenweburl, data=data)
                        if response.status_code == 200:
                            print(f"Notification sent to {user_mobile_number}.")
                        else:
                            print(f"Failed to send notification to {user_mobile_number}. Response: {response.text}")
                    except requests.RequestException as e:
                        print(f"Error sending notification: {e}")

# View for live status of users
def live_status(request):
    # Get the current time
    current_time = timezone.now()

    # Fetch all user statuses
    user_statuses = UserStatus.objects.all()

    # List to hold user details to be displayed
    users_info = []

    # Iterate over each user status and determine online/offline status
    for user_status in user_statuses:
        user_info = {
            'id': user_status.user.id,
            'username': user_status.user.username,
            'status': 'Online' if user_status.is_online else 'Offline',
            'offline_duration': None
        }

        # If the user is offline, calculate the offline duration
        if not user_status.is_online:
            offline_duration = current_time - user_status.last_online_time
            user_info['offline_duration'] = offline_duration

            # If the user has been offline for more than 5 minutes, send an SMS
            if offline_duration > timedelta(minutes=5):
                user_mobile_number = user_status.user.mobile_number
                if user_mobile_number:  # Ensure the mobile number is available
                    data = {
                        'token': token,
                        'to': user_mobile_number,
                        'message': sms_message
                    }
                    try:
                        # Send SMS via the bulk SMS API
                        response = requests.post(url=greenweburl, data=data)
                        if response.status_code == 200:
                            print(f"SMS sent successfully to {user_mobile_number}.")
                        else:
                            print(f"Failed to send SMS to {user_mobile_number}. Response: {response.text}")
                    except requests.RequestException as e:
                        print(f"Error sending SMS: {e}")

        # Append user info to the list
        users_info.append(user_info)

    # Render the live status page with user details
    return render(request, 'live_status.html', {'users_info': users_info})

# Class-based view to create and list UserProfile entries
class UserProfileListCreate(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def perform_create(self, serializer):
        if UserProfile.objects.filter(username=serializer.validated_data['username']).exists():
            raise serializers.ValidationError("Username already exists.")
        serializer.save()

# Class-based view to create and list UserStatus entries
class UserStatusListCreate(generics.ListCreateAPIView):
    queryset = UserStatus.objects.all()
    serializer_class = UserStatusSerializer

    def perform_create(self, serializer):
        # Check if the user is already in the database
        user = serializer.validated_data.get('user')
        existing_status = UserStatus.objects.filter(user=user).first()

        # Ensure that a user cannot have multiple statuses
        if existing_status:
            raise ValidationError(f"User {user.username} already has a status entry.")

        # Check if the user is trying to set the status to 'Offline' with a current online timestamp
        is_online = serializer.validated_data.get('is_online', True)
        if not is_online:
            # Ensure there is a valid 'last_online_time' for offline users
            last_online_time = serializer.validated_data.get('last_online_time')
            if not last_online_time:
                raise ValidationError("Last online time must be provided when setting a user status to offline.")

            # Verify that the last_online_time is not in the future
            if last_online_time > timezone.now():
                raise ValidationError("Last online time cannot be in the future.")

        # Save the user status if all checks pass
        serializer.save()

    def create(self, request, *args, **kwargs):
        # Overriding create method to add logging or other custom actions
        response = super().create(request, *args, **kwargs)
        user_status = response.data
        # Example: Log the creation of a user status or send a notification
        print(f"User status for {user_status['user']} created with status: {user_status['is_online']}")
        return response

# Advanced custom logic for MasterSMSDataListCreate
class MasterSMSDataListCreate(generics.ListCreateAPIView):
    queryset = MasterSMSData.objects.all()
    serializer_class = MasterSMSDataSerializer

    def perform_create(self, serializer):
        # Example: Implementing business logic to prevent duplicate transactions
        transaction_number = serializer.validated_data.get('transaction_number')

        # Ensure that each transaction number is unique in the master data
        if MasterSMSData.objects.filter(transaction_number=transaction_number).exists():
            raise ValidationError(f"Transaction number {transaction_number} already exists in master data.")

        # Implement logic to calculate or validate fields if necessary
        current_amount = serializer.validated_data.get('current_amount')
        total_amount = serializer.validated_data.get('total_amount')

        # Ensure amounts are valid decimals
        try:
            current_amount = Decimal(current_amount.replace(',', ''))
            total_amount = Decimal(total_amount.replace(',', ''))
        except (InvalidOperation, ValueError):
            raise ValidationError("Invalid numeric format for amounts.")

        # Validate business rules, e.g., current amount cannot exceed total amount
        if current_amount > total_amount:
            raise ValidationError("Current amount cannot exceed total amount.")

        # Ensure that necessary fields are not empty and conform to business rules
        if not serializer.validated_data.get('username'):
            raise ValidationError("Username must be provided.")

        # Perform the save after all checks
        serializer.save()

    def create(self, request, *args, **kwargs):
        # Custom response handling or additional processing
        response = super().create(request, *args, **kwargs)
        master_sms_data = response.data
        # Example: Log the creation or send a notification
        print(f"Master SMS data entry created with transaction number: {master_sms_data['transaction_number']}")
        return response