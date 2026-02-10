from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.db.models import JSONField, UniqueConstraint
from django.core.validators import RegexValidator
from django.conf import settings
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
    
    
class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    is_active = models.BooleanField(default=True)         
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True) 
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_branches')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_branches')
      

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        ordering = ['name']

    def __str__(self):
        return self.name

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    
    contact_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Contact number must be digits only, optionally starting with + (up to 15 digits)."
            )
        ],
    )
    
    branch = models.ForeignKey(
        'Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_branch'
    )
    
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    role = models.ForeignKey(
        'Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    reporting_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name="Reporting To"
    )
    
    available_branches = models.ManyToManyField(Branch,blank=True,related_name='users')

    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    reset_token = models.CharField(max_length=32, blank=True, null=True)
    reset_token_expiry = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_users')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_users')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['employee_id']),
            models.Index(fields=['is_active']),
        ]

    def get_full_name(self):
        """
        Returns the user's full name, falling back to email if name is empty.
        Used for display in dropdowns, user lists, etc.
        """
        full_name = f"{self.first_name.strip()} {self.last_name.strip()}".strip()
        return full_name if full_name else self.email

    def __str__(self):
        # This affects admin panel, logs, StringRelatedField, etc.
        return self.get_full_name()





class Department(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    code = models.CharField(max_length=50, unique=True)
    department_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)          
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)   
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_departments')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_departments')   

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        constraints = [
            UniqueConstraint(
                fields=['branch', 'department_name'],
                name='unique_dept_name_per_branch'
            ),
            UniqueConstraint(
                fields=['code'],
                name='unique_department_code'
            ),
        ]
        indexes = [
            models.Index(fields=['branch', 'department_name']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.department_name


class Role(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='roles')
    role = models.CharField(max_length=25)
    description = models.TextField(blank=True, null=True)
    permissions = JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)          
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_roles')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_roles')    

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        constraints = [
            UniqueConstraint(
                fields=['department', 'role'],
                name='unique_role_per_department'
            ),
        ]
        indexes = [
            models.Index(fields=['department', 'role']),
        ]

    def __str__(self):
        return self.role




from django.db import models

from django.utils import timezone
from django.db.models import UniqueConstraint, Index
from django.core.validators import MinValueValidator



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_categories')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_categories')

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name'], name='unique_category_name')
        ]
        indexes = [
            Index(fields=['name', 'is_active'])
        ]

    def __str__(self):
        return self.name

from decimal import Decimal
from django.core.validators import MinValueValidator

class TaxCode(models.Model):
    name = models.CharField(max_length=100, unique=True)
    percentage = models.DecimalField(
                max_digits=5,
                decimal_places=2,
                validators=[MinValueValidator(Decimal('0.00'))]
            )

    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_tax_codes')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_tax_codes')

    class Meta:
        verbose_name = "Tax Code"
        verbose_name_plural = "Tax Codes"
        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name'], name='unique_tax_code_name')
        ]
        indexes = [
            Index(fields=['name', 'is_active'])
        ]

    def __str__(self):
        return self.name


class UOM(models.Model):
    name = models.CharField(max_length=100, unique=True)
    items = models.IntegerField(validators=[MinValueValidator(1)])
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_uoms')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_uoms')

    class Meta:
        verbose_name = "UOM"
        verbose_name_plural = "UOMs"
        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name'], name='unique_uom_name')
        ]
        indexes = [
            Index(fields=['name', 'is_active'])
        ]

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200)
    manager_name = models.CharField(max_length=100, blank=True, null=True)
    contact_info = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_warehouses')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_warehouses')

    class Meta:
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"
        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name'], name='unique_warehouse_name')
        ]
        indexes = [
            Index(fields=['name', 'is_active'])
        ]

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=50, unique=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_sizes')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_sizes')

    class Meta:
        verbose_name = "Size"
        verbose_name_plural = "Sizes"
        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name'], name='unique_size_name')
        ]
        indexes = [
            Index(fields=['name', 'is_active'])
        ]

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_colors')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_colors')

    class Meta:
        verbose_name = "Color"
        verbose_name_plural = "Colors"
        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name'], name='unique_color_name')
        ]
        indexes = [
            Index(fields=['name', 'is_active'])
        ]

    def __str__(self):
        return self.name


class ProductSupplier(models.Model):
    name = models.CharField(max_length=100, unique=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_product_suppliers')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_product_suppliers')

    class Meta:
        verbose_name = "Product Supplier"
        verbose_name_plural = "Product Suppliers"
        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name'], name='unique_product_supplier_name')
        ]
        indexes = [
            Index(fields=['name', 'is_active'])
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    product_id = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    name = models.CharField(max_length=100)
    product_type = models.CharField(
        max_length=50,
        choices=[('Goods', 'Goods'), ('Services', 'Services'), ('Combo', 'Combo')]
    )
    description = models.TextField(blank=True, null=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_category = models.BooleanField(default=False)
    custom_category = models.CharField(max_length=255, blank=True, null=True)
    sub_category = models.CharField(max_length=100, blank=True, null=True)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)])
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])

    tax_code = models.ForeignKey(TaxCode, on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_tax_code = models.BooleanField(default=False)
    custom_tax_code = models.CharField(max_length=255, blank=True, null=True)

    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    uom = models.ForeignKey(UOM, on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_uom = models.BooleanField(default=False)
    custom_uom = models.CharField(max_length=255, blank=True, null=True)

    stock_level = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_warehouse = models.BooleanField(default=False)
    custom_warehouse = models.CharField(max_length=255, blank=True, null=True)

    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_size = models.BooleanField(default=False)
    custom_size = models.CharField(max_length=255, blank=True, null=True)

    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_color = models.BooleanField(default=False)
    custom_color = models.CharField(max_length=255, blank=True, null=True)

    weight = models.CharField(max_length=50, blank=True, null=True)
    specifications = models.TextField(blank=True, null=True)

    related_products = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='related_to')
    is_custom_related_products = models.BooleanField(default=False)
    custom_related_products = models.CharField(max_length=255, blank=True, null=True)

    supplier = models.ForeignKey(ProductSupplier, on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_supplier = models.BooleanField(default=False)
    custom_supplier = models.CharField(max_length=255, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Discontinued', 'Discontinued')]
    )
    product_usage = models.CharField(
        max_length=20,
        choices=[('Purchase', 'Purchase'), ('Sale', 'Sale'), ('Both', 'Both')]
    )
    image = models.ImageField(upload_to='product_images/%Y/%m/%d/', blank=True, null=True)
    

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_products')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_products')

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']
        indexes = [
            Index(fields=['name', 'status', 'is_active']),
            Index(fields=['product_id'])
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.product_id:
            self.product_id = f'CVB{self.id:03d}'
            super().save(update_fields=['product_id'])



class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    customer_type = models.CharField(
        max_length=50,
        choices=[('Individual', 'Individual'), ('Business', 'Business'), ('Organization', 'Organization')]
    )
    customer_id = models.CharField(max_length=10, unique=True, null=True, blank=True, editable=False)
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active'
    )
    assigned_sales_rep = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_customers',
        limit_choices_to={'role__role': 'Sales Representative'}  # ← only sales reps
    )

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    gst_tax_id = models.CharField(max_length=20, blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    available_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    payment_terms = models.CharField(max_length=50, blank=True, null=True)
    credit_term = models.CharField(max_length=50, blank=True, null=True)
    last_edit_date = models.DateTimeField(auto_now=True)

    # Added for consistency with other modules
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_customers')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_customers')

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['-last_edit_date']
        indexes = [
            Index(fields=['email', 'status', 'is_active']),
            Index(fields=['customer_id'])
        ]
        constraints = [
            UniqueConstraint(fields=['email'], name='unique_customer_email')
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id or 'N/A'})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.customer_id:
            last_customer = Customer.objects.order_by('-id').first()
            if last_customer and last_customer.customer_id:
                last_id = int(last_customer.customer_id.replace('CUS', '')) + 1
            else:
                last_id = 1

            self.customer_id = f'CUS{last_id:04d}'
        super().save(*args, **kwargs)



from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import UniqueConstraint, Index


# All Choices
class CountryChoices(models.TextChoices):
    INDIA = 'IN', 'India'
    USA = 'US', 'United States'
    CANADA = 'CA', 'Canada'
    UNITED_KINGDOM = 'GB', 'United Kingdom'
    AUSTRALIA = 'AU', 'Australia'
    GERMANY = 'DE', 'Germany'
    FRANCE = 'FR', 'France'
    SINGAPORE = 'SG', 'Singapore'
    UAE = 'AE', 'United Arab Emirates'
    CHINA = 'CN', 'China'
    JAPAN = 'JP', 'Japan'


SUPPLIER_TYPE_CHOICES = [
    ('Manufacturer', 'Manufacturer'),
    ('Distributor', 'Distributor'),
    ('Service Provider', 'Service Provider'),
    ('Trader', 'Trader'),
    ('Importer', 'Importer'),
    ('Other', 'Other'),
    ('Custom', 'Custom'),
]

STATUS_CHOICES = [
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
    ('Blacklisted', 'Blacklisted')
]

WORKFLOW_STATUS_CHOICES = [
    ('Draft', 'Draft'),
    ('Submitted', 'Submitted'),
]

TIER_CHOICES = [
    ('Strategic', 'Strategic'),
    ('Preferred', 'Preferred'),
    ('Backup', 'Backup')
]

PAYMENT_METHOD_CHOICES = [
    ('Wire Transfer', 'Wire Transfer'),
    ('ACH', 'ACH'),
    ('Check', 'Check'),
    ('Credit Card', 'Credit Card'),
    ('UPI', 'UPI')
]

PAYMENT_TERMS_CHOICES = [
    ('Net 15', 'Net 15'),
    ('Net 30', 'Net 30'),
    ('Net 45', 'Net 45'),
    ('Net 60', 'Net 60'),
    ('Prepaid', 'Prepaid'),
    ('COD', 'COD'),
    ('Custom', 'Custom'),
]

CURRENCY_CHOICES = [
    ('INR', 'Indian Rupee'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
    ('SGD', 'Singapore Dollar')
]

RISK_RATING_CHOICES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High')
]


class Supplier(models.Model):
    supplier_id = models.CharField(max_length=15, unique=True, editable=False, blank=True)

    tax_id = models.CharField(max_length=30, unique=True, verbose_name="Tax ID / GSTIN / VAT")
    supplier_name = models.CharField(max_length=200)
    company_registration_number = models.CharField(max_length=50, blank=True, null=True)
    legal_entity_name = models.CharField(max_length=200)
    country_of_registration = models.CharField(max_length=3, choices=CountryChoices.choices, default=CountryChoices.INDIA)

    # Supplier Type with custom
    supplier_type = models.CharField(max_length=30, choices=SUPPLIER_TYPE_CHOICES, blank=True, null=True)
    is_custom_supplier_type = models.BooleanField(default=False)
    custom_supplier_type = models.CharField(max_length=100, blank=True, null=True)

    # Supplier Status (Active/Inactive/Blacklisted)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Active')

    # Workflow Status (for buttons: Save Draft / Submit)
    workflow_status = models.CharField(max_length=15, choices=WORKFLOW_STATUS_CHOICES, default='Draft') 

    supplier_tier = models.CharField(max_length=20, choices=TIER_CHOICES, blank=True, null=True)
    product_details = models.TextField(blank=True, default='')

    primary_contact_first_name = models.CharField(max_length=100)
    primary_contact_last_name = models.CharField(max_length=100, blank=True, default='')
    primary_contact_designation = models.CharField(max_length=100, blank=True, default='')
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=20)
    alternate_contact_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    relationship_manager = models.CharField(max_length=100, blank=True, null=True)

    registered_address = models.TextField()
    mailing_address = models.TextField(blank=True, null=True)
    warehouse_address = models.TextField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    region = models.CharField(max_length=3, choices=CountryChoices.choices, default=CountryChoices.INDIA)

    bank_name = models.CharField(max_length=150, blank=True, default='')
    bank_account_no = models.CharField(max_length=50, default='')
    iban_swift = models.CharField(max_length=50, blank=True, null=True)

    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)

    # Payment Terms with custom
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, blank=True, null=True)
    is_custom_payment_terms = models.BooleanField(default=False)
    custom_payment_terms = models.CharField(max_length=100, blank=True, null=True)

    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    tax_withholding_setup = models.CharField(max_length=100, blank=True, null=True)

    categories_served = models.TextField(default='')
    incoterms = models.CharField(max_length=10, blank=True, null=True)
    product_catalog = models.TextField(blank=True, default='')
    freight_terms = models.CharField(max_length=100, blank=True, null=True)
    min_order_quantity = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    return_replacement_policy = models.TextField(blank=True, default='')
    avg_lead_time_days = models.PositiveIntegerField(default=30, validators=[MinValueValidator(1)])
    contract_references = models.TextField(blank=True, default='')

    certifications = models.TextField(blank=True, null=True)
    compliance_status = models.CharField(max_length=100, blank=True, null=True)
    insurance_documents = models.FileField(upload_to='suppliers/insurance/', blank=True, null=True)
    mitigation_plans = models.FileField(upload_to='suppliers/mitigation/', blank=True, null=True)
    risk_rating = models.CharField(max_length=10, choices=RISK_RATING_CHOICES, default='Low')
    risk_notes = models.TextField(blank=True, null=True)
    last_risk_assessment = models.DateField(null=True, blank=True)

    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    quality_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    defect_return_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    last_evaluation_date = models.DateField(null=True, blank=True)
    contract_breaches = models.TextField(blank=True, default='')
    improvement_plans = models.TextField(blank=True, default='')
    complaints_registered = models.TextField(blank=True, default='')

    external_key_contact = models.CharField(max_length=100, blank=True, null=True)
    interaction_logs = models.FileField(upload_to='suppliers/interaction_logs/', blank=True, null=True)
    dispute_resolutions = models.FileField(upload_to='suppliers/dispute/', blank=True, null=True)
    feedback_surveys = models.FileField(upload_to='suppliers/feedback/', blank=True, null=True)
    visit_mom_history = models.FileField(upload_to='suppliers/mom/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_suppliers')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_suppliers')

    class Meta:
        verbose_name_plural = "Suppliers"
        ordering = ['-created_at']
        indexes = [
            Index(fields=['supplier_id', 'status', 'tax_id']),
            Index(fields=['supplier_name'])
        ]
        constraints = [
            UniqueConstraint(fields=['tax_id'], name='unique_supplier_tax_id')
        ]

    def save(self, *args, **kwargs):
        if not self.supplier_id:
            last = Supplier.objects.order_by('-id').first()
            num = 1
            if last and last.supplier_id and '-' in last.supplier_id:
                try:
                    num = int(last.supplier_id.split('-')[1]) + 1
                except:
                    pass
            self.supplier_id = f"SUP-{num:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier_id} - {self.supplier_name}"


# Related Models
class SupplierComment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    commented_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class SupplierAttachment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='extra_attachments')
    file = models.FileField(upload_to='suppliers/extra_attachments/%Y/%m/%d/')
    description = models.CharField(max_length=300, blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']


class SupplierHistory(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    changes = models.TextField()  # e.g. "payment_terms changed from Net 30 to Custom: 45 days"

    class Meta:
        ordering = ['-changed_at']