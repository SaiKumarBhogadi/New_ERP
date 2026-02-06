# core/management/commands/createsuperuser.py
# (or wherever you placed it)

from django.core.management import CommandError
from django.contrib.auth.management.commands import createsuperuser
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Command(createsuperuser.Command):
    help = 'Create a superuser with email as login (no username field)'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        # Remove username argument (we don't use it)
        parser.remove_argument('username')

        # Add/keep your custom fields
        parser.add_argument('--first-name', dest='first_name', default=None, help='First name (required)')
        parser.add_argument('--last-name', dest='last_name', default=None, help='Last name (optional)')
        parser.add_argument('--contact-number', dest='contact_number', default=None, help='Contact number (optional)')
        parser.add_argument('--employee-id', dest='employee_id', default=None, help='Employee ID (optional)')
        parser.add_argument('--profile-pic', dest='profile_pic', default=None, help='Profile picture URL (optional)')

    def handle(self, *args, **options):
        # Force skip username prompt (we don't have username field)
        options['username'] = None

        # Get email (required)
        email = options.get('email')
        if not email:
            email = self.get_input_data(self, 'email', 'Email address: ', required=True)

        # Get first name (required by REQUIRED_FIELDS)
        first_name = options.get('first_name')
        if not first_name:
            first_name = self.get_input_data(self, 'first_name', 'First name: ', required=True)

        # Optional fields
        last_name = options.get('last_name') or self.get_input_data(self, 'last_name', 'Last name (optional): ', default='')
        contact_number = options.get('contact_number') or self.get_input_data(self, 'contact_number', 'Contact number (optional): ', default=None)
        employee_id = options.get('employee_id') or self.get_input_data(self, 'employee_id', 'Employee ID (optional): ', default=None)
        profile_pic = options.get('profile_pic') or self.get_input_data(self, 'profile_pic', 'Profile picture URL (optional): ', default=None)

        # Password
        password = options.get('password')
        if not password:
            while True:
                password = self.get_input_data(self, 'password', 'Password: ', is_password=True)
                password2 = self.get_input_data(self, 'password', 'Password (again): ', is_password=True)
                if password == password2:
                    break
                self.stderr.write(self.style.ERROR("Passwords don't match."))

        # Create superuser
        try:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                contact_number=contact_number or None,
                employee_id=employee_id or None,
                profile_pic=profile_pic or None,
            )
            user.date_joined = timezone.now()
            user.save()

            self.stdout.write(self.style.SUCCESS(
                f'Superuser created successfully:\n'
                f'Email: {email}\n'
                f'Name: {first_name} {last_name}\n'
                f'Login with this email and password.'
            ))
        except Exception as e:
            raise CommandError(f'Error creating superuser: {str(e)}')

    def get_input_data(self, field, prompt, required=False, default=None, is_password=False):
        while True:
            if is_password:
                value = input(prompt).strip()
            else:
                value = input(prompt).strip()

            if not value and default is not None:
                return default

            if not value and required:
                self.stderr.write(self.style.ERROR(f'{field.capitalize()} is required.'))
                continue

            return value or None