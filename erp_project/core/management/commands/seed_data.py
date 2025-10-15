from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Branch, Department, Role, Profile
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with initial data (branches, departments, roles, users)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        # Clear existing data (optional, comment out if you don't want to clear)
        Profile.objects.all().delete()
        User.objects.all().delete()
        Role.objects.all().delete()
        Department.objects.all().delete()
        Branch.objects.all().delete()

        # Create Branches
        branch1 = Branch.objects.create(name="Chennai - Main")
        branch2 = Branch.objects.create(name="Mumbai - Central")
        self.stdout.write(self.style.SUCCESS(f'Created branches: {branch1}, {branch2}'))

        # Create Departments
        dept1 = Department.objects.create(
            code="#IT001",
            name="Information Technology",
            branch=branch1,
            description="Handles IT infrastructure and software development."
        )
        dept2 = Department.objects.create(
            code="#HR002",
            name="Human Resources",
            branch=branch2,
            description="Manages recruitment and employee relations."
        )
        dept3 = Department.objects.create(
            code="#FIN003",
            name="Finance",
            branch=branch1,
            description="Manages financial operations and budgeting."
        )
        dept4 = Department.objects.create(
            code="#MKT004",
            name="Marketing",
            branch=branch2,
            description="Handles marketing campaigns and branding."
        )
        dept5 = Department.objects.create(
            code="#OPS005",
            name="Operations",
            branch=branch1,
            description="Manages daily operations and logistics."
        )
        self.stdout.write(self.style.SUCCESS(f'Created departments: {dept1}, {dept2}, {dept3}, {dept4}, {dept5}'))

        # Define Permissions for Roles
        senior_developer_permissions = {
            "dashboard": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "task": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "projectTracker": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "onboarding": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "attendance": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False}
        }
        junior_developer_permissions = {
            "dashboard": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "task": {"fullAccess": False, "view": True, "create": True, "edit": False, "delete": False},
            "projectTracker": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "onboarding": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "attendance": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False}
        }
        hr_manager_permissions = {
            "dashboard": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "task": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "projectTracker": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "onboarding": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "attendance": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True}
        }
        recruitment_specialist_permissions = {
            "dashboard": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "task": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "projectTracker": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "onboarding": {"fullAccess": False, "view": True, "create": True, "edit": False, "delete": False},
            "attendance": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False}
        }
        finance_manager_permissions = {
            "dashboard": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "task": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "projectTracker": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "onboarding": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "attendance": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False}
        }
        accountant_permissions = {
            "dashboard": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "task": {"fullAccess": False, "view": True, "create": True, "edit": False, "delete": False},
            "projectTracker": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "onboarding": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "attendance": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False}
        }
        marketing_lead_permissions = {
            "dashboard": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "task": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "projectTracker": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "onboarding": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "attendance": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False}
        }
        content_creator_permissions = {
            "dashboard": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "task": {"fullAccess": False, "view": True, "create": True, "edit": False, "delete": False},
            "projectTracker": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "onboarding": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "attendance": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False}
        }
        operations_manager_permissions = {
            "dashboard": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "task": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True},
            "projectTracker": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "onboarding": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "attendance": {"fullAccess": True, "view": True, "create": True, "edit": True, "delete": True}
        }
        logistics_coordinator_permissions = {
            "dashboard": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "task": {"fullAccess": False, "view": True, "create": True, "edit": False, "delete": False},
            "projectTracker": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False},
            "onboarding": {"fullAccess": False, "view": False, "create": False, "edit": False, "delete": False},
            "attendance": {"fullAccess": False, "view": True, "create": False, "edit": False, "delete": False}
        }

        # Create Roles for Each Department
        role1 = Role.objects.create(
            name="Senior Developer",
            description="Senior software developer role",
            department=dept1,
            permissions=senior_developer_permissions
        )
        role2 = Role.objects.create(
            name="Junior Developer",
            description="Junior software developer role",
            department=dept1,
            permissions=junior_developer_permissions
        )
        role3 = Role.objects.create(
            name="HR Manager",
            description="Human Resources Manager role",
            department=dept2,
            permissions=hr_manager_permissions
        )
        role4 = Role.objects.create(
            name="Recruitment Specialist",
            description="Specialist in recruitment",
            department=dept2,
            permissions=recruitment_specialist_permissions
        )
        role5 = Role.objects.create(
            name="Finance Manager",
            description="Manages financial operations",
            department=dept3,
            permissions=finance_manager_permissions
        )
        role6 = Role.objects.create(
            name="Accountant",
            description="Handles accounting tasks",
            department=dept3,
            permissions=accountant_permissions
        )
        role7 = Role.objects.create(
            name="Marketing Lead",
            description="Leads marketing campaigns",
            department=dept4,
            permissions=marketing_lead_permissions
        )
        role8 = Role.objects.create(
            name="Content Creator",
            description="Creates marketing content",
            department=dept4,
            permissions=content_creator_permissions
        )
        role9 = Role.objects.create(
            name="Operations Manager",
            description="Manages daily operations",
            department=dept5,
            permissions=operations_manager_permissions
        )
        role10 = Role.objects.create(
            name="Logistics Coordinator",
            description="Coordinates logistics",
            department=dept5,
            permissions=logistics_coordinator_permissions
        )
        self.stdout.write(self.style.SUCCESS(f'Created roles: {role1}, {role2}, {role3}, {role4}, {role5}, {role6}, {role7}, {role8}, {role9}, {role10}'))

        # Create Users with Profiles
        # User 1: Senior Developer in IT (Chennai - Main)
        user1 = User.objects.create_user(
            username="senior_dev@example.com",
            email="senior_dev@example.com",
            password="password123",
            first_name="John",
            last_name="Doe"
        )
        profile1 = Profile.objects.create(
            user=user1,
            phone="9876543210",
            role=role1,
            profilePic="https://example.com/john.jpg",
            contact_number="9876543210",
            department=dept1,
            branch=branch1,
            employee_id="EMP001"
        )
        profile1.available_branches.set([branch1])

        # User 2: HR Manager in HR (Mumbai - Central)
        user2 = User.objects.create_user(
            username="hr_manager@example.com",
            email="hr_manager@example.com",
            password="password123",
            first_name="Jane",
            last_name="Smith"
        )
        profile2 = Profile.objects.create(
            user=user2,
            phone="9123456789",
            role=role3,
            profilePic="https://example.com/jane.jpg",
            contact_number="9123456789",
            department=dept2,
            branch=branch2,
            employee_id="EMP002"
        )
        profile2.available_branches.set([branch2])

        # User 3: Finance Manager in Finance (Chennai - Main)
        user3 = User.objects.create_user(
            username="finance_manager@example.com",
            email="finance_manager@example.com",
            password="password123",
            first_name="Alice",
            last_name="Johnson"
        )
        profile3 = Profile.objects.create(
            user=user3,
            phone="9234567890",
            role=role5,
            profilePic="https://example.com/alice.jpg",
            contact_number="9234567890",
            department=dept3,
            branch=branch1,
            employee_id="EMP003"
        )
        profile3.available_branches.set([branch1])

        # User 4: Marketing Lead in Marketing (Mumbai - Central)
        user4 = User.objects.create_user(
            username="marketing_lead@example.com",
            email="marketing_lead@example.com",
            password="password123",
            first_name="Bob",
            last_name="Williams"
        )
        profile4 = Profile.objects.create(
            user=user4,
            phone="9345678901",
            role=role7,
            profilePic="https://example.com/bob.jpg",
            contact_number="9345678901",
            department=dept4,
            branch=branch2,
            employee_id="EMP004"
        )
        profile4.available_branches.set([branch2])

        # User 5: Operations Manager in Operations (Chennai - Main)
        user5 = User.objects.create_user(
            username="ops_manager@example.com",
            email="ops_manager@example.com",
            password="password123",
            first_name="Emma",
            last_name="Brown"
        )
        profile5 = Profile.objects.create(
            user=user5,
            phone="9456789012",
            role=role9,
            profilePic="https://example.com/emma.jpg",
            contact_number="9456789012",
            department=dept5,
            branch=branch1,
            employee_id="EMP005"
        )
        profile5.available_branches.set([branch1])

        # User 6: Junior Developer in IT (Mumbai - Central)
        user6 = User.objects.create_user(
            username="junior_dev@example.com",
            email="junior_dev@example.com",
            password="password123",
            first_name="Michael",
            last_name="Lee"
        )
        profile6 = Profile.objects.create(
            user=user6,
            phone="9567890123",
            role=role2,
            profilePic="https://example.com/michael.jpg",
            contact_number="9567890123",
            department=dept1,
            branch=branch2,
            employee_id="EMP006"
        )
        profile6.available_branches.set([branch2])

        self.stdout.write(self.style.SUCCESS(f'Created users: {user1.email}, {user2.email}, {user3.email}, {user4.email}, {user5.email}, {user6.email}'))
        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))