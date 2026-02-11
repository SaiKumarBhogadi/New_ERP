from rest_framework import serializers
from django.db import transaction
import re
import logging

from .models import (
    CustomUser, Branch, Department, Role,
    Category, TaxCode, UOM, Warehouse, Size, Color, ProductSupplier, Product, Customer ,Supplier,SupplierAttachment,SupplierComment,SupplierHistory # commented until needed
)
from django.utils.crypto import get_random_string
logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────
# Shared validation helpers (DRY)
# ────────────────────────────────────────────────

def validate_letters_space(value, field_name="Field"):
    if not re.match(r'^[A-Za-z ]+$', value):
        raise serializers.ValidationError(f"{field_name} can contain only letters and spaces.")
    return value


def validate_alphanumeric(value, field_name="Field"):
    if not re.match(r'^[A-Za-z0-9]+$', value):
        raise serializers.ValidationError(f"{field_name} can contain only letters and numbers.")
    return value


def validate_alphanumeric_space(value, field_name="Field"):
    if not re.match(r'^[A-Za-z0-9 ]+$', value):
        raise serializers.ValidationError(f"{field_name} can contain only letters, numbers and spaces.")
    return value


def validate_description(value):
    if value and len(value) > 500:
        raise serializers.ValidationError("Description cannot exceed 500 characters.")
    return value


def validate_permissions(value):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise serializers.ValidationError("Permissions must be a valid JSON object (dictionary).")
    return value


# ────────────────────────────────────────────────
# Branch
# ────────────────────────────────────────────────

class BranchSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate_name(self, value):
        qs = Branch.objects.filter(name__iexact=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Branch with this name already exists.")

        return value
    
    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


# ────────────────────────────────────────────────
# Department – read & dropdown
# ────────────────────────────────────────────────

class DepartmentDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'department_name']


class DepartmentBaseSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'code', 'department_name', 'description', 'branch']


# ────────────────────────────────────────────────
# Role – read-only serializers only
# ────────────────────────────────────────────────

class RoleReadSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    branch_name     = serializers.CharField(source='branch.name', read_only=True)
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id', 'role', 'description', 'permissions',
            'department_name', 'branch_name',
            'is_active', 'created_at', 'updated_at' ,'created_by', 'updated_by',
        ]
    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


# ────────────────────────────────────────────────
# Nested Role (only used inside Department)
# ────────────────────────────────────────────────

class NestedRoleSerializer(serializers.ModelSerializer):
    """
    Used for both create & update inside department payload
    id is accepted but ignored on create / full-replace
    """
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Role
        fields = ['id', 'role', 'description', 'permissions']

    def validate_role(self, value):
        return validate_alphanumeric_space(value, "Role name")

    def validate_description(self, value):
        return validate_description(value)

    def validate_permissions(self, value):
        return validate_permissions(value)


# ────────────────────────────────────────────────
# Department with nested roles – main serializers for create & update
# ────────────────────────────────────────────────

class DepartmentCreateWithRolesSerializer(serializers.ModelSerializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    roles  = NestedRoleSerializer(many=True, required=False, allow_empty=True)

    class Meta:
        model = Department
        fields = ['code', 'department_name', 'description', 'branch', 'roles']

    def validate_department_name(self, value):
        return validate_letters_space(value, "Department name")

    def validate_code(self, value):
        return validate_alphanumeric(value, "Department code")

    def validate_description(self, value):
        return validate_description(value)

    @transaction.atomic
    def create(self, validated_data):
        roles_data = validated_data.pop('roles', [])
        department = Department.objects.create(
            **validated_data,
            created_by=self.context['request'].user,
            updated_by=self.context['request'].user
        )


        for role_data in roles_data:
            role_data.pop('id', None)  # ignore any sent id
            Role.objects.create(
                department=department,
                branch=department.branch,
                created_by=self.context['request'].user,
                updated_by=self.context['request'].user,
                **role_data
            )


        return department


class DepartmentUpdateWithRolesSerializer(serializers.ModelSerializer):
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=False
    )
    roles = NestedRoleSerializer(many=True, required=False, allow_empty=True)
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    class Meta:
        model = Department
        fields = [
            'id',               # include so it shows in response
            'code',
            'department_name',
            'description',
            'branch',
            'is_active',        # if you have this field
            'created_at',
            'updated_at',
            'roles', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def validate_department_name(self, value):
        return validate_letters_space(value, "Department name")

    def validate_code(self, value):
        return validate_alphanumeric(value, "Department code")

    def validate_description(self, value):
        return validate_description(value)
    
    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None

    @transaction.atomic
    def update(self, instance, validated_data):
        roles_data = validated_data.pop('roles', None)

        # Update department scalar fields (partial update)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = self.context['request'].user
        instance.save()

        # Sync roles if provided (add new, update existing, delete missing)
        if roles_data is not None:
            sent_role_ids = []
            for role_data in roles_data:
                role_id = role_data.pop('id', None)
                if role_id:
                    # Update existing
                    try:
                        role = Role.objects.get(id=role_id, department=instance)
                        for k, v in role_data.items():
                            setattr(role, k, v)
                        role.updated_by = self.context['request'].user
                        role.save()
                        sent_role_ids.append(role_id)
                    except Role.DoesNotExist:
                        logger.warning(f"Role ID {role_id} not found or not in department {instance.id}")
                else:
                    # Create new
                    new_role = Role.objects.create(
                        department=instance,
                        branch=instance.branch,
                        created_by=self.context['request'].user,
                        updated_by=self.context['request'].user,
                        **role_data
                    )

                    sent_role_ids.append(new_role.id)

            # Delete roles not in the sent list
            Role.objects.filter(department=instance).exclude(id__in=sent_role_ids).delete()

        # Return the instance (DRF will re-serialize it with all fields)
        return instance


# ────────────────────────────────────────────────
# Department list/detail serializers (read)
# ────────────────────────────────────────────────

class DepartmentListSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)
    roles  = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'code', 'department_name', 'description', 'branch', 'roles', 'created_by' , 'updated_by' ]

    def get_roles(self, obj):
        if self.context.get('include_roles', True):
            return RoleReadSerializer(obj.roles.all(), many=True).data
        return []
    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class DepartmentDetailSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)
    roles  = RoleReadSerializer(many=True, read_only=True)
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'code', 'department_name', 'description', 'branch', 'roles', 'created_by' , 'updated_by' ]

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None
# ────────────────────────────────────────────────
# CustomUser serializers
# ────────────────────────────────────────────────

class CustomUserDetailSerializer(serializers.ModelSerializer):
    branch            = BranchSerializer(read_only=True)
    department        = DepartmentListSerializer(read_only=True)
    role              = RoleReadSerializer(read_only=True)
    available_branches = BranchSerializer(many=True, read_only=True)
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    reporting_to= serializers.StringRelatedField(read_only=True)  # Shows __str__ (email) — or change to get_full_name if you have it

    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email', 'contact_number',
            'branch', 'department', 'role', 'available_branches',
            'reporting_to', 'employee_id', 'profile_pic','created_by', 'updated_by'
        ]
    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class CustomUserCreateSerializer(serializers.ModelSerializer):
    available_branches = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        many=True,
        required=False
    )
    reporting_to = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=False,
        allow_null=True
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=False,
        allow_null=True
    )
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'contact_number',
            'branch', 'department', 'role',
            'reporting_to', 'available_branches',
            'employee_id', 'profile_pic'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'last_name': {'required': False, 'allow_blank': True},
        }

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_employee_id(self, value):
        if value and CustomUser.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("Employee ID must be unique.")
        return value

    def validate_contact_number(self, value):
        if value:
            cleaned = value.replace("+", "").replace("-", "").replace(" ", "")
            if not cleaned.isdigit():
                raise serializers.ValidationError("Contact number must contain only digits, +, -, or spaces.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        # Pop all special fields
        branches = validated_data.pop('available_branches', [])
        reporting_to = validated_data.pop('reporting_to', None)
        branch = validated_data.pop('branch', None)
        department = validated_data.pop('department', None)
        role = validated_data.pop('role', None)

        # Generate password if not provided
        password = validated_data.pop('password', None)
        if not password:
            password = get_random_string(length=8, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*')

        # Create user with password (this hashes it automatically)
        user = CustomUser.objects.create_user(
            email=validated_data.pop('email'),
            password=password,  # ← passed here — hashed in manager
            **validated_data
        )

        # Explicitly set FKs (safety net)
        user.created_by = self.context['request'].user
        user.updated_by = self.context['request'].user
        user.branch = branch
        user.department = department
        user.role = role
        user.reporting_to = reporting_to
        user.save()

        # Set M2M
        if branches:
            user.available_branches.set(branches)

        # Return user (for email in view)
        return user

class CustomUserUpdateSerializer(serializers.ModelSerializer):
    available_branches = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        many=True,
        required=False
    )

    reporting_to = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'contact_number',
            'branch', 'department', 'role',
            'reporting_to', 'available_branches',
            'employee_id', 'profile_pic'
        ]
        extra_kwargs = {
            'email': {'required': False},
            'first_name': {'required': False},
        }

    def validate_role(self, value):
        if self.instance and self.instance.role:
            if self.instance.role.role.lower() == 'admin':
                if value and value.role.lower() != 'admin':
                    # Only Django superuser can downgrade an Admin
                    if not self.context['request'].user.is_superuser:
                        raise serializers.ValidationError(
                            "Cannot remove 'Admin' role unless you are a Django superuser."
                        )
        return value

    def validate_email(self, value):
        if self.instance and self.instance.email == value:
            return value
        if CustomUser.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_employee_id(self, value):
        if value and self.instance and self.instance.employee_id == value:
            return value
        if value and CustomUser.objects.filter(employee_id=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Employee ID must be unique.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        branches = validated_data.pop('available_branches', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = self.context['request'].user
        instance.save()

        if branches is not None:
            instance.available_branches.set(branches)

        return instance
    


from rest_framework import serializers
from .models import Category, TaxCode, UOM, Warehouse, Size, Color, ProductSupplier, Product


class CategorySerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class TaxCodeSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = TaxCode
        fields = ['id', 'name', 'percentage', 'description', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class UOMSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = UOM
        fields = ['id', 'name', 'items', 'description', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class WarehouseSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'location', 'manager_name', 'contact_info', 'notes', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class SizeSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Size
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class ColorSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Color
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class ProductSupplierSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = ProductSupplier
        fields = ['id', 'name', 'contact_person', 'phone_number', 'email', 'address', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None

        
class ProductSerializer(serializers.ModelSerializer):
    
    # Write: accept IDs
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )
    tax_code = serializers.PrimaryKeyRelatedField(
        queryset=TaxCode.objects.all(),
        required=False,
        allow_null=True
    )
    uom = serializers.PrimaryKeyRelatedField(
        queryset=UOM.objects.all(),
        required=False,
        allow_null=True
    )
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        required=False,
        allow_null=True
    )
    size = serializers.PrimaryKeyRelatedField(
        queryset=Size.objects.all(),
        required=False,
        allow_null=True
    )
    color = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(),
        required=False,
        allow_null=True
    )
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=ProductSupplier.objects.all(),
        required=False,
        allow_null=True
    )
    related_products = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        many=True,
        required=False
    )

    # Read: nested for detail view
    category_detail = CategorySerializer(source='category', read_only=True)
    tax_code_detail = TaxCodeSerializer(source='tax_code', read_only=True)
    uom_detail = UOMSerializer(source='uom', read_only=True)
    warehouse_detail = WarehouseSerializer(source='warehouse', read_only=True)
    size_detail = SizeSerializer(source='size', read_only=True)
    color_detail = ColorSerializer(source='color', read_only=True)
    supplier_detail = ProductSupplierSerializer(source='supplier', read_only=True)
    related_products_detail = serializers.SerializerMethodField(read_only=True)

    # Audit fields (read-only)
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    

    class Meta:
        model = Product
        fields = [
            'id', 'product_id', 'name', 'product_type', 'description',
            'category', 'category_detail', 'is_custom_category', 'custom_category',
            'tax_code', 'tax_code_detail', 'is_custom_tax_code', 'custom_tax_code',
            'uom', 'uom_detail', 'is_custom_uom', 'custom_uom',
            'warehouse', 'warehouse_detail', 'is_custom_warehouse', 'custom_warehouse',
            'size', 'size_detail', 'is_custom_size', 'custom_size',
            'color', 'color_detail', 'is_custom_color', 'custom_color',
            'supplier', 'supplier_detail', 'is_custom_supplier', 'custom_supplier',
            'related_products', 'related_products_detail', 'is_custom_related_products', 'custom_related_products',
            'unit_price', 'discount', 'quantity', 'stock_level', 'reorder_level',
            'weight', 'specifications', 'status', 'product_usage', 'image', 'sub_category',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'product_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'category_detail', 'tax_code_detail', 'uom_detail', 'warehouse_detail',
            'size_detail', 'color_detail', 'supplier_detail', 'related_products_detail'
        ]

    def get_related_products_detail(self, obj):
        # Optional: return nested product info for read
        return [{"id": p.id, "name": p.name} for p in obj.related_products.all()]

    def validate(self, data):
        # Only enforce full required fields on creation (POST)
        if self.instance is None:  # ← this means CREATE (no existing instance)
            required = ['name', 'product_type', 'unit_price', 'quantity', 'stock_level', 'status', 'product_usage']
            for field in required:
                if field not in data or not data[field]:
                    raise serializers.ValidationError({
                        field: f"{field.replace('_', ' ').title()} is required"
                    })

        # Custom field validation (always run, but only check if field is sent)
        custom_pairs = [
            ('category', 'custom_category'),
            ('tax_code', 'custom_tax_code'),
            ('uom', 'custom_uom'),
            ('warehouse', 'custom_warehouse'),
            ('size', 'custom_size'),
            ('color', 'custom_color'),
            ('supplier', 'custom_supplier'),
            ('related_products', 'custom_related_products'),
        ]

        for normal, custom in custom_pairs:
            is_custom = data.get(f'is_custom_{normal}', False)
            custom_val = data.get(f'custom_{normal}', '')

            # Only validate if the field is being updated/sent
            if f'is_custom_{normal}' in data or f'custom_{normal}' in data or normal in data:
                if is_custom and not custom_val:
                    raise serializers.ValidationError({
                        f'custom_{normal}': f"Custom {normal.replace('_', ' ').title()} is required when custom is selected"
                    })
                if not is_custom and normal not in data and not self.instance:
                    raise serializers.ValidationError({
                        normal: f"{normal.replace('_', ' ').title()} is required"
                    })

        return data

    @transaction.atomic
    def create(self, validated_data):
        related_products = validated_data.pop('related_products', [])
        # ... pop other fields ...

        product = Product.objects.create(
            **validated_data,
            created_by=self.context['request'].user,
            updated_by=self.context['request'].user
        )

        product.related_products.set(related_products)
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        related_products = validated_data.pop('related_products', None)
        # ... pop other fields ...

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.updated_by = self.context['request'].user  
        instance.save()

        if related_products is not None:
            instance.related_products.set(related_products)

        return instance

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None
    
class CustomerSerializer(serializers.ModelSerializer):
    assigned_sales_rep = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role__role="Sales Representative"),
        allow_null=True,
        required=False
    )
    customer_id = serializers.CharField(required=False, allow_blank=True)
    available_limit = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    
    # Read-only nested for detail view
    assigned_sales_rep_detail = serializers.StringRelatedField(source='assigned_sales_rep', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'first_name', 'last_name', 'customer_type', 'customer_id',
            'status', 'assigned_sales_rep', 'assigned_sales_rep_detail', 'email', 'phone_number', 'address',
            'street', 'city', 'state', 'zip_code', 'country', 'company_name',
            'industry', 'location', 'gst_tax_id', 'credit_limit', 'available_limit',
            'billing_address', 'shipping_address', 'payment_terms', 'credit_term',
            'last_edit_date', 'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'customer_id', 'last_edit_date', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'assigned_sales_rep_detail'
        ]

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None
    
    def validate(self, data):
        # Only enforce required fields on creation (POST)
        if self.instance is None:
            required = ['first_name', 'email', 'phone_number', 'customer_type', 'status']
            for field in required:
                if field not in data or not data[field]:
                    raise serializers.ValidationError({
                        field: f"{field.replace('_', ' ').title()} is required"
                    })

        # Email uniqueness (only check if email is being changed/added)
        if 'email' in data:
            if self.instance and self.instance.email == data['email']:
                pass  # same email → ok
            elif Customer.objects.filter(email=data['email']).exists():
                raise serializers.ValidationError({
                    "email": "A customer with this email already exists."
                })

        return data

    def create(self, validated_data):
        if not validated_data.get('customer_id'):
            last_customer = Customer.objects.order_by('-id').first()
            last_id = int(last_customer.customer_id.replace('CUS', '')) + 1 if last_customer else 1
            validated_data['customer_id'] = f'CUS{last_id:04d}'

        if 'available_limit' not in validated_data or validated_data['available_limit'] is None:
            validated_data['available_limit'] = 0.00

        customer = Customer.objects.create(**validated_data, created_by=self.context['request'].user)
        return customer

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = self.context['request'].user
        instance.save()
        return instance
    

class SupplierSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ['supplier_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class SupplierCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'tax_id', 'supplier_name', 'company_registration_number', 'legal_entity_name',
            'country_of_registration',
            'supplier_type', 'is_custom_supplier_type', 'custom_supplier_type',
            'supplier_tier',
            'status', 'workflow_status', 'product_details',
            'primary_contact_first_name', 'primary_contact_last_name', 'primary_contact_designation',
            'primary_contact_email', 'primary_contact_phone', 'alternate_contact_number', 'website',
            'relationship_manager', 'registered_address', 'mailing_address', 'warehouse_address',
            'billing_address', 'region', 'bank_name', 'bank_account_no', 'iban_swift', 'payment_method',
            'payment_terms', 'is_custom_payment_terms', 'custom_payment_terms', 'currency', 'tax_withholding_setup',
            'categories_served', 'incoterms', 'product_catalog', 'freight_terms', 'min_order_quantity',
            'return_replacement_policy', 'avg_lead_time_days', 'contract_references', 'certifications',
            'compliance_status', 'insurance_documents', 'mitigation_plans', 'risk_rating', 'risk_notes',
            'last_risk_assessment', 'on_time_delivery_rate', 'quality_rating', 'defect_return_rate',
            'last_evaluation_date', 'contract_breaches', 'improvement_plans', 'complaints_registered',
            'external_key_contact', 'interaction_logs', 'dispute_resolutions', 'feedback_surveys',
            'visit_mom_history'
        ]

    def validate(self, data):
        # Required fields only on create (POST)
        if self.instance is None:
            required = [
                'tax_id', 'supplier_name', 'legal_entity_name', 'country_of_registration',
                'primary_contact_first_name', 'primary_contact_email', 'primary_contact_phone',
                'registered_address'
            ]
            for field in required:
                if not data.get(field):
                    raise serializers.ValidationError({
                        field: f"{field.replace('_', ' ').title()} is required"
                    })

        # Custom dropdown validation (run if field is present)
        custom_pairs = [
            ('supplier_type', 'custom_supplier_type'),
            ('payment_terms', 'custom_payment_terms'),
        ]
        for normal, custom in custom_pairs:
            if f'is_custom_{normal}' in data:
                is_custom = data[f'is_custom_{normal}']
                custom_val = data.get(f'custom_{normal}', '')
                normal_val = data.get(normal)

                if is_custom:
                    if not custom_val:
                        raise serializers.ValidationError({
                            f'custom_{normal}': f"Custom {normal.replace('_', ' ').title()} is required when custom is selected"
                        })
                else:
                    if normal in data and not normal_val:
                        raise serializers.ValidationError({
                            normal: f"{normal.replace('_', ' ').title()} is required"
                        })

        # Workflow status validation (always run if present)
        if self.instance:
            old_workflow = self.instance.workflow_status
            new_workflow = data.get('workflow_status', old_workflow)

            if old_workflow == 'Draft' and new_workflow not in ['Draft', 'Submitted']:
                raise serializers.ValidationError({"workflow_status": "Draft can only be saved as Draft or Submitted"})

            if old_workflow == 'Submitted' and new_workflow == 'Draft':
                raise serializers.ValidationError({"workflow_status": "Cannot revert to Draft after submission"})

        # Number validations – only check if the field is actually sent in the request
        if 'avg_lead_time_days' in data and data['avg_lead_time_days'] <= 0:
            raise serializers.ValidationError({"avg_lead_time_days": "Must be positive"})

        if 'on_time_delivery_rate' in data and data['on_time_delivery_rate'] > 100:
            raise serializers.ValidationError({"on_time_delivery_rate": "Cannot exceed 100%"})

        if 'quality_rating' in data and data['quality_rating'] > 5:
            raise serializers.ValidationError({"quality_rating": "Cannot exceed 5.0"})

        if 'defect_return_rate' in data and data['defect_return_rate'] > 100:
            raise serializers.ValidationError({"defect_return_rate": "Cannot exceed 100%"})

        if 'min_order_quantity' in data and data['min_order_quantity'] <= 0:
            raise serializers.ValidationError({"min_order_quantity": "Must be positive"})

        return data

    def create(self, validated_data):
        supplier = Supplier.objects.create(**validated_data, created_by=self.context['request'].user)
        return supplier

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = self.context['request'].user
        instance.save()
        return instance


class SupplierCommentSerializer(serializers.ModelSerializer):
    commented_by = serializers.SerializerMethodField()
    class Meta:
        model = SupplierComment
        fields = '__all__'
        read_only_fields = ['commented_by', 'timestamp']

    def get_commented_by(self, obj):
        return obj.commented_by.get_full_name() if obj.commented_by else None


class SupplierAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = SupplierAttachment
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at']
    
    def get_uploaded_by(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None


class SupplierHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.SerializerMethodField()

    class Meta:
        model = SupplierHistory
        fields = '__all__'
        read_only_fields = ['changed_by', 'changed_at']

    def get_changed_by(self, obj):
        return obj.changed_by.get_full_name() if obj.changed_by else None