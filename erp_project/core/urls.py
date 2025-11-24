from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('onboarding/', views.OnboardingListView.as_view(), name='onboarding-list'),
    path('onboarding/<int:pk>/', views.OnboardingDetailView.as_view(), name='onboarding-detail'),
    path('attendance/', views.AttendanceView.as_view(), name='attendance'),
    path('attendance/check-in-out/', views.CheckInOutView.as_view(), name='check-in-out'),
    path('attendance/holidays/', views.GovernmentHolidayView.as_view(), name='holidays'),
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('task-summary/', views.TaskSummaryView.as_view(), name='task-summary'),
    path("dashboard/", views.DashboardCombinedView.as_view(), name="dashboard-all"),

    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<str:token>/', views.ResetPasswordView.as_view(), name='reset-password'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)