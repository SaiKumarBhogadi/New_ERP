from django.db import models
from django.utils import timezone
import re
from django.contrib.auth.models import AbstractUser
from django.db.models import JSONField


class CandidateDocument(models.Model):
    file = models.FileField(upload_to='Candidate_documents/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CandidateDocument - {self.file.name}"

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"

class Candidate(models.Model):
    employee_code = models.CharField(max_length=10, unique=True, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    department = models.ForeignKey('masters.Department', on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey('masters.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey('masters.Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='candidate_designations')
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    joining_date = models.DateField(null=True, blank=True)
    personal_number = models.CharField(max_length=15)
    emergency_contact_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(unique=True)
    aadhar_number = models.CharField(max_length=14)
    pan_number = models.CharField(max_length=10)
    status = models.CharField(max_length=10, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')
    current_address = models.TextField(blank=True)
    highest_qualification = models.CharField(max_length=200, blank=True)
    previous_employer = models.CharField(max_length=200, blank=True)
    total_experience_year = models.PositiveIntegerField(null=True, blank=True)
    total_experience_month = models.PositiveIntegerField(null=True, blank=True)
    relevant_experience_year = models.PositiveIntegerField(null=True, blank=True)
    relevant_experience_month = models.PositiveIntegerField(null=True, blank=True)
    marital_status = models.CharField(max_length=20, choices=[('Married', 'Married'), ('Unmarried', 'Unmarried')], blank=True)
    basics = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hra = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    conveyance_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    esi = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    uan_number = models.CharField(max_length=12, blank=True)
    pf_number = models.CharField(max_length=12, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    asset = models.CharField(max_length=3, choices=[('Y', 'Yes'), ('N', 'No')], blank=True)
    asset_type = models.CharField(max_length=50, choices=[('laptop', 'Laptop'), ('phone', 'Phone')], blank=True)
    laptop_company_name = models.CharField(max_length=50, choices=[('HP', 'HP'), ('Dell', 'Dell'), ('Lenovo', 'Lenovo')], blank=True)
    asset_id = models.CharField(max_length=20, blank=True)
    upload_documents = models.ManyToManyField(CandidateDocument, blank=True)

    def save(self, *args, **kwargs):
        if not self.employee_code:
            last_candidate = Candidate.objects.order_by('id').last()
            if last_candidate:
                last_num = int(last_candidate.employee_code.replace('STA', ''))
                new_num = last_num + 1
            else:
                new_num = 1
            self.employee_code = f'STA{new_num:04d}'

        phone_regex = r'^[0-9+\-\s]+$'
        if self.personal_number and not re.match(phone_regex, self.personal_number):
            raise ValueError("Personal number must contain only digits, +, -, or spaces.")
        if self.emergency_contact_number and not re.match(phone_regex, self.emergency_contact_number):
            raise ValueError("Emergency contact number must contain only digits, +, -, or spaces.")

        aadhar_regex = r'^\d{4}\s?\d{4}\s?\d{4}$'
        if not re.match(aadhar_regex, self.aadhar_number):
            raise ValueError("Aadhar number must be 12 digits, optionally with spaces.")

        pan_regex = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pan_regex, self.pan_number):
            raise ValueError("PAN number must be 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F).")

        if self.account_number and not self.account_number.isdigit():
            raise ValueError("Account number must contain only digits.")

        if self.asset == 'Y' and not self.asset_type:
            raise ValueError("Asset type is required when asset is Yes.")
        if self.asset_type == 'laptop' and not self.laptop_company_name:
            raise ValueError("Laptop company name is required when asset type is laptop.")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_code} - {self.first_name} {self.last_name}"

class GovernmentHoliday(models.Model):
    date = models.DateField(unique=True)
    description = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.date} - {self.description}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Weekend', 'Weekend'),
        ('Holiday', 'Holiday'),
    ]
    user = models.ForeignKey('masters.CustomUser', on_delete=models.CASCADE)
    date = models.DateField()
    check_in_times = JSONField(default=list)  # Array of check-in/check-out timestamps
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.status} ({self.total_hours} hrs)"

class Task(models.Model):
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=[
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Awaiting Feedback', 'Awaiting Feedback')
    ])
    start_date = models.DateField()
    due_date = models.DateField()
    assigned_to = models.ForeignKey('masters.CustomUser', on_delete=models.CASCADE, related_name='tasks_assigned')
    priority = models.CharField(max_length=20, choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name