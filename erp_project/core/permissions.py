from rest_framework import permissions

class RoleBasedPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Superusers have full access
        if request.user.is_superuser:
            return True

        # Non-superusers must have a role
        if not request.user.profile.role:
            return False

        # Get the user's role permissions
        role_permissions = request.user.profile.role.permissions

        # Map the view to a permission category
        permission_category = None
        if view.__class__.__name__ in ['DepartmentListView', 'DepartmentDetailView']:
            permission_category = 'dashboard'
        elif view.__class__.__name__ in ['RoleView', 'RoleDetailView']:
            permission_category = 'task'
        elif view.__class__.__name__ in ['BranchListView', 'BranchDetailView']:
            permission_category = 'projectTracker'
        elif view.__class__.__name__ in ['ManageUsersView', 'ManageUserDetailView', 'OnboardingListView', 'OnboardingDetailView']:
            permission_category = 'onboarding'
        elif view.__class__.__name__ in ['ProductListView', 'ProductDetailView', 'ProductImportView', 'CategoryListView', 'CategoryDetailView', 'TaxCodeListView', 'TaxCodeDetailView', 'UOMListView', 'UOMDetailView', 'WarehouseListView', 'WarehouseDetailView', 'SizeListView', 'SizeDetailView', 'ColorListView', 'ColorDetailView', 'SupplierListView', 'SupplierDetailView']:
            permission_category = 'inventory'
        elif view.__class__.__name__ in ['AttendanceView', 'CheckInOutView']:
            permission_category = 'attendance'
        elif view.__class__.__name__ in ['ProfileView']:
            permission_category = 'profile'
        else:
            return False  # Deny access by default for unmapped views

        # Check if the category exists in permissions
        if permission_category not in role_permissions:
            return False

        category_permissions = role_permissions[permission_category]

        # Check specific permissions based on the request method
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return category_permissions.get('view', False)
        elif request.method == 'POST':
            return category_permissions.get('create', False)
        elif request.method in ['PUT', 'PATCH']:
            return category_permissions.get('edit', False)
        elif request.method == 'DELETE':
            return category_permissions.get('delete', False)

        return False