from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
import pandas as pd
from django.db.models import Count
from django.db.models import Q

import logging
from .models import (
    CustomUser, Branch, Department, Role, Category, TaxCode, UOM, Warehouse,
    Size, Color, Supplier, Product, Customer
)
from .serializers import (
    CustomUserCreateSerializer, CustomUserDetailSerializer, CustomUserUpdateSerializer,
    BranchSerializer, DepartmentSerializer, DepartmentCreateSerializer, DepartmentDropdownSerializer,
    RoleSerializer, RoleUpdateSerializer, CategorySerializer, TaxCodeSerializer, UOMSerializer,
    WarehouseSerializer, SizeSerializer, ColorSerializer, SupplierSerializer, ProductSerializer,
    CustomerSerializer
)
from core.serializers import Candidate,CandidateSerializer,CandidateDocumentSerializer

from django.template.loader import render_to_string
from django.core.mail import EmailMessage
logger = logging.getLogger(__name__)

class RoleBasedPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

class ManageUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    def get(self, request):
        # Pagination
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))

        # Search
        search = request.query_params.get('search', '').strip()

        users = CustomUser.objects.select_related('role').order_by('id')

        # 🔍 GLOBAL SEARCH (PARTIAL + CASE INSENSITIVE)
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(contact_number__icontains=search) |
                Q(role__name__icontains=search)
            )

        paginator = Paginator(users, per_page)
        page_obj = paginator.get_page(page)

        serializer = CustomUserDetailSerializer(page_obj, many=True)

        return Response({
            'users': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': users.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can add users'}, status=status.HTTP_403_FORBIDDEN)

        password = get_random_string(length=8, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*')
        serializer = CustomUserCreateSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save(password=password)

            context = {
                'first_name': user.first_name,
                'email': user.email,
                'password': password,
                'site_name': 'Stackly ERP',
                'site_link': 'https://yourdomain.com/login'
            }

            email_subject = 'Welcome to Stackly ERP - Your Account Credentials'
            email_body = render_to_string('emails/user_registration.html', context)
            email = EmailMessage(email_subject, email_body, settings.DEFAULT_FROM_EMAIL, [user.email])
            email.content_subtype = 'html'

            try:
                email.send(fail_silently=False)
                logger.info(f"Email sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send email to {user.email}: {str(e)}")
                return Response({'error': 'User created but email failed to send'}, status=status.HTTP_201_CREATED)

            return Response(CustomUserDetailSerializer(user).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ManageUserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    def get(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            serializer = CustomUserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            serializer = CustomUserUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                user = serializer.save()
                return Response(CustomUserDetailSerializer(user).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class BranchListView(APIView):
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    def get(self, request):
        branches = Branch.objects.all()
        serializer = BranchSerializer(branches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            branch = serializer.save()
            return Response(BranchSerializer(branch).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BranchDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    def get(self, request, pk):
        try:
            branch = Branch.objects.get(pk=pk)
            serializer = BranchSerializer(branch)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Branch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            branch = Branch.objects.get(pk=pk)
            serializer = BranchSerializer(branch, data=request.data, partial=True)
            if serializer.is_valid():
                branch = serializer.save()
                return Response(BranchSerializer(branch).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Branch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            branch = Branch.objects.get(pk=pk)
            branch.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Branch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)

class DepartmentListView(APIView):
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 5))
        branch_id = request.query_params.get('branch')
        dropdown = request.query_params.get('dropdown', 'false').lower() == 'true'
        include_roles = request.query_params.get('include_roles', 'false').lower() == 'true'

        departments = Department.objects.all()
        if branch_id:
            try:
                departments = departments.filter(branch_id=branch_id)
            except ValueError:
                return Response({'error': 'Invalid branch ID'}, status=status.HTTP_400_BAD_REQUEST)

        paginator = PageNumberPagination()
        paginator.page_size = per_page
        page_obj = paginator.paginate_queryset(departments, request)

        if dropdown:
            serializer = DepartmentDropdownSerializer(page_obj, many=True)
        else:
            serializer = DepartmentSerializer(page_obj, many=True, context={'include_roles': include_roles})

        return Response({
            'departments': serializer.data,
            'total_pages': paginator.page.paginator.num_pages,
            'current_page': page,
            'total_entries': departments.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DepartmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            department = serializer.save()
            return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DepartmentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    def get(self, request, pk):
        try:
            department = Department.objects.get(pk=pk)
            serializer = DepartmentSerializer(department)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Department.DoesNotExist:
            return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            department = Department.objects.get(pk=pk)
            serializer = DepartmentCreateSerializer(department, data=request.data, partial=True)
            if serializer.is_valid():
                department = serializer.save()
                return Response(DepartmentSerializer(department).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Department.DoesNotExist:
            return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            department = Department.objects.get(pk=pk)
            department.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Department.DoesNotExist:
            return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

class RoleView(APIView):
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        department_id = request.query_params.get('department')

        roles = Role.objects.all().order_by('id')
        if department_id:
            try:
                roles = roles.filter(department_id=department_id)
            except ValueError:
                return Response({'error': 'Invalid department ID'}, status=status.HTTP_400_BAD_REQUEST)

        paginator = PageNumberPagination()
        paginator.page_size = per_page
        page_obj = paginator.paginate_queryset(roles, request)
        serializer = RoleSerializer(page_obj, many=True)

        return Response({
            'roles': serializer.data,
            'total_pages': paginator.page.paginator.num_pages,
            'current_page': page,
            'total_entries': roles.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RoleUpdateSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RoleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    def get(self, request, pk=None):
        if pk:
            try:
                role = Role.objects.get(pk=pk)
                serializer = RoleSerializer(role)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Role.DoesNotExist:
                return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            page = int(request.query_params.get('page', 1))
            per_page = int(request.query_params.get('per_page', 10))
            department_id = request.query_params.get('department')

            roles = Role.objects.all().order_by('id')
            if department_id:
                try:
                    roles = roles.filter(department_id=department_id)
                except ValueError:
                    return Response({'error': 'Invalid department ID'}, status=status.HTTP_400_BAD_REQUEST)

            paginator = PageNumberPagination()
            paginator.page_size = per_page
            page_obj = paginator.paginate_queryset(roles, request)
            serializer = RoleSerializer(page_obj, many=True)

            return Response({
                'roles': serializer.data,
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': page,
                'total_entries': roles.count(),
            }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            serializer = RoleUpdateSerializer(role, data=request.data, partial=True)
            if serializer.is_valid():
                role = serializer.save()
                return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Role.DoesNotExist:
            return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            role.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Role.DoesNotExist:
            return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

class ProductListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        products = Product.objects.all()
        paginator = Paginator(products, per_page)
        page_obj = paginator.get_page(page)
        serializer = ProductSerializer(page_obj, many=True)
        return Response({
            'products': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': products.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can add products'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can edit products'}, status=status.HTTP_403_FORBIDDEN)
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete products'}, status=status.HTTP_403_FORBIDDEN)
        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

class ProductImportView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can import products'}, status=status.HTTP_403_FORBIDDEN)
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        required_fields = ['product_id', 'name', 'product_type', 'category', 'status', 'stock_level', 'unit_price']
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            return Response({'error': f'Missing required fields: {missing_fields}'}, status=status.HTTP_400_BAD_REQUEST)

        valid_rows = []
        invalid_rows = []
        skipped_rows = []

        seen_product_ids = set()
        seen_product_names = set()

        for index, row in df.iterrows():
            if not all(row[field] for field in required_fields):
                invalid_rows.append(index)
                continue

            product_id = str(row['product_id'])
            product_name = str(row['name'])
            if product_id in seen_product_ids or product_name in seen_product_names:
                skipped_rows.append(index)
                continue

            seen_product_ids.add(product_id)
            seen_product_names.add(product_name)
            valid_rows.append(row.to_dict())

        for row in valid_rows:
            serializer = ProductSerializer(data=row)
            if serializer.is_valid():
                serializer.save()
            else:
                invalid_rows.append(row)

        return Response({
            'valid_rows': len(valid_rows),
            'invalid_rows': len(invalid_rows),
            'skipped_rows': len(skipped_rows)
        }, status=status.HTTP_201_CREATED)

class CategoryListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        categories = Category.objects.all()
        paginator = Paginator(categories, per_page)
        page_obj = paginator.get_page(page)
        serializer = CategorySerializer(page_obj, many=True)
        return Response({
            'categories': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': categories.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can add categories'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can edit categories'}, status=status.HTTP_403_FORBIDDEN)
        try:
            category = Category.objects.get(pk=pk)
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete categories'}, status=status.HTTP_403_FORBIDDEN)
        try:
            category = Category.objects.get(pk=pk)
            category.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

class TaxCodeListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        tax_codes = TaxCode.objects.all()
        paginator = Paginator(tax_codes, per_page)
        page_obj = paginator.get_page(page)
        serializer = TaxCodeSerializer(page_obj, many=True)
        return Response({
            'tax_codes': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': tax_codes.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can add tax codes'}, status=status.HTTP_403_FORBIDDEN)
        serializer = TaxCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TaxCodeDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            tax_code = TaxCode.objects.get(pk=pk)
            serializer = TaxCodeSerializer(tax_code)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TaxCode.DoesNotExist:
            return Response({'error': 'Tax code not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can edit tax codes'}, status=status.HTTP_403_FORBIDDEN)
        try:
            tax_code = TaxCode.objects.get(pk=pk)
            serializer = TaxCodeSerializer(tax_code, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TaxCode.DoesNotExist:
            return Response({'error': 'Tax code not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete tax codes'}, status=status.HTTP_403_FORBIDDEN)
        try:
            tax_code = TaxCode.objects.get(pk=pk)
            tax_code.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TaxCode.DoesNotExist:
            return Response({'error': 'Tax code not found'}, status=status.HTTP_404_NOT_FOUND)

class UOMListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        uoms = UOM.objects.all()
        paginator = Paginator(uoms, per_page)
        page_obj = paginator.get_page(page)
        serializer = UOMSerializer(page_obj, many=True)
        return Response({
            'uoms': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': uoms.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can add UOMs'}, status=status.HTTP_403_FORBIDDEN)
        serializer = UOMSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UOMDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            uom = UOM.objects.get(pk=pk)
            serializer = UOMSerializer(uom)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UOM.DoesNotExist:
            return Response({'error': 'UOM not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can edit UOMs'}, status=status.HTTP_403_FORBIDDEN)
        try:
            uom = UOM.objects.get(pk=pk)
            serializer = UOMSerializer(uom, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UOM.DoesNotExist:
            return Response({'error': 'UOM not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete UOMs'}, status=status.HTTP_403_FORBIDDEN)
        try:
            uom = UOM.objects.get(pk=pk)
            uom.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UOM.DoesNotExist:
            return Response({'error': 'UOM not found'}, status=status.HTTP_404_NOT_FOUND)

class WarehouseListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        warehouses = Warehouse.objects.all()
        paginator = Paginator(warehouses, per_page)
        page_obj = paginator.get_page(page)
        serializer = WarehouseSerializer(page_obj, many=True)
        return Response({
            'warehouses': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': warehouses.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can add warehouses'}, status=status.HTTP_403_FORBIDDEN)
        serializer = WarehouseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WarehouseDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            warehouse = Warehouse.objects.get(pk=pk)
            serializer = WarehouseSerializer(warehouse)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Warehouse.DoesNotExist:
            return Response({'error': 'Warehouse not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can edit warehouses'}, status=status.HTTP_403_FORBIDDEN)
        try:
            warehouse = Warehouse.objects.get(pk=pk)
            serializer = WarehouseSerializer(warehouse, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Warehouse.DoesNotExist:
            return Response({'error': 'Warehouse not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete warehouses'}, status=status.HTTP_403_FORBIDDEN)
        try:
            warehouse = Warehouse.objects.get(pk=pk)
            warehouse.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Warehouse.DoesNotExist:
            return Response({'error': 'Warehouse not found'}, status=status.HTTP_404_NOT_FOUND)

class SizeListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        sizes = Size.objects.all()
        paginator = Paginator(sizes, per_page)
        page_obj = paginator.get_page(page)
        serializer = SizeSerializer(page_obj, many=True)
        return Response({
            'sizes': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': sizes.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can add sizes'}, status=status.HTTP_403_FORBIDDEN)
        serializer = SizeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SizeDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            size = Size.objects.get(pk=pk)
            serializer = SizeSerializer(size)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Size.DoesNotExist:
            return Response({'error': 'Size not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can edit sizes'}, status=status.HTTP_403_FORBIDDEN)
        try:
            size = Size.objects.get(pk=pk)
            serializer = SizeSerializer(size, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Size.DoesNotExist:
            return Response({'error': 'Size not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete sizes'}, status=status.HTTP_403_FORBIDDEN)
        try:
            size = Size.objects.get(pk=pk)
            size.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Size.DoesNotExist:
            return Response({'error': 'Size not found'}, status=status.HTTP_404_NOT_FOUND)

class ColorListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        colors = Color.objects.all()
        paginator = Paginator(colors, per_page)
        page_obj = paginator.get_page(page)
        serializer = ColorSerializer(page_obj, many=True)
        return Response({
            'colors': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': colors.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can add colors'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ColorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ColorDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            color = Color.objects.get(pk=pk)
            serializer = ColorSerializer(color)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Color.DoesNotExist:
            return Response({'error': 'Color not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can edit colors'}, status=status.HTTP_403_FORBIDDEN)
        try:
            color = Color.objects.get(pk=pk)
            serializer = ColorSerializer(color, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Color.DoesNotExist:
            return Response({'error': 'Color not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete colors'}, status=status.HTTP_403_FORBIDDEN)
        try:
            color = Color.objects.get(pk=pk)
            color.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Color.DoesNotExist:
            return Response({'error': 'Color not found'}, status=status.HTTP_404_NOT_FOUND)

from .models import ProductSupplier
from .serializers import ProductSupplierSerializer
class ProductSupplierListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        suppliers = ProductSupplier.objects.all()
        paginator = Paginator(suppliers, per_page)
        page_obj = paginator.get_page(page)
        serializer = ProductSupplierSerializer(page_obj, many=True)
        return Response({
            'suppliers': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': suppliers.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can add suppliers'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProductSupplierSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductSupplierDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            supplier = ProductSupplier.objects.get(pk=pk)
            serializer = ProductSupplierSerializer(supplier)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ProductSupplier.DoesNotExist:
            return Response({'error': 'Supplier not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can edit suppliers'}, status=status.HTTP_403_FORBIDDEN)
        try:
            supplier = ProductSupplier.objects.get(pk=pk)
            serializer = ProductSupplierSerializer(supplier, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ProductSupplier.DoesNotExist:
            return Response({'error': 'Supplier not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete suppliers'}, status=status.HTTP_403_FORBIDDEN)
        try:
            supplier = ProductSupplier.objects.get(pk=pk)
            supplier.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProductSupplier.DoesNotExist:
            return Response({'error': 'Supplier not found'}, status=status.HTTP_404_NOT_FOUND)

class CustomerListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 10))
        customers = Customer.objects.all().order_by('last_edit_date')
        paginator = Paginator(customers, per_page)
        page_obj = paginator.get_page(page)
        serializer = CustomerSerializer(page_obj, many=True)
        return Response({
            'customers': serializer.data,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_entries': customers.count(),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            customer = Customer.objects.get(pk=pk)
            serializer = CustomerSerializer(customer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            customer = Customer.objects.get(pk=pk)
            serializer = CustomerSerializer(customer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            customer = Customer.objects.get(pk=pk)
            customer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

class CustomerSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        customers = Customer.objects.all()
        summary = {
            'active': customers.filter(status='Active').count(),
            'inactive': customers.filter(status='Inactive').count(),
            'sales_reps': CandidateSerializer(
                Candidate.objects.filter(designation__role="Sales Representative"),
                many=True
            ).data
        }
        return Response(summary, status=status.HTTP_200_OK)

class CustomerDuplicatesView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request):
        duplicates = (
            Customer.objects.values('first_name', 'last_name')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        duplicate_groups = []
        for item in duplicates:
            first_name = item['first_name']
            last_name = item['last_name']
            matching_customers = Customer.objects.filter(first_name=first_name, last_name=last_name)
            if matching_customers.count() > 1:
                primary = matching_customers.order_by('last_edit_date').first()
                duplicates = matching_customers.exclude(id=primary.id)
                serializer = CustomerSerializer(primary)
                duplicates_serializer = CustomerSerializer(duplicates, many=True)
                group = {
                    'primary': serializer.data,
                    'duplicates': duplicates_serializer.data
                }
                duplicate_groups.append(group)

        return Response(duplicate_groups, status=status.HTTP_200_OK)

class CustomerMergeView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def post(self, request):
        primary_id = request.data.get('primary_id')
        duplicate_ids = request.data.get('duplicate_ids', [])

        if not primary_id or not duplicate_ids:
            return Response(
                {'error': 'Primary ID and duplicate IDs are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            primary = Customer.objects.get(id=primary_id)
            duplicates = Customer.objects.filter(id__in=duplicate_ids)

            if not duplicates.exists():
                return Response(
                    {'error': 'No valid duplicates provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = CustomerSerializer(primary)
            duplicates.delete()

            return Response(
                {'merged_record': serializer.data},
                status=status.HTTP_200_OK
            )
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Primary record or duplicates not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from .models import Supplier, SupplierComment, SupplierAttachment
from .serializers import (
    SupplierSerializer,
    SupplierCreateUpdateSerializer,
    SupplierCommentSerializer,
    SupplierAttachmentSerializer
)


class SupplierListView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]
    def get(self, request):
        suppliers = Supplier.objects.all()

        # Search by supplier ID or name
        search = request.GET.get("search")
        if search:
            suppliers = suppliers.filter(
                Q(supplier_id__icontains=search) |
                Q(supplier_name__icontains=search)
            )

        # Filter by status
        status_param = request.GET.get("status")
        if status_param:
            suppliers = suppliers.filter(status=status_param)

        # Filter by type
        supplier_type = request.GET.get("type")
        if supplier_type:
            suppliers = suppliers.filter(supplier_type=supplier_type)

        # Filter by tier
        supplier_tier = request.GET.get("tier")
        if supplier_tier:
            suppliers = suppliers.filter(supplier_tier=supplier_tier)

        serializer = SupplierSerializer(suppliers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SupplierCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            supplier = serializer.save(created_by=request.user)
            return Response(
                SupplierSerializer(supplier).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]
    def get(self, request, pk):
        try:
            supplier = Supplier.objects.get(pk=pk)
        except Supplier.DoesNotExist:
            return Response({"error": "Supplier not found"}, status=404)

        serializer = SupplierSerializer(supplier)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            supplier = Supplier.objects.get(pk=pk)
        except Supplier.DoesNotExist:
            return Response({"error": "Supplier not found"}, status=404)

        serializer = SupplierCreateUpdateSerializer(supplier, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(SupplierSerializer(supplier).data)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            supplier = Supplier.objects.get(pk=pk)
            supplier.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)  # Better
        except Supplier.DoesNotExist:
            return Response({"error": "Supplier not found"}, status=404)


class SupplierCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]
    def get(self, request, pk):
        comments = SupplierComment.objects.filter(supplier_id=pk)
        serializer = SupplierCommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        data = request.data.copy()
        data["supplier"] = pk
        data["commented_by"] = request.user.id

        serializer = SupplierCommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class SupplierAttachmentView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]
    def get(self, request, pk):
        attachments = SupplierAttachment.objects.filter(supplier_id=pk)
        serializer = SupplierAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        data = request.data.copy()
        data["supplier"] = pk
        data["uploaded_by"] = request.user.id

        serializer = SupplierAttachmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import pdfkit
import os

from .models import Supplier
from .serializers import SupplierSerializer


# Dynamic wkhtmltopdf path
WKHTMLTOPDF_PATH = (
    r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    if os.name == "nt"
    else "/usr/bin/wkhtmltopdf"
)
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

class SupplierPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def get(self, request, pk):
        try:
            supplier = Supplier.objects.get(id=pk)

            context = {
                "supplier": supplier,
                "attachments": supplier.extra_attachments.all(),
                "comments": supplier.comments.all(),
            }

            html = render_to_string("supplier_pdf.html", context)

            options = {
                "page-size": "A4",
                "margin-top": "10mm",
                "margin-right": "10mm",
                "margin-bottom": "10mm",
                "margin-left": "10mm",
                "encoding": "UTF-8",
                "dpi": 300,
                "zoom": 1,
                "enable-local-file-access": None,
                "no-stop-slow-scripts": None,
                "disable-smart-shrinking": None,
            }

            pdf = pdfkit.from_string(html, False, configuration=config, options=options)

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="supplier_{supplier.supplier_id}.pdf"'
            )
            return response

        except ObjectDoesNotExist:
            return Response(
                {"error": "Supplier not found"}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": f"PDF generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class SupplierEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated,RoleBasedPermission]

    def post(self, request, pk):
        try:
            supplier = Supplier.objects.get(id=pk)

            email = request.data.get("email")
            if not email:
                return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

            data = SupplierSerializer(supplier).data

            # Default HTML email template
            html_content = request.data.get(
                "html_content",
                f"""
                <html>
                    <body>
                        <h2>Supplier Details</h2>
                        <p><strong>Supplier ID:</strong> {supplier.supplier_id}</p>
                        <p><strong>Name:</strong> {supplier.supplier_name}</p>
                        <p><strong>Country:</strong> {supplier.get_country_of_registration_display()}</p>
                        <p><strong>Status:</strong> {supplier.status}</p>
                        <p><strong>Risk Rating:</strong> {supplier.risk_rating}</p>
                        <p>Thank you.</p>
                    </body>
                </html>
                """
            )

            subject = f"Supplier {supplier.supplier_id}"
            msg = EmailMessage(subject, html_content, to=[email])
            msg.content_subtype = "html"
            msg.send()

            return Response({"message": "Email sent successfully"}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"error": "Supplier not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
