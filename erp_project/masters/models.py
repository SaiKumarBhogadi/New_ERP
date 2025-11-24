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

class Supplier(models.Model):
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
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True)
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