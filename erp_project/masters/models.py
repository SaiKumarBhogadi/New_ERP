from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.db.models import JSONField

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
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_branch')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)
    reporting_to = models.CharField(max_length=25, blank=True, null=True)
    available_branches = JSONField(blank=True, default=list)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    reset_token = models.CharField(max_length=32, blank=True, null=True)
    reset_token_expiry = models.DateTimeField(blank=True, null=True)

    # Permissions / Django flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Specify email as the unique identifier for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

class Department(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    code = models.CharField(max_length=50, unique=True)
    department_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.department_name

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        unique_together = ('branch', 'department_name')  # name unique per branch

class Role(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='roles')
    role = models.CharField(max_length=25)
    description = models.TextField(blank=True, null=True)
    permissions = JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.role

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        unique_together = ('department', 'role')






class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class TaxCode(models.Model):
    name = models.CharField(max_length=100, unique=True)
    percentage = models.FloatField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class UOM(models.Model):
    name = models.CharField(max_length=100, unique=True)
    items = models.IntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200)
    manager_name = models.CharField(max_length=100, blank=True)
    contact_info = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class ProductSupplier(models.Model):
    name = models.CharField(max_length=100, unique=True)
    contact_person = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()

    def __str__(self):
        return self.name

class Product(models.Model):
    product_id = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    name = models.CharField(max_length=100)
    product_type = models.CharField(
        max_length=50,
        choices=[('Goods', 'Goods'), ('Services', 'Services'), ('Combo', 'Combo')]
    )
    description = models.TextField(blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_category = models.BooleanField(default=False)
    custom_category = models.CharField(max_length=255, blank=True, null=True)
    tax_code = models.ForeignKey('TaxCode', on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_tax_code = models.BooleanField(default=False)
    custom_tax_code = models.CharField(max_length=255, blank=True, null=True)
    uom = models.ForeignKey('UOM', on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_uom = models.BooleanField(default=False)
    custom_uom = models.CharField(max_length=255, blank=True, null=True)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_warehouse = models.BooleanField(default=False)
    custom_warehouse = models.CharField(max_length=255, blank=True, null=True)
    size = models.ForeignKey('Size', on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_size = models.BooleanField(default=False)
    custom_size = models.CharField(max_length=255, blank=True, null=True)
    color = models.ForeignKey('Color', on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_color = models.BooleanField(default=False)
    custom_color = models.CharField(max_length=255, blank=True, null=True)
    supplier = models.ForeignKey('ProductSupplier', on_delete=models.SET_NULL, null=True, blank=True)
    is_custom_supplier = models.BooleanField(default=False)
    custom_supplier = models.CharField(max_length=255, blank=True, null=True)
    related_products = models.CharField(max_length=1000, blank=True)
    is_custom_related_products = models.BooleanField(default=False)
    custom_related_products = models.CharField(max_length=255, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    quantity = models.IntegerField(default=0)
    stock_level = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=0)
    weight = models.CharField(max_length=50, blank=True)
    specifications = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Discontinued', 'Discontinued')]
    )
    product_usage = models.CharField(
        max_length=20,
        choices=[('Purchase', 'Purchase'), ('Sale', 'Sale'), ('Both', 'Both')]
    )
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    sub_category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.product_id:
            self.product_id = f'CVB{self.id:03d}'
            Product.objects.filter(pk=self.pk).update(product_id=self.product_id)

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    customer_type = models.CharField(max_length=50, choices=[
        ('Individual', 'Individual'),
        ('Business', 'Business'),
        ('Organization', 'Organization'),
    ])
    customer_id = models.CharField(max_length=10, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ])
    assigned_sales_rep = models.ForeignKey(
    'masters.CustomUser',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='assigned_customers'
    )

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    gst_tax_id = models.CharField(max_length=20, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    available_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, blank=True)
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=50, blank=True)
    credit_term = models.CharField(max_length=50, blank=True)
    last_edit_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"
    
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# --------------------------- CHOICES ---------------------------
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
]

STATUS_CHOICES = [
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
    ('Blacklisted', 'Blacklisted')
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
    ('COD', 'COD')
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


# --------------------------- MAIN MODEL ---------------------------
class Supplier(models.Model):
    # Auto-generated ID
    supplier_id = models.CharField(max_length=15, unique=True, editable=False, blank=True)

    # Basic Info
    tax_id = models.CharField(max_length=30, unique=True, verbose_name="Tax ID / GSTIN / VAT")
    supplier_name = models.CharField(max_length=200)
    company_registration_number = models.CharField(max_length=50, blank=True, null=True)
    legal_entity_name = models.CharField(max_length=200)
    country_of_registration = models.CharField(max_length=3, choices=CountryChoices.choices, default=CountryChoices.INDIA)

    supplier_type = models.CharField(max_length=30, choices=SUPPLIER_TYPE_CHOICES, default='Manufacturer')
    supplier_tier = models.CharField(max_length=20, choices=TIER_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Active')
    product_details = models.TextField(blank=True, default='')

    # Contact Information
    primary_contact_first_name = models.CharField(max_length=100)
    primary_contact_last_name = models.CharField(max_length=100, blank=True, default='')
    primary_contact_designation = models.CharField(max_length=100, blank=True, default='')
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=20)
    alternate_contact_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    relationship_manager = models.CharField(max_length=100, blank=True, null=True)

    # Addresses
    registered_address = models.TextField()
    mailing_address = models.TextField(blank=True, null=True)
    warehouse_address = models.TextField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    region = models.CharField(max_length=3, choices=CountryChoices.choices, default=CountryChoices.INDIA)

    # Banking & Payment
    bank_name = models.CharField(max_length=150, blank=True, default='')
    bank_account_no = models.CharField(max_length=50, default='')
    iban_swift = models.CharField(max_length=50, blank=True, null=True)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='Wire Transfer')
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default='Net 30')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    tax_withholding_setup = models.CharField(max_length=100, blank=True, null=True)

    # Procurement & Operational
    categories_served = models.TextField(default='')
    incoterms = models.CharField(max_length=10, blank=True, null=True)
    product_catalog = models.TextField(blank=True, default='')
    freight_terms = models.CharField(max_length=100, blank=True, null=True)
    min_order_quantity = models.PositiveIntegerField(null=True, blank=True)
    return_replacement_policy = models.TextField(blank=True, default='')
    avg_lead_time_days = models.PositiveIntegerField(default=30)  # Most important fix
    contract_references = models.TextField(blank=True, default='')

    # Compliance & Risk
    certifications = models.TextField(blank=True, null=True)
    compliance_status = models.CharField(max_length=100, blank=True, null=True)
    insurance_documents = models.FileField(upload_to='suppliers/insurance/', blank=True, null=True)
    mitigation_plans = models.FileField(upload_to='suppliers/mitigation/', blank=True, null=True)
    risk_rating = models.CharField(max_length=10, choices=RISK_RATING_CHOICES, default='Low')
    risk_notes = models.TextField(blank=True, null=True)
    last_risk_assessment = models.DateField(null=True, blank=True)

    # Performance & Evaluation
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quality_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    defect_return_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    last_evaluation_date = models.DateField(null=True, blank=True)
    contract_breaches = models.TextField(blank=True, default='')
    improvement_plans = models.TextField(blank=True, default='')
    complaints_registered = models.TextField(blank=True, default='')

    # Relationship
    external_key_contact = models.CharField(max_length=100, blank=True, null=True)
    interaction_logs = models.FileField(upload_to='suppliers/interaction_logs/', blank=True, null=True)
    dispute_resolutions = models.FileField(upload_to='suppliers/dispute/', blank=True, null=True)
    feedback_surveys = models.FileField(upload_to='suppliers/feedback/', blank=True, null=True)
    visit_mom_history = models.FileField(upload_to='suppliers/mom/', blank=True, null=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_suppliers')

    class Meta:
                          # Prevents conflict with old table
        ordering = ['-created_at']
        verbose_name_plural = "SuppliersMaster"

    def save(self, *args, **kwargs):
        if not self.supplier_id:
            last = Supplier.objects.order_by('-id').first()
            if last and last.supplier_id and '-' in last.supplier_id:
                try:
                    num = int(last.supplier_id.split('-')[1]) + 1
                except:
                    num = 1
            else:
                num = 1
            self.supplier_id = f"SUP-{num:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier_id} - {self.supplier_name}"


# --------------------------- RELATED MODELS ---------------------------
class SupplierComment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    commented_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commented_by} on {self.supplier}"


class SupplierAttachment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='extra_attachments')
    file = models.FileField(upload_to='suppliers/extra_attachments/%Y/%m/%d/')
    description = models.CharField(max_length=300, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.file.name.split('/')[-1]