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

class RoleBasedPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CustomUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'name': user.first_name,
                    'email': user.email,
                    'profile_pic': user.profile_pic.url if user.profile_pic else None,
                    'job_role': user.role.role if user.role else None,
                    'mobile': user.contact_number,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user:
                token, created = Token.objects.get_or_create(user=user)
                if not serializer.validated_data.get('remember_me', True):
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)
                return Response({
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'name': user.first_name,
                        'email': user.email,
                        'profile_pic': user.profile_pic.url if user.profile_pic else None,
                        'job_role': user.role.role if user.role else None,
                        'mobile': user.contact_number,
                    }
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                reset_token = get_random_string(length=32)
                user.reset_token = reset_token
                user.reset_token_expiry = timezone.now() + timezone.timedelta(minutes=30)
                user.save()

                reset_link = f"http://yourdomain.com/reset-password/{reset_token}/"
                subject = 'Password Reset Request'
                message = f'Click the link to reset your password: {reset_link}'
                from_email = settings.EMAIL_HOST_USER
                send_mail(subject, message, from_email, [email], fail_silently=False)

                return Response({'redirect': '/check-email', 'email': email}, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                return Response({'error': 'Email not registered'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, token):
        try:
            user = CustomUser.objects.get(reset_token=token, reset_token_expiry__gt=timezone.now())
            serializer = ResetPasswordSerializer(data=request.data)
            if serializer.is_valid():
                user.set_password(serializer.validated_data['new_password'])
                user.reset_token = None
                user.reset_token_expiry = None
                user.save()
                return Response({'message': 'Password reset successful. Please log in.', 'redirect': '/login'}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = CustomUserDetailSerializer(request.user)
        logger.info(f"Profile retrieved for user: {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        password_data = {
            'password': data.pop('password', None),
            'confirm_password': data.pop('confirm_password', None)
        }

        serializer = ProfileUpdateSerializer(request.user, data=data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Profile updated for user: {request.user.email}, updated fields: {serializer.validated_data}")
            if password_data['password'] and password_data['confirm_password']:
                password_serializer = ProfileChangePasswordSerializer(data=password_data)
                if password_serializer.is_valid():
                    password_serializer.update(request.user, password_serializer.validated_data)
                    logger.info(f"Password updated for user: {request.user.email}")
                else:
                    logger.error(f"Password update failed for user: {request.user.email}, errors: {password_serializer.errors}")
                    return Response(password_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(CustomUserDetailSerializer(user).data, status=status.HTTP_200_OK)
        logger.error(f"Profile update failed for user: {request.user.email}, errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

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
                defaults={'check_in_times': [], 'total_hours': 0.0}
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
    permission_classes = [permissions.IsAuthenticated]

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

class DashboardTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(assigned_to=request.user).order_by('id')
        
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

        serializer = TaskDataSerializer(task_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DashboardAttendanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now()
        attendance_data = Attendance.objects.filter(user=request.user, date__year=today.year).values('date').annotate(
            month=ExtractMonth('date')
        ).values(
            'month'
        ).annotate(
            present=Count('id', filter=Q(total_hours__gt=0)),
            absent=Count('id', filter=Q(total_hours=0))
        ).order_by('month')

        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        date_data = [
            {
                'month': month_names.get(row['month'], 'Unknown'),
                'present': row['present'],
                'absent': row['absent']
            } for row in attendance_data
        ]

        for month in range(1, 13):
            month_name = month_names[month]
            if not any(d['month'] == month_name for d in date_data):
                date_data.append({'month': month_name, 'present': 0, 'absent': 0})

        date_data.sort(key=lambda x: list(month_names.values()).index(x['month']))

        serializer = DashboardAttendanceSerializer({'dateData': date_data})
        return Response(serializer.data, status=status.HTTP_200_OK)