from rest_framework import serializers
from .models import CustomUser, Branch, Department, Role, Category, TaxCode, UOM, Warehouse, Size, Color, ProductSupplier, Product, Customer
from core.models import Candidate
import re
import logging

logger = logging.getLogger(__name__)

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name']

class DepartmentDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'department_name']

class DepartmentSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'code', 'department_name', 'branch', 'description', 'roles']

    def get_roles(self, obj):
        if self.context.get('include_roles', True):
            return RoleSerializer(obj.roles.all(), many=True).data
        return []

import re
from rest_framework import serializers

class DepartmentCreateSerializer(serializers.ModelSerializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())

    class Meta:
        model = Department
        fields = ['id', 'code', 'department_name', 'branch', 'description']

    def validate_department_name(self, value):
        if not re.match(r'^[A-Za-z ]+$', value):
            raise serializers.ValidationError(
                "Department name can contain only letters and spaces."
            )
        return value

    def validate_code(self, value):
        if not re.match(r'^[A-Za-z0-9]+$', value):
            raise serializers.ValidationError(
                "Department code can contain only letters and numbers."
            )
        return value
    
    def validate_description(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError(
                "Description cannot exceed 500 characters."
            )
        return value


class RoleSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'role', 'description', 'permissions', 'department_name', 'branch_name']

    def validate_role(self, value):
        # Only allow letters, numbers, and spaces
        if not re.match(r'^[A-Za-z0-9 ]+$', value):
            raise serializers.ValidationError(
                "Role name can contain only letters, numbers, and spaces."
            )
        return value
    
    def validate_description(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError(
                "Description cannot exceed 500 characters."
            )
        return value

class RoleUpdateSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)
    permissions = serializers.JSONField(required=False, allow_null=True, default=dict)

    class Meta:
        model = Role
        fields = ['id', 'role', 'description', 'permissions', 'department', 'department_name', 'branch', 'branch_name']

    def validate_permissions(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("Permissions must be a valid JSON object.")
        return value
    
    def validate_role(self, value):
        if not re.match(r'^[A-Za-z0-9 ]+$', value):
            raise serializers.ValidationError(
                "Role name can contain only letters, numbers, and spaces."
            )
        return value
    
    def validate_description(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError(
                "Description cannot exceed 500 characters."
            )
        return value

from rest_framework import serializers
from .models import CustomUser, Branch, Department, Role
from core.serializers import CandidateDocumentSerializer, CandidateSerializer 
import re
import logging

logger = logging.getLogger(__name__)

class CustomUserDetailSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    role = RoleSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email', 'contact_number', 'department',
            'branch', 'role', 'available_branches', 'reporting_to', 'employee_id', 'profile_pic'
        ]

class CustomUserUpdateSerializer(serializers.ModelSerializer):
    # Mandatory fields
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=True)

    # Optional fields
    contact_number = serializers.CharField(max_length=15, allow_blank=True, allow_null=True)
    reporting_to = serializers.CharField(allow_null=True, allow_blank=True)
    available_branches = serializers.ListField(child=serializers.CharField(), required=False)
    employee_id = serializers.CharField(max_length=50, allow_blank=True, allow_null=True)
    profile_pic = serializers.ImageField(allow_empty_file=True, required=False)

    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'email',
            'contact_number',
            'branch',
            'department',
            'role',
            'reporting_to',
            'available_branches',
            'employee_id',
            'profile_pic'
        ]

    def validate_contact_number(self, value):
        if value and not value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise serializers.ValidationError("Contact number must contain only digits, +, -, or spaces.")
        return value

    def validate_employee_id(self, value):
        if value and self.instance and self.instance.employee_id == value:
            return value
        if value and CustomUser.objects.filter(employee_id=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Employee ID must be unique.")
        return value

class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'contact_number', 'department',
                  'branch', 'role', 'available_branches', 'reporting_to', 'employee_id', 'profile_pic']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'last_name': {'allow_blank': True, 'required': False}
        }

    def validate_email(self, value):
        if self.instance and self.instance.email == value:
            return value
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data.get('last_name', ''),
            contact_number=validated_data.get('contact_number'),
            department=validated_data.get('department'),
            branch=validated_data.get('branch'),
            role=validated_data.get('role'),
            available_branches=validated_data.get('available_branches', []),
            reporting_to=validated_data.get('reporting_to'),
            employee_id=validated_data.get('employee_id'),
            profile_pic=validated_data.get('profile_pic')
        )
        return user

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class TaxCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxCode
        fields = ['id', 'name', 'percentage', 'description']

class UOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = UOM
        fields = ['id', 'name', 'items', 'description']

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'location', 'manager_name', 'contact_info', 'notes']

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'name']

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name']

class ProductSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSupplier
        fields = ['id', 'name', 'contact_person', 'phone_number', 'email', 'address']

from .models import ProductSupplier

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    tax_code = serializers.PrimaryKeyRelatedField(queryset=TaxCode.objects.all(), required=False, allow_null=True)
    uom = serializers.PrimaryKeyRelatedField(queryset=UOM.objects.all(), required=False, allow_null=True)
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all(), required=False, allow_null=True)
    size = serializers.PrimaryKeyRelatedField(queryset=Size.objects.all(), required=False, allow_null=True)
    color = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all(), required=False, allow_null=True)
    supplier = serializers.PrimaryKeyRelatedField(queryset=ProductSupplier.objects.all(), required=False, allow_null=True)

    related_products = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    # Custom fields
    is_custom_category = serializers.BooleanField(default=False, required=False)
    custom_category = serializers.CharField(max_length=255, required=False, allow_blank=True)

    is_custom_tax_code = serializers.BooleanField(default=False, required=False)
    custom_tax_code = serializers.CharField(max_length=255, required=False, allow_blank=True)

    is_custom_uom = serializers.BooleanField(default=False, required=False)
    custom_uom = serializers.CharField(max_length=255, required=False, allow_blank=True)

    is_custom_warehouse = serializers.BooleanField(default=False, required=False)
    custom_warehouse = serializers.CharField(max_length=255, required=False, allow_blank=True)

    is_custom_size = serializers.BooleanField(default=False, required=False)
    custom_size = serializers.CharField(max_length=255, required=False, allow_blank=True)

    is_custom_color = serializers.BooleanField(default=False, required=False)
    custom_color = serializers.CharField(max_length=255, required=False, allow_blank=True)

    is_custom_supplier = serializers.BooleanField(default=False, required=False)
    custom_supplier = serializers.CharField(max_length=255, required=False, allow_blank=True)

    is_custom_related_products = serializers.BooleanField(default=False, required=False)
    custom_related_products = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = Product
        fields = [
            'id', 'product_id', 'name', 'product_type', 'description', 'category', 'is_custom_category',
            'custom_category', 'tax_code', 'is_custom_tax_code', 'custom_tax_code', 'unit_price',
            'discount', 'uom', 'is_custom_uom', 'custom_uom', 'quantity', 'stock_level',
            'reorder_level', 'warehouse', 'is_custom_warehouse', 'custom_warehouse', 'size',
            'is_custom_size', 'custom_size', 'color', 'is_custom_color', 'custom_color', 'weight',
            'specifications', 'supplier', 'is_custom_supplier', 'custom_supplier', 'status',
            'product_usage', 'related_products', 'is_custom_related_products', 'custom_related_products',
            'image', 'sub_category'
        ]

    # ----------------------------
    # VALIDATION
    # ----------------------------
    def validate(self, data):
        required_fields = [
            'name', 'product_type', 'description', 'unit_price', 'discount', 'quantity',
            'stock_level', 'reorder_level', 'weight', 'specifications', 'status',
            'product_usage', 'sub_category'
        ]

        for field in required_fields:
            if field not in data or data[field] in [None, ""]:
                raise serializers.ValidationError({field: f"{field.replace('_',' ').title()} is required"})

        dropdown_fields = ['category', 'tax_code', 'uom', 'warehouse', 'size', 'color', 'supplier']
        for field in dropdown_fields:
            is_custom = data.get(f'is_custom_{field}', False)
            custom_val = data.get(f'custom_{field}', '')
            normal_val = data.get(field)

            if is_custom:
                if not custom_val:
                    raise serializers.ValidationError({
                        f'custom_{field}': f"Custom {field.replace('_',' ').title()} is required"
                    })
            else:
                if normal_val is None:
                    raise serializers.ValidationError({
                        field: f"{field.replace('_',' ').title()} is required"
                    })

        is_custom_rp = data.get('is_custom_related_products', False)
        custom_rp = data.get('custom_related_products', '')
        rp = data.get('related_products', '')

        if is_custom_rp:
            if not custom_rp:
                raise serializers.ValidationError({
                    'custom_related_products': "Custom Related Products required"
                })
        else:
            if not rp:
                raise serializers.ValidationError({
                    'related_products': "Related Products required"
                })

        return data

    # ----------------------------
    # CREATE
    # ----------------------------
    def create(self, validated_data):

        custom_fields = {}
        for field in ['category', 'tax_code', 'uom', 'warehouse', 'size', 'color', 'supplier', 'related_products']:
            custom_fields[f'is_custom_{field}'] = validated_data.pop(f'is_custom_{field}', False)
            custom_fields[f'custom_{field}'] = validated_data.pop(f'custom_{field}', '')

        product = Product.objects.create(**validated_data)

        # Save custom flags & custom values
        for field in ['category', 'tax_code', 'uom', 'warehouse', 'size', 'color', 'supplier', 'related_products']:
            setattr(product, f'is_custom_{field}', custom_fields[f'is_custom_{field}'])
            setattr(product, f'custom_{field}', custom_fields[f'custom_{field}'] if custom_fields[f'is_custom_{field}'] else "")

        product.save()
        return product

    # ----------------------------
    # UPDATE
    # ----------------------------
    def update(self, instance, validated_data):

        custom_fields = {}
        for field in ['category', 'tax_code', 'uom', 'warehouse', 'size', 'color', 'supplier', 'related_products']:
            custom_fields[f'is_custom_{field}'] = validated_data.pop(f'is_custom_{field}', False)
            custom_fields[f'custom_{field}'] = validated_data.pop(f'custom_{field}', '')

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        for field in ['category', 'tax_code', 'uom', 'warehouse', 'size', 'color', 'supplier', 'related_products']:
            setattr(instance, f'is_custom_{field}', custom_fields[f'is_custom_{field}'])
            setattr(instance, f'custom_{field}', custom_fields[f'custom_{field}'] if custom_fields[f'is_custom_{field}'] else "")

        instance.save()
        return instance


class CustomerSerializer(serializers.ModelSerializer):
    assigned_sales_rep = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role__role="Sales Representative"),
        allow_null=True
        )
    customer_id = serializers.CharField(required=False, allow_blank=True)
    available_limit = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'first_name', 'last_name', 'customer_type', 'customer_id',
            'status', 'assigned_sales_rep', 'email', 'phone_number', 'address',
            'street', 'city', 'state', 'zip_code', 'country', 'company_name',
            'industry', 'location', 'gst_tax_id', 'credit_limit', 'available_limit',
            'billing_address', 'shipping_address', 'payment_terms', 'credit_term',
            'last_edit_date'
        ]

    def create(self, validated_data):
        if not validated_data.get('customer_id'):
            validated_data['customer_id'] = self._generate_customer_id()
        if 'available_limit' not in validated_data or validated_data['available_limit'] is None:
            validated_data['available_limit'] = 0.00
        return super().create(validated_data)

    def _generate_customer_id(self):
        last_customer = Customer.objects.order_by('-id').first()
        if last_customer:
            last_id = int(last_customer.customer_id.replace('CUS', '')) + 1
        else:
            last_id = 1
        return f'CUS{last_id:04d}'
    
from rest_framework import serializers
from .models import Supplier, SupplierComment, SupplierAttachment


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class SupplierCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        exclude = [
            "supplier_id", "created_at", "updated_at", "created_by"
        ]


class SupplierCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierComment
        fields = "__all__"
        read_only_fields = ["timestamp"]


class SupplierAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAttachment
        fields = "__all__"
        read_only_fields = ["uploaded_at"]
