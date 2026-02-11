import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from django.contrib.auth import authenticate

from core.permissions import RoleBasedPermission
from .models import Customer
from .serializers import CustomerSerializer
import pandas as pd


from .models import (
    CustomUser, Branch, Department, Role, Category, TaxCode, UOM, Warehouse,
    Size, Color, Supplier, Product, Customer,SupplierHistory,SupplierAttachment,SupplierComment,ProductSupplier
)
from .serializers import (
    
     CategorySerializer, TaxCodeSerializer, UOMSerializer,
    WarehouseSerializer, SizeSerializer, ColorSerializer, SupplierSerializer, ProductSerializer,
    CustomerSerializer,Supplier,SupplierHistory
)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from core.permissions import RoleBasedPermission  # ← your real RBAC permission
from .models import CustomUser, Branch, Department, Role
from .serializers import (
    CustomUserCreateSerializer, CustomUserDetailSerializer, CustomUserUpdateSerializer,
    BranchSerializer,
    DepartmentListSerializer, DepartmentDetailSerializer,
    DepartmentCreateWithRolesSerializer, DepartmentUpdateWithRolesSerializer,DepartmentDropdownSerializer,
    RoleReadSerializer,  # only read serializer for roles
)

from core.serializers import Candidate,CandidateSerializer,CandidateDocumentSerializer
logger = logging.getLogger(__name__)


# Custom pagination if you want different sizes per view
class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'per_page'
    max_page_size = 100


# ────────────────────────────────────────────────
# Users Management
# ────────────────────────────────────────────────
class ManageUsersListCreateView(generics.ListCreateAPIView):
    """
    List all users (paginated, searchable) + Create new user (admin only)
    """
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomUserCreateSerializer
        return CustomUserDetailSerializer

    def get_queryset(self):
        qs = CustomUser.objects.select_related('branch', 'department', 'role').order_by('id')
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(role__role__icontains=search) |
                Q(department__department_name__icontains=search) |
                Q(branch__name__icontains=search)
            )
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Users fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance

        # Your existing email logic remains unchanged
        password = get_random_string(length=8, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*')
        instance.set_password(password)
        instance.save(update_fields=['password'])

        context = {
            'first_name': instance.first_name or "User",
            'email': instance.email,
            'password': password,
            'site_name': 'Stackly ERP',
            'site_link': settings.FRONTEND_URL.rstrip('/') + '/login',
            'expiry_hours': 24,
        }

        subject = 'Welcome to Stackly ERP - Your Account Credentials'
        html_message = render_to_string('emails/user_registration.html', context)

        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[instance.email],
        )
        email.content_subtype = 'html'

        try:
            email.send(fail_silently=False)
            logger.info(f"Welcome email sent successfully to {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {instance.email}: {str(e)}")

        return Response({
            "message": "User created successfully",
            "data": CustomUserDetailSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class ManageUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CustomUserUpdateSerializer
        return CustomUserDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "User fetched successfully",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "User updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "User deleted successfully"
        })

# ────────────────────────────────────────────────
# Branches
# ────────────────────────────────────────────────

class BranchListCreateView(generics.ListCreateAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Branches fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Branch created successfully"
        }, status=status.HTTP_201_CREATED)


class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Branch fetched successfully",
            "data": serializer.data
        })

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Branch updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Branch deleted successfully"
        })


# ────────────────────────────────────────────────
# Departments (with nested roles support)
# ────────────────────────────────────────────────

class DepartmentListView(generics.ListAPIView):
    serializer_class = DepartmentListSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Department.objects.select_related('branch').all()
        branch_id = self.request.query_params.get('branch')
        search = self.request.query_params.get('search')
        dropdown = self.request.query_params.get('dropdown', 'false').lower() == 'true'

        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(department_name__icontains=search)
            )

        self.dropdown_mode = dropdown
        return qs

    def get_serializer_class(self):
        if getattr(self, 'dropdown_mode', False):
            return DepartmentDropdownSerializer
        return DepartmentListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['include_roles'] = self.request.query_params.get('include_roles', 'true').lower() == 'true'
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Departments fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })


class DepartmentCreateView(generics.CreateAPIView):
    serializer_class = DepartmentCreateWithRolesSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Department created successfully",
            "data": DepartmentDetailSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.select_related('branch').all()
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DepartmentUpdateWithRolesSerializer
        return DepartmentDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Department fetched successfully",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Department updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Department deleted successfully"
        })


# ────────────────────────────────────────────────
# Roles – READ-ONLY (no create/update/delete)
# ────────────────────────────────────────────────

class RoleListView(generics.ListAPIView):
    serializer_class = RoleReadSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Role.objects.select_related('department', 'branch').all()
        department_id = self.request.query_params.get('department')
        if department_id:
            qs = qs.filter(department_id=department_id)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Roles fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })


class RoleDetailView(generics.RetrieveAPIView):
    queryset = Role.objects.select_related('department', 'branch').all()
    serializer_class = RoleReadSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Role fetched successfully",
            "data": serializer.data
        })




from .models import (
    Product, Category, TaxCode, UOM, Warehouse, Size, Color, ProductSupplier
)
from .serializers import (
    ProductSerializer, CategorySerializer, TaxCodeSerializer, UOMSerializer,
    WarehouseSerializer, SizeSerializer, ColorSerializer, ProductSupplierSerializer
)




# ────────────────────────────────────────────────
# Product Views
# ────────────────────────────────────────────────
from rest_framework import generics, status
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Product
from .serializers import ProductSerializer  # assuming this is your main serializer


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related(
        'category', 'tax_code', 'uom', 'warehouse', 'size', 'color', 'supplier'
    ).prefetch_related('related_products')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(product_id__icontains=search) |
                Q(description__icontains=search) |
                Q(category__name__icontains=search) |
                Q(supplier__name__icontains=search)
            )
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Products fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Product created successfully",
            "data": ProductSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, Update, Delete single Product
    """
    queryset = Product.objects.select_related(
        'category', 'tax_code', 'uom', 'warehouse', 'size', 'color', 'supplier'
    ).prefetch_related('related_products')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Product fetched successfully",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Product updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Product deleted successfully"
        })


# ────────────────────────────────────────────────
# Category Views
# ────────────────────────────────────────────────

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Categories fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Category created successfully",
            "data": CategorySerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Category fetched successfully",
            "data": serializer.data
        })
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Category updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Category deleted successfully"
        })


# ────────────────────────────────────────────────
# TaxCode Views
# ────────────────────────────────────────────────

class TaxCodeListCreateView(generics.ListCreateAPIView):
    queryset = TaxCode.objects.all()
    serializer_class = TaxCodeSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Tax Codes fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Tax Code created successfully",
            "data": TaxCodeSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class TaxCodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TaxCode.objects.all()
    serializer_class = TaxCodeSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Tax Code fetched successfully",
            "data": serializer.data
        })
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Tax Code updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Tax Code deleted successfully"
        })


# ────────────────────────────────────────────────
# UOM Views
# ────────────────────────────────────────────────

class UOMListCreateView(generics.ListCreateAPIView):
    queryset = UOM.objects.all()
    serializer_class = UOMSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "UOMs fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "UOM created successfully",
            "data": UOMSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class UOMDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UOM.objects.all()
    serializer_class = UOMSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "UOM fetched successfully",
            "data": serializer.data
        })
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "UOM updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "UOM deleted successfully"
        })


# ────────────────────────────────────────────────
# Warehouse Views
# ────────────────────────────────────────────────

class WarehouseListCreateView(generics.ListCreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Warehouses fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Warehouse created successfully",
            "data": WarehouseSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Warehouse fetched successfully",
            "data": serializer.data
        })
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Warehouse updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Warehouse deleted successfully"
        })


# ────────────────────────────────────────────────
# Size Views
# ────────────────────────────────────────────────

class SizeListCreateView(generics.ListCreateAPIView):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Sizes fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Size created successfully",
            "data": SizeSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class SizeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Size fetched successfully",
            "data": serializer.data
        })
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Size updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Size deleted successfully"
        })


# ────────────────────────────────────────────────
# Color Views
# ────────────────────────────────────────────────

class ColorListCreateView(generics.ListCreateAPIView):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Colors fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Color created successfully",
            "data": ColorSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class ColorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Color fetched successfully",
            "data": serializer.data
        })
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Color updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Color deleted successfully"
        })


# ────────────────────────────────────────────────
# ProductSupplier Views
# ────────────────────────────────────────────────

class ProductSupplierListCreateView(generics.ListCreateAPIView):
    queryset = ProductSupplier.objects.all()
    serializer_class = ProductSupplierSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Product Suppliers fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Product Supplier created successfully",
            "data": ProductSupplierSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class ProductSupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductSupplier.objects.all()
    serializer_class = ProductSupplierSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Product Supplier fetched successfully",
            "data": serializer.data
        })
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Product Supplier updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Product Supplier deleted successfully"
        })
    

class ProductImportView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded'}, status=400)

        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Unsupported file format'}, status=400)
        except Exception as e:
            return Response({'error': f'File read error: {str(e)}'}, status=400)

        # Required columns
        required = ['name', 'product_type', 'unit_price', 'quantity', 'stock_level', 'status', 'product_usage']

        missing = [col for col in required if col not in df.columns]
        if missing:
            return Response({'error': f'Missing columns: {", ".join(missing)}'}, status=400)

        valid_rows = []
        invalid_rows = []
        skipped_rows = []

        seen_names = set()

        for index, row in df.iterrows():
            row_dict = row.to_dict()

            if all(pd.isna(v) or v == '' for v in row_dict.values()):
                skipped_rows.append(index + 1)
                continue

            missing_in_row = [col for col in required if pd.isna(row_dict.get(col)) or row_dict.get(col) == '']
            if missing_in_row:
                invalid_rows.append({
                    'row': index + 1,
                    'errors': [f"{col} is required" for col in missing_in_row]
                })
                continue

            name = str(row_dict.get('name', '')).strip()
            if name in seen_names:
                skipped_rows.append(index + 1)
                continue

            seen_names.add(name)

            data = {
                'name': name,
                'product_type': row_dict.get('product_type', ''),
                'description': row_dict.get('description', ''),
                'unit_price': float(row_dict.get('unit_price', 0)),
                'discount': float(row_dict.get('discount', 0)),
                'quantity': int(row_dict.get('quantity', 0)),
                'stock_level': int(row_dict.get('stock_level', 0)),
                'reorder_level': int(row_dict.get('reorder_level', 0)),
                'weight': row_dict.get('weight', ''),
                'specifications': row_dict.get('specifications', ''),
                'status': row_dict.get('status', 'Active'),
                'product_usage': row_dict.get('product_usage', 'Both'),
                'sub_category': row_dict.get('sub_category', ''),
                # Add foreign keys if in CSV (IDs)
                'category': row_dict.get('category', None),
                'tax_code': row_dict.get('tax_code', None),
                'uom': row_dict.get('uom', None),
                'warehouse': row_dict.get('warehouse', None),
                'size': row_dict.get('size', None),
                'color': row_dict.get('color', None),
                'supplier': row_dict.get('supplier', None),
            }

            serializer = ProductSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                valid_rows.append(data)
            else:
                invalid_rows.append({
                    'row': index + 1,
                    'errors': serializer.errors
                })

        return Response({
            'valid_count': len(valid_rows),
            'invalid_count': len(invalid_rows),
            'skipped_count': len(skipped_rows),
            'invalid_rows': invalid_rows,
            'message': 'Validation complete. Click Import to save valid rows.'
        }, status=200)


class ProductImportConfirmView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    @transaction.atomic
    def post(self, request):
        valid_rows = request.data.get('valid_rows', [])

        if not valid_rows:
            return Response({'error': 'No valid rows'}, status=400)

        created = []
        errors = []

        for row in valid_rows:
            serializer = ProductSerializer(data=row, context={'request': request})
            if serializer.is_valid():
                product = serializer.save()
                created.append(ProductSerializer(product).data)
            else:
                errors.append(serializer.errors)

        return Response({
            'created_count': len(created),
            'error_count': len(errors),
            'created': created,
            'errors': errors,
            'message': 'Import complete. Review product data.'
        }, status=201)

from rest_framework import generics, status
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Customer
from .serializers import CustomerSerializer  # assuming this is your main serializer


class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all().order_by('-last_edit_date')
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(company_name__icontains=search) |
                Q(customer_id__icontains=search)
            )
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Customers fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Customer created successfully",
            "data": CustomerSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Customer fetched successfully",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Customer updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Customer deleted successfully"
        })




class CustomerImportView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        # Read file (support CSV and Excel)
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Unsupported file format. Use CSV or Excel'}, status=400)
        except Exception as e:
            return Response({'error': f'File read error: {str(e)}'}, status=400)

        # Required columns (must match frontend template)
        required_columns = [
            'first_name', 'email', 'phone_number', 'customer_type', 'status'
        ]
        optional_columns = [
            'last_name', 'address', 'street', 'city', 'state', 'zip_code', 'country',
            'company_name', 'industry', 'location', 'gst_tax_id', 'credit_limit',
            'billing_address', 'shipping_address', 'payment_terms', 'credit_term'
        ]

        # Check missing required columns
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return Response({'error': f'Missing required columns: {", ".join(missing)}'}, status=400)

        valid_rows = []
        invalid_rows = []
        skipped_rows = []

        seen_emails = set()

        for index, row in df.iterrows():
            row_dict = row.to_dict()

            # Skip empty rows
            if all(pd.isna(val) or val == '' for val in row_dict.values()):
                skipped_rows.append(index + 1)
                continue

            # Check required fields
            missing_in_row = [col for col in required_columns if pd.isna(row_dict.get(col)) or row_dict.get(col) == '']
            if missing_in_row:
                invalid_rows.append({
                    'row': index + 1,
                    'errors': [f"{col} is required" for col in missing_in_row]
                })
                continue

            # Email uniqueness check (in-memory + DB)
            email = str(row_dict.get('email', '')).strip()
            if not email:
                invalid_rows.append({'row': index + 1, 'errors': ['Email is required']})
                continue

            if email in seen_emails or Customer.objects.filter(email=email).exists():
                skipped_rows.append(index + 1)
                continue

            seen_emails.add(email)

            # Prepare data for serializer
            data = {
                'first_name': row_dict.get('first_name', ''),
                'last_name': row_dict.get('last_name', ''),
                'customer_type': row_dict.get('customer_type', ''),
                'email': email,
                'phone_number': str(row_dict.get('phone_number', '')),
                'status': row_dict.get('status', 'Active'),
                'address': row_dict.get('address', ''),
                'street': row_dict.get('street', ''),
                'city': row_dict.get('city', ''),
                'state': row_dict.get('state', ''),
                'zip_code': row_dict.get('zip_code', ''),
                'country': row_dict.get('country', 'India'),
                'company_name': row_dict.get('company_name', ''),
                'industry': row_dict.get('industry', ''),
                'location': row_dict.get('location', ''),
                'gst_tax_id': row_dict.get('gst_tax_id', ''),
                'credit_limit': float(row_dict.get('credit_limit', 0.00)),
                'billing_address': row_dict.get('billing_address', ''),
                'shipping_address': row_dict.get('shipping_address', ''),
                'payment_terms': row_dict.get('payment_terms', ''),
                'credit_term': row_dict.get('credit_term', ''),
            }

            # Validate with serializer
            serializer = CustomerSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                valid_rows.append(data)
            else:
                invalid_rows.append({
                    'row': index + 1,
                    'errors': serializer.errors
                })

        return Response({
            'valid_count': len(valid_rows),
            'invalid_count': len(invalid_rows),
            'skipped_count': len(skipped_rows),
            'invalid_rows': invalid_rows,
            'message': 'Validation complete. Click Import to save valid rows.'
        }, status=status.HTTP_200_OK)


class CustomerImportConfirmView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    @transaction.atomic
    def post(self, request):
        valid_rows = request.data.get('valid_rows', [])

        if not valid_rows:
            return Response({'error': 'No valid rows to import'}, status=400)

        created = []
        errors = []

        for row in valid_rows:
            serializer = CustomerSerializer(data=row, context={'request': request})
            if serializer.is_valid():
                customer = serializer.save()
                created.append(CustomerSerializer(customer).data)
            else:
                errors.append(serializer.errors)

        return Response({
            'created_count': len(created),
            'error_count': len(errors),
            'created': created,
            'errors': errors,
            'message': 'Import complete. Review billing and shipping addresses.'
        }, status=status.HTTP_201_CREATED)

# class CustomerSummaryView(APIView):
#     permission_classes = [IsAuthenticated, RoleBasedPermission]

#     def get(self, request):
#         customers = Customer.objects.all()
#         summary = {
#             'active': customers.filter(status='Active').count(),
#             'inactive': customers.filter(status='Inactive').count(),
#             'total_credit_limit': customers.aggregate(total=models.Sum('credit_limit'))['total'] or 0,
#             'total_available_limit': customers.aggregate(total=models.Sum('available_limit'))['total'] or 0,
#             'sales_reps': CustomUser.objects.filter(role__role="Sales Representative").count()
#         }
#         return Response(summary, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from django.db import transaction
from .models import Customer
from .serializers import CustomerSerializer

from fuzzywuzzy import fuzz
from django.db.models import Q

class CustomerDuplicatesListView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get(self, request):
        # Get all active customers
        customers = Customer.objects.filter(is_active=True).select_related('assigned_sales_rep')

        duplicate_groups = []

        # Group by similar names (fuzzy match)
        name_groups = {}
        for c in customers:
            full_name = f"{c.first_name} {c.last_name or ''}".strip().lower()
            company = (c.company_name or "").strip().lower()

            key = full_name if full_name else company
            if not key:
                continue

            found = False
            for existing_key, group in name_groups.items():
                similarity = fuzz.token_sort_ratio(key, existing_key)
                if similarity > 85:  # adjust threshold
                    group.append(c)
                    found = True
                    break

            if not found:
                name_groups[key] = [c]

        # Build groups with more than 1 customer
        for group in name_groups.values():
            if len(group) > 1:
                primary = group[0]  # oldest or first
                duplicates = group[1:]

                group_data = {
                    'primary': CustomerSerializer(primary).data,
                    'duplicates': CustomerSerializer(duplicates, many=True).data,
                    'matching_fields': ['Name', 'Company Name'],
                    'potential_conflicts': ['Email', 'Phone', 'Address', 'GST ID']
                }
                duplicate_groups.append(group_data)

        return Response({
            'duplicate_groups': duplicate_groups,
            'total_groups': len(duplicate_groups),
            'message': 'Potential duplicates based on name/company similarity'
        }, status=200)


class CustomerMergeReviewView(APIView):
    """
    Returns detailed side-by-side comparison for selected primary + duplicates
    """
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request):
        primary_id = request.data.get('primary_id')
        duplicate_ids = request.data.get('duplicate_ids', [])

        if not primary_id or not duplicate_ids:
            return Response({'error': 'Primary ID and at least one duplicate ID required'}, status=400)

        try:
            primary = Customer.objects.get(id=primary_id)
            duplicates = Customer.objects.filter(id__in=duplicate_ids)

            if not duplicates.exists():
                return Response({'error': 'No valid duplicates found'}, status=400)

            # Build side-by-side fields for review
            fields_to_compare = [
                'first_name', 'last_name', 'email', 'phone_number', 'company_name',
                'address', 'street', 'city', 'state', 'zip_code', 'country',
                'gst_tax_id', 'credit_limit', 'billing_address', 'shipping_address'
            ]

            comparison = []
            for field in fields_to_compare:
                primary_val = getattr(primary, field, None)
                duplicate_vals = [getattr(d, field, None) for d in duplicates]

                comparison.append({
                    'field': field.replace('_', ' ').title(),
                    'primary_value': primary_val,
                    'duplicate_values': duplicate_vals,
                    'conflict': len(set([v for v in duplicate_vals if v is not None])) > 1 or primary_val != duplicate_vals[0] if duplicate_vals else False
                })

            return Response({
                'primary': CustomerSerializer(primary).data,
                'duplicates': CustomerSerializer(duplicates, many=True).data,
                'comparison': comparison
            }, status=200)
        except Customer.DoesNotExist:
            return Response({'error': 'Primary or duplicate not found'}, status=404)


class CustomerMergeConfirmView(APIView):
    """
    Performs the actual merge based on user choices
    """
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    @transaction.atomic
    def post(self, request):
        primary_id = request.data.get('primary_id')
        duplicate_ids = request.data.get('duplicate_ids', [])
        field_choices = request.data.get('field_choices', {})  # e.g. {"phone_number": "left", "address": "right"}

        if not primary_id or not duplicate_ids:
            return Response({'error': 'Primary ID and duplicate IDs required'}, status=400)

        try:
            primary = Customer.objects.get(id=primary_id)
            duplicates = Customer.objects.filter(id__in=duplicate_ids)

            if not duplicates.exists():
                return Response({'error': 'No valid duplicates'}, status=400)

            # Merge logic: apply user choices for conflicts
            for field, choice in field_choices.items():
                if choice == 'left':
                    value = getattr(primary, field)
                else:
                    # Take from first duplicate (or implement more logic)
                    value = getattr(duplicates.first(), field)
                setattr(primary, field, value)

            primary.save()

            # Delete duplicates
            duplicates.delete()

            return Response({
                'message': 'Merge successful',
                'primary': CustomerSerializer(primary).data
            }, status=200)
        except Customer.DoesNotExist:
            return Response({'error': 'Primary or duplicate not found'}, status=404)
        


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import RoleBasedPermission
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.mail import EmailMessage
import os

from .models import Supplier, SupplierComment, SupplierAttachment
from .serializers import (
    SupplierSerializer, SupplierCreateUpdateSerializer,
    SupplierCommentSerializer, SupplierAttachmentSerializer,SupplierHistorySerializer
)
from rest_framework.parsers import MultiPartParser, FormParser

class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'per_page'
    max_page_size = 100
class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all().order_by('-created_at')
    serializer_class = SupplierCreateUpdateSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(supplier_id__icontains=search) |
                Q(supplier_name__icontains=search) |
                Q(tax_id__icontains=search)
            )
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = SupplierSerializer(page, many=True)  # Use full serializer for list

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Suppliers fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response({
            "message": "Supplier created successfully",
            "data": SupplierSerializer(instance).data
        }, status=status.HTTP_201_CREATED)


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all()
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return SupplierSerializer  # full details for GET
        return SupplierCreateUpdateSerializer  # input for PATCH/PUT

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Supplier fetched successfully",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Supplier updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.workflow_status != 'Draft':
            return Response({'message': "Cannot delete submitted suppliers"}, status=403)
        instance.delete()
        return Response({
            "message": "Supplier deleted successfully"
        })


class SupplierPDFView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        if supplier.workflow_status != 'Submitted':
            return Response({'message': 'PDF only available after submission'}, status=403)

        context = {
            'supplier': supplier,
            'comments': supplier.comments.all(),
            'attachments': supplier.extra_attachments.all(),
            'history': supplier.history.all()
        }

        html_string = render_to_string('emails/supplier_pdf.html', context)
        html = HTML(string=html_string)
        pdf = html.write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Supplier_{supplier.supplier_id}.pdf"'
        return response


class SupplierEmailView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        if supplier.workflow_status != 'Submitted':
            return Response({'message': 'Email only available after submission'}, status=403)

        email = request.data.get('email')
        if not email:
            return Response({'message': 'Email is required'}, status=400)

        html_content = render_to_string('emails/supplier_email.html', {'supplier': supplier})
        msg = EmailMessage(f"Supplier {supplier.supplier_id}", html_content, to=[email])
        msg.content_subtype = "html"
        msg.send()

        return Response({"message": "Email sent successfully"})


class SupplierCommentView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get(self, request, pk):
        comments = SupplierComment.objects.filter(supplier_id=pk)
        serializer = SupplierCommentSerializer(comments, many=True)
        return Response({
            "message": "Comments fetched successfully",
            "data": serializer.data
        })

    def post(self, request, pk):
        data = request.data.copy()
        data["supplier"] = pk
        data["commented_by"] = request.user.id

        serializer = SupplierCommentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message": "Comment added successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class SupplierAttachmentView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, pk):
        attachments = SupplierAttachment.objects.filter(supplier_id=pk)
        serializer = SupplierAttachmentSerializer(attachments, many=True)
        return Response({
            "message": "Attachments fetched successfully",
            "data": serializer.data
        })

    def post(self, request, pk):
        data = request.data.copy()
        data["supplier"] = pk
        data["uploaded_by"] = request.user.id

        serializer = SupplierAttachmentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message": "Attachment uploaded successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class SupplierHistoryView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get(self, request, pk):
        history = SupplierHistory.objects.filter(supplier_id=pk)
        serializer = SupplierHistorySerializer(history, many=True)
        return Response({
            "message": "History fetched successfully",
            "data": serializer.data
        })