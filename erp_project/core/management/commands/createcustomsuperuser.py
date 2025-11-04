from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError
from django.contrib.auth import get_user_model
from core.models import Profile

User = get_user_model()

class Command(createsuperuser.Command):
    help = 'Create a superuser with registration details similar to RegisterView'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        # Add arguments for profile fields
       
        parser.add_argument('--profile-pic', dest='profile_pic', default=None, help='Profile picture URL')
        parser.add_argument('--contact-number', dest='contact_number', default=None, help='Contact number')
        parser.add_argument('--employee-id', dest='employee_id', default=None, help='Employee ID')
        # Add last name argument
        parser.add_argument('--last-name', dest='last_name', default=None, help='Last name')

    def handle(self, *args, **options):
        # Skip username prompt since we use email
        options['username'] = None

        # Prompt for required fields
        email = options.get('email')
        if not email:
            email = self.get_input_data('email', 'Email address: ')

        first_name = options.get('first_name')
        if not first_name:
            first_name = self.get_input_data('first_name', 'First name: ')

        last_name = options.get('last_name')
        if not last_name:
            last_name = self.get_input_data('last_name', 'Last name: ')

        password = options.get('password')
        if not password:
            password = self.get_input_data('password', 'Password: ', is_password=True)
            password2 = self.get_input_data('password', 'Password (again): ', is_password=True)
            if password != password2:
                raise CommandError("Error: Your passwords didn't match.")

        # Prompt for profile fields (optional)
        profile_pic = options.get('profile_pic')
        if not profile_pic:
            profile_pic = self.get_input_data('profile_pic', 'Profile picture URL (optional): ', default='')

        contact_number = options.get('contact_number')
        if not contact_number:
            contact_number = self.get_input_data('contact_number', 'Contact number (optional): ', default='')

        employee_id = options.get('employee_id')
        if not employee_id:
            employee_id = self.get_input_data('employee_id', 'Employee ID (optional): ', default='')

        # Create the superuser
        user = User.objects.create_superuser(
            username=email,  # Using email as username
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create the associated Profile
        Profile.objects.create(
            user=user,
            profilePic=profile_pic if profile_pic else None,
            contact_number=contact_number if contact_number else None,
            employee_id=employee_id if employee_id else None
        )

        self.stdout.write(self.style.SUCCESS(f'Superuser created successfully: {email}'))

    def get_input_data(self, field, prompt, default=None, is_password=False):
        while True:
            if is_password:
                value = input(prompt).strip()
            else:
                value = input(prompt).strip() or default
            if value:
                return value
            if default is not None:
                return default
            self.stdout.write(self.style.ERROR(f'Error: This field cannot be blank.'))
