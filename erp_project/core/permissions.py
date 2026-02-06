# core/permissions.py

from rest_framework import permissions


class RoleBasedPermission(permissions.BasePermission):
    """
    Role-Based Access Control (RBAC) for Stackly ERP

    - Django superuser (created via createsuperuser) → full access (bypass everything)
    - Role named 'Admin' → full access to ALL modules/views (listed or unlisted)
    - All other roles → strict permission check based on role.permissions JSONField
    - Unknown/unlisted views → denied for normal users (safe default)
    """

    # View name → permission category mapping
    # Only listed here for normal users. Admin & superuser bypass this entirely.
    VIEW_TO_CATEGORY = {
        # Masters
        'BranchListCreateView': 'masters',
        'BranchDetailView': 'masters',
        'DepartmentListView': 'masters',
        'DepartmentCreateView': 'masters',
        'DepartmentDetailView': 'masters',

        # Users
        'ManageUsersListCreateView': 'users',
        'ManageUserDetailView': 'users',

        # Inventory Masters
        'CategoryListCreateView': 'inventory',
        'CategoryDetailView': 'inventory',
        'TaxCodeListCreateView': 'inventory',
        'TaxCodeDetailView': 'inventory',
        'UOMListCreateView': 'inventory',
        'UOMDetailView': 'inventory',
        'WarehouseListCreateView': 'inventory',
        'WarehouseDetailView': 'inventory',
        'SizeListCreateView': 'inventory',
        'SizeDetailView': 'inventory',
        'ColorListCreateView': 'inventory',
        'ColorDetailView': 'inventory',
        'ProductSupplierListCreateView': 'inventory',
        'ProductSupplierDetailView': 'inventory',
        'ProductListCreateView': 'inventory',
        'ProductDetailView': 'inventory',

        # Suppliers / Customers
        'SupplierListCreateView': 'supplier',
        'SupplierDetailView': 'supplier',
        'CustomerListCreateView': 'customer',
        'CustomerDetailView': 'customer',

        # HR / Onboarding
        'OnboardingListView': 'hr',
        'OnboardingDetailView': 'hr',

        # Task & Projects
        'TaskListCreateView': 'task',
        'TaskDetailView': 'task',
        'ProjectListCreateView': 'project',
        'ProjectDetailView': 'project',

        # Attendance
        'AttendanceView': 'attendance',
        'CheckInOutView': 'attendance',

        # Dashboard & Profile
        'DashboardCombinedView': 'dashboard',
        'ProfileView': 'profile',

        # Reports
        'ReportListView': 'reports',
        'ReportDetailView': 'reports',
    }

    def has_permission(self, request, view):
        # 1. Django superuser (created via createsuperuser command) → full access
        if request.user.is_superuser:
            return True

        # 2. Must be authenticated
        if not request.user.is_authenticated:
            return False

        # 3. Must have a role assigned
        if not hasattr(request.user, 'role') or not request.user.role:
            return False

        role = request.user.role
        role_name = role.role.lower().strip()  # Normalize for matching

        # 4. Special 'Admin' role → full access (bypass all checks, listed or unlisted views)
        if role_name == 'admin':
            return True

        # 5. Normal roles → apply strict JSON-based permission check
        permissions_dict = role.permissions or {}

        view_name = view.__class__.__name__
        category = self.VIEW_TO_CATEGORY.get(view_name)

        # If view is NOT listed in mapping → deny access (safe default for normal users)
        if not category:
            return False

        # Get permissions for this category from JSON
        cat_perms = permissions_dict.get(category, {})

        # SAFE METHODS (GET, HEAD, OPTIONS) → require 'view' or 'full_access'
        if request.method in permissions.SAFE_METHODS:
            return cat_perms.get('view', False) or cat_perms.get('full_access', False)

        # CREATE (POST)
        if request.method == 'POST':
            return cat_perms.get('create', False) or cat_perms.get('full_access', False)

        # UPDATE (PUT/PATCH)
        if request.method in ['PUT', 'PATCH']:
            return cat_perms.get('edit', False) or cat_perms.get('full_access', False)

        # DELETE
        if request.method == 'DELETE':
            return cat_perms.get('delete', False) or cat_perms.get('full_access', False)

        # Default deny
        return False