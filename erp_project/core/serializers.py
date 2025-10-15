from rest_framework import serializers
from .models import Candidate, CandidateDocument, Attendance, GovernmentHoliday, Task
from masters.models import Department, Role, Branch, CustomUser
import re
import logging

logger = logging.getLogger(__name__)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(default=True, required=False)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")
        
        return data

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

class ProfileChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance

class CandidateDocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = CandidateDocument
        fields = ['id', 'file', 'uploaded_at']

class CandidateSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=False)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False)
    designation = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False)
    upload_documents = CandidateDocumentSerializer(many=True, required=False)

    class Meta:
        model = Candidate
        fields = [
            'employee_code', 'first_name', 'last_name', 'department', 'branch', 'designation',
            'gender', 'joining_date', 'personal_number', 'emergency_contact_number', 'email',
            'aadhar_number', 'pan_number', 'status', 'current_address', 'highest_qualification',
            'previous_employer', 'total_experience_year', 'total_experience_month',
            'relevant_experience_year', 'relevant_experience_month', 'marital_status',
            'basics', 'hra', 'conveyance_allowance', 'medical_allowance', 'other_allowances',
            'bonus', 'taxes', 'pf', 'esi', 'gross_salary', 'net_salary', 'uan_number',
            'pf_number', 'bank_name', 'account_number', 'ifsc_code', 'asset', 'asset_type',
            'laptop_company_name', 'asset_id', 'upload_documents'
        ]
        depth = 1

    def validate_personal_number(self, value):
        if not value:
            raise serializers.ValidationError("Personal number is required.")
        if not re.match(r'^[0-9+\-\s]+$', value):
            raise serializers.ValidationError("Personal number must contain only digits, +, -, or spaces.")
        return value

    def validate_emergency_contact_number(self, value):
        if value and not re.match(r'^[0-9+\-\s]+$', value):
            raise serializers.ValidationError("Emergency contact number must contain only digits, +, -, or spaces.")
        return value

    def validate_aadhar_number(self, value):
        if not value:
            raise serializers.ValidationError("Aadhar number is required.")
        if not re.match(r'^\d{4}\s?\d{4}\s?\d{4}$', value):
            raise serializers.ValidationError("Aadhar number must be 12 digits, optionally with spaces.")
        return value

    def validate_pan_number(self, value):
        if not value:
            raise serializers.ValidationError("PAN number is required.")
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', value):
            raise serializers.ValidationError("PAN number must be 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F).")
        return value

    def validate_account_number(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Account number must contain only digits.")
        return value

    def validate(self, data):
        bank_fields = ['bank_name', 'account_number', 'ifsc_code']
        provided = [field in data and data[field] for field in bank_fields]
        if any(provided) and not all(provided):
            raise serializers.ValidationError("Bank name, account number, and IFSC code must all be provided or none.")

        asset = data.get('asset', self.instance.asset if self.instance else None)
        if asset == 'Y':
            if not data.get('asset_type'):
                raise serializers.ValidationError("Asset type is required when asset is Yes.")
            if data.get('asset_type') == 'laptop' and not data.get('laptop_company_name'):
                raise serializers.ValidationError("Laptop company name is required when asset type is laptop.")

        logger.info("Validated serializer data: %s", data)
        return data

    def create(self, validated_data):
        upload_documents_data = validated_data.pop('upload_documents', [])
        candidate = super().create(validated_data)
        for document_data in upload_documents_data:
            CandidateDocument.objects.create(candidate=candidate, **document_data)
        return candidate

    def update(self, instance, validated_data):
        upload_documents_data = validated_data.pop('upload_documents', [])
        instance = super().update(instance, validated_data)
        if upload_documents_data:
            instance.upload_documents.all().delete()
            for document_data in upload_documents_data:
                CandidateDocument.objects.create(candidate=instance, **document_data)
        return instance

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'date', 'check_in_times', 'total_hours']

class CheckInOutSerializer(serializers.Serializer):
    date = serializers.DateField()
    is_check_in = serializers.BooleanField()

class GovernmentHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentHoliday
        fields = ['date', 'description']

class TaskSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = Task
        fields = ['id', 'name', 'status', 'start_date', 'due_date', 'assigned_to', 'priority']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['assigned_to'] = {
            'id': instance.assigned_to.id,
            'name': instance.assigned_to.first_name
        }
        return data

class TaskSummarySerializer(serializers.Serializer):
    not_started = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    completed = serializers.IntegerField()
    awaiting_feedback = serializers.IntegerField()

class TaskDataSerializer(serializers.Serializer):
    taskData = TaskSerializer(many=True)
    taskSummary = TaskSummarySerializer()

class DashboardAttendanceSerializer(serializers.Serializer):
    dateData = serializers.ListField(child=serializers.DictField())