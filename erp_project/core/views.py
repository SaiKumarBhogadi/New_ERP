from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.db.models import Count, Q
from django.utils import timezone
from django.db.models.functions import ExtractMonth
from .models import Candidate, CandidateDocument, Attendance, GovernmentHoliday, Task
from .serializers import CandidateSerializer, AttendanceSerializer, CheckInOutSerializer, GovernmentHolidaySerializer, TaskSerializer, TaskSummarySerializer, TaskDataSerializer, DashboardAttendanceSerializer, LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer, ProfileChangePasswordSerializer,ProfileUpdateSerializer
import logging
from masters.models import CustomUser
from masters.serializers import CustomUserDetailSerializer,CustomUserCreateSerializer, CustomUserUpdateSerializer
import os
import uuid
from django.core.files.storage import default_storage
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)

# core/views.py (auth-related views only - add to your existing file)

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import logging

from masters.models import CustomUser
from masters.serializers import CustomUserDetailSerializer
from .serializers import (
    LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    ProfileUpdateSerializer, ProfileChangePasswordSerializer
)
from core.permissions import RoleBasedPermission

logger = logging.getLogger(__name__)


class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token, _ = Token.objects.get_or_create(user=user)

        # Handle remember_me
        if not serializer.validated_data.get('remember_me', True):
            request.session.set_expiry(0)  # session ends on browser close
        else:
            request.session.set_expiry(1209600)  # 2 weeks

        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'profile_pic': user.profile_pic.url if user.profile_pic else None,
                'job_role': user.role.role if user.role else None,
                'mobile': user.contact_number,
            }
        }, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()  # delete token
        request.session.flush()           # clear session
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


class ForgotPasswordView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email, is_active=True)
        except CustomUser.DoesNotExist:
            return Response({"detail": "No active user found with this email."}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = get_random_string(length=32)
        user.reset_token = reset_token
        user.reset_token_expiry = timezone.now() + timezone.timedelta(hours=1)
        user.save()

        reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{reset_token}"

        context = {
            'user': user,
            'reset_link': reset_link,
            'expiry_hours': 1,
            'site_name': 'Stackly ERP',
        }

        subject = 'Stackly ERP - Password Reset Request'
        html_message = render_to_string('emails/forgot_password.html', context)

        email_msg = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_msg.content_subtype = 'html'

        try:
            email_msg.send(fail_silently=False)
            logger.info(f"Password reset email sent to {email}")
            return Response({"detail": "Password reset link has been sent to your email."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to send reset email to {email}: {str(e)}")
            return Response({"detail": "Failed to send reset email. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request, token):
        try:
            user = CustomUser.objects.get(
                reset_token=token,
                reset_token_expiry__gt=timezone.now()
            )
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid or expired reset token"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data['new_password'])
        user.reset_token = None
        user.reset_token_expiry = None
        user.save()

        return Response({"message": "Password reset successful. Please log in."}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    serializer_class = CustomUserDetailSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProfileUpdateSerializer
        return CustomUserDetailSerializer

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        # Handle profile update
        profile_serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        # Handle password change (if provided)
        if 'current_password' in request.data:
            password_serializer = ProfileChangePasswordSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            password_serializer.is_valid(raise_exception=True)
            password_serializer.save()  # ← NO (user) here — just save()

        return Response(CustomUserDetailSerializer(user).data, status=status.HTTP_200_OK)


class OnboardingListView(APIView):
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    def get(self, request, format=None):
        try:
            candidates = Candidate.objects.select_related('department', 'branch', 'designation').all()
            serializer = CandidateSerializer(candidates, many=True)
            logger.info("Fetched %d candidates", candidates.count())
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error fetching candidates: %s", str(e))
            return Response(
                {"error": "Failed to fetch candidates"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        logger.info("Received POST request with data keys: %s", list(request.data.keys()))
        logger.info("Received FILES: %s", list(request.FILES.keys()))

        upload_documents = request.FILES.getlist('upload_documents')
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data

        documents_data = []
        for file in upload_documents:
            file_name, file_ext = os.path.splitext(file.name)
            unique_name = f"{file_name}_{uuid.uuid4().hex[:8]}{file_ext}"
            save_path = os.path.join('candidate_documents', unique_name)
            saved_path = default_storage.save(save_path, file)
            documents_data.append({'file': saved_path})

        data['upload_documents'] = documents_data
        serializer = CandidateSerializer(data=data)
        if serializer.is_valid():
            candidate = serializer.save()
            logger.info("Candidate saved successfully with %d documents", len(candidate.upload_documents.all()))
            return Response(
                {'message': 'Data submitted successfully', 'data': CandidateSerializer(candidate).data},
                status=status.HTTP_201_CREATED
            )
        logger.error("Serializer errors: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OnboardingDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated , RoleBasedPermission]

    def get(self, request, pk):
        try:
            candidate = Candidate.objects.select_related('department', 'branch', 'designation').get(pk=pk)
            serializer = CandidateSerializer(candidate)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Candidate.DoesNotExist:
            return Response({'error': 'Candidate not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can edit candidates'}, status=status.HTTP_403_FORBIDDEN)
        try:
            candidate = Candidate.objects.get(pk=pk)
            upload_documents = request.FILES.getlist('upload_documents')
            data = request.data.dict() if hasattr(request.data, 'dict') else request.data

            documents_data = []
            for file in upload_documents:
                file_name, file_ext = os.path.splitext(file.name)
                unique_name = f"{file_name}_{uuid.uuid4().hex[:8]}{file_ext}"
                save_path = os.path.join('Candidate_documents', unique_name)
                saved_path = default_storage.save(save_path, file)
                documents_data.append({'file': saved_path})

            data['upload_documents'] = documents_data
            serializer = CandidateSerializer(candidate, data=data, partial=True)
            if serializer.is_valid():
                candidate = serializer.save()
                logger.info("Candidate updated with %d documents", len(candidate.upload_documents.all()))
                return Response(CandidateSerializer(candidate).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Candidate.DoesNotExist:
            return Response({'error': 'Candidate not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete candidates'}, status=status.HTTP_403_FORBIDDEN)
        try:
            candidate = Candidate.objects.get(pk=pk)
            candidate.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Candidate.DoesNotExist:
            return Response({'error': 'Candidate not found'}, status=status.HTTP_404_NOT_FOUND)

class AttendanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        attendance_data = Attendance.objects.filter(user=user).order_by('date')
        serializer = AttendanceSerializer(attendance_data, many=True)
        return Response(serializer.data)

class CheckInOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = CheckInOutSerializer(data=request.data)
        if serializer.is_valid():
            date = serializer.validated_data['date']
            is_check_in = serializer.validated_data['is_check_in']
            current_date = timezone.now().date()

            if date < current_date:
                return Response({"error": "Cannot check-in/out for past dates"}, status=status.HTTP_400_BAD_REQUEST)
            if date > current_date:
                return Response({"error": "Cannot check-in/out for future dates"}, status=status.HTTP_400_BAD_REQUEST)

            attendance, created = Attendance.objects.get_or_create(
                user=user,
                date=date,
                defaults={'check_in_times': [], 'total_hours': 0.0, 'status': 'Present'}
            )

            check_in_times = attendance.check_in_times
            now = timezone.now().isoformat()

            if is_check_in:
                if len(check_in_times) % 2 == 0:
                    check_in_times.append(now)
                else:
                    return Response({"error": "Already checked in. Check out first."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if len(check_in_times) % 2 == 1:
                    check_in_times.append(now)
                else:
                    return Response({"error": "Not checked in yet."}, status=status.HTTP_400_BAD_REQUEST)

            total_hours = 0.0
            times = [timezone.datetime.fromisoformat(t) for t in check_in_times]
            for i in range(0, len(times) - 1, 2):
                if i + 1 < len(times):
                    total_hours += (times[i + 1] - times[i]).total_seconds() / 3600

            attendance.check_in_times = check_in_times
            attendance.total_hours = round(total_hours, 2)
            attendance.status = "Present" if total_hours > 7 else "Absent"
            attendance.save()

            serializer = AttendanceSerializer(attendance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GovernmentHolidayView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        holidays = GovernmentHoliday.objects.all()
        serializer = GovernmentHolidaySerializer(holidays, many=True)
        return Response(serializer.data)

class TaskListView(APIView):
    permission_classes = [permissions.IsAuthenticated ]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        tasks = Task.objects.filter(assigned_to=request.user).order_by('due_date')
        paginator = Paginator(tasks, per_page)
        page_obj = paginator.get_page(page)
        serializer = TaskSerializer(page_obj, many=True)
        return Response({
            'tasks': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': tasks.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(assigned_to=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TaskDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk, assigned_to=request.user)
            serializer = TaskSerializer(task)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            task = Task.objects.get(pk=pk, assigned_to=request.user)
            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            task = Task.objects.get(pk=pk, assigned_to=request.user)
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

class TaskSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(assigned_to=request.user)
        summary = {
            'not_started': tasks.filter(status='Not Started').count(),
            'in_progress': tasks.filter(status='In Progress').count(),
            'completed': tasks.filter(status='Completed').count(),
            'awaiting_feedback': tasks.filter(status='Awaiting Feedback').count(),
        }
        return Response(summary, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth
from django.utils import timezone

class DashboardCombinedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # -------- TASK DATA --------
        tasks = Task.objects.filter(assigned_to=user).order_by('id')

        task_summary = {
            'not_started': tasks.filter(status='Not Started').count(),
            'in_progress': tasks.filter(status='In Progress').count(),
            'completed': tasks.filter(status='Completed').count(),
            'awaiting_feedback': tasks.filter(status='Awaiting Feedback').count(),
        }

        task_data = {
            'taskData': TaskSerializer(tasks, many=True).data,
            'taskSummary': task_summary,
        }

        # -------- ATTENDANCE DATA --------
        today = timezone.now()

        attendance_data = Attendance.objects.filter(
            user=user,
            date__year=today.year
        ).values('date').annotate(
            month=ExtractMonth('date')
        ).values('month').annotate(
            present=Count('id', filter=Q(total_hours__gt=0)),
            absent=Count('id', filter=Q(total_hours=0))
        ).order_by('month')

        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }

        attendance_list = [
            {
                'month': month_names.get(row['month'], 'Unknown'),
                'present': row['present'],
                'absent': row['absent']
            }
            for row in attendance_data
        ]

        for month in range(1, 13):
            month_name = month_names[month]
            if not any(d['month'] == month_name for d in attendance_list):
                attendance_list.append({
                    'month': month_name,
                    'present': 0,
                    'absent': 0
                })

        attendance_list.sort(key=lambda x: list(month_names.values()).index(x['month']))

        # -------- RETURN MERGED DATA --------
        return Response(
            {
                "tasks": task_data,
                "attendance": attendance_list
            },
            status=status.HTTP_200_OK
        )
