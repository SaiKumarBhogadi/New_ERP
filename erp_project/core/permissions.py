# core/permissions.py (or your preferred location)

from rest_framework import permissions

class RoleBasedPermission(permissions.BasePermission):
    """
    Role-based permission using CustomUser.role.permissions JSONField
    Superusers have full access
    """

    # Map view class names to permission categories
    VIEW_TO_CATEGORY = {
        # Masters / Setup
        'DepartmentListView': 'masters',
        'DepartmentDetailView': 'masters',
        'RoleView': 'masters',
        'RoleDetailView': 'masters',
        'BranchListView': 'masters',
        'BranchDetailView': 'masters',

        # Users Management
        'ManageUsersView': 'users',
        'ManageUserDetailView': 'users',

        # Onboarding / HR
        'OnboardingListView': 'hr',
        'OnboardingDetailView': 'hr',

        # Inventory / Masters
        'ProductListView': 'inventory',
        'ProductDetailView': 'inventory',
        'ProductImportView': 'inventory',
        'CategoryListView': 'inventory',
        'CategoryDetailView': 'inventory',
        'TaxCodeListView': 'inventory',
        'TaxCodeDetailView': 'inventory',
        'UOMListView': 'inventory',
        'UOMDetailView': 'inventory',
        'WarehouseListView': 'inventory',
        'WarehouseDetailView': 'inventory',
        'SizeListView': 'inventory',
        'SizeDetailView': 'inventory',
        'ColorListView': 'inventory',
        'ColorDetailView': 'inventory',
        'ProductSupplierListView': 'inventory',
        'ProductSupplierDetailView': 'inventory',

        #  Supplier
        'SupplierListView': 'supplier',
        'SupplierDetailView': 'supplier',

        # Attendance
        'AttendanceView': 'attendance',
        'CheckInOutView': 'attendance',

        # Task Management
        'TaskListView': 'task',
        'TaskDetailView': 'task',
        'TaskSummaryView': 'task',

        # Dashboard
        'DashboardCombinedView': 'dashboard',

        # Profile
        'ProfileView': 'profile',

        # Auth Views - AllowAny already set, but safe fallback
        'RegisterView': 'auth',
        'LoginView': 'auth',
        'LogoutView': 'auth',
        'ForgotPasswordView': 'auth',
        'ResetPasswordView': 'auth',
    }

    def has_permission(self, request, view):
        # Superuser → full access
        if request.user.is_superuser:
            return True

        # Public endpoints (AllowAny views)
        public_views = ['RegisterView', 'LoginView', 'ForgotPasswordView', 'ResetPasswordView']
        if view.__class__.__name__ in public_views:
            return True

        # Must be authenticated
        if not request.user.is_authenticated:
            return False

        # Must have a role
        try:
            role = request.user.role
            if not role:
                return False
            permissions_dict = role.permissions  # JSONField
        except AttributeError:
            return False

        # Get category from view name
        view_name = view.__class__.__name__
        category = self.VIEW_TO_CATEGORY.get(view_name)

        if not category:
            return False  # Unknown view → deny

        # Get category permissions
        cat_perms = permissions_dict.get(category, {})

        # SAFE METHODS (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return cat_perms.get('view', False)

        # CREATE (POST on ListView)
        elif request.method == 'POST':
            if view_name.endswith('ListView'):
                return cat_perms.get('create', False)
            else:
                # Actions like submit, comment, upload → usually need edit
                return cat_perms.get('edit', False)

        # UPDATE (PUT/PATCH)
        elif request.method in ['PUT', 'PATCH']:
            return cat_perms.get('edit', False)

        # DELETE
        elif request.method == 'DELETE':
            return cat_perms.get('delete', False)

        return False