from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # Users Management
    path('users/', views.ManageUsersListCreateView.as_view(), name='users-list-create'),
    path('users/<int:pk>/', views.ManageUserDetailView.as_view(), name='user-detail'),

    # Branches
    path('branches/', views.BranchListCreateView.as_view(), name='branches-list-create'),
    path('branches/<int:pk>/', views.BranchDetailView.as_view(), name='branch-detail'),

    # Departments
    path('departments/', views.DepartmentListView.as_view(), name='departments-list'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='departments-create'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='departments-detail'),

    # Roles (read-only)
    path('roles/', views.RoleListView.as_view(), name='roles-list'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='roles-detail'),

    # Products
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),

    # Category
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),

    # TaxCode
    path('taxcodes/', views.TaxCodeListCreateView.as_view(), name='taxcode-list-create'),
    path('taxcodes/<int:pk>/', views.TaxCodeDetailView.as_view(), name='taxcode-detail'),

    # UOM
    path('uoms/', views.UOMListCreateView.as_view(), name='uom-list-create'),
    path('uoms/<int:pk>/', views.UOMDetailView.as_view(), name='uom-detail'),

    # Warehouse
    path('warehouses/', views.WarehouseListCreateView.as_view(), name='warehouse-list-create'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse-detail'),

    # Size
    path('sizes/', views.SizeListCreateView.as_view(), name='size-list-create'),
    path('sizes/<int:pk>/', views.SizeDetailView.as_view(), name='size-detail'),

    # Color
    path('colors/', views.ColorListCreateView.as_view(), name='color-list-create'),
    path('colors/<int:pk>/', views.ColorDetailView.as_view(), name='color-detail'),

    # ProductSupplier
    path('product-suppliers/', views.ProductSupplierListCreateView.as_view(), name='product-supplier-list-create'),
    path('product-suppliers/<int:pk>/', views.ProductSupplierDetailView.as_view(), name='product-supplier-detail'),

    #import
    path('products/import/', views.ProductImportView.as_view(), name='product-import'),
    path('products/import/confirm/', views.ProductImportConfirmView.as_view(), name='product-import-confirm'),
    
    #Customer
    path('customers/', views.CustomerListCreateView.as_view(), name='customer-list-create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer-detail'),
    path('customers/import/', views.CustomerImportView.as_view(), name='customer-import'),
    path('customers/import/confirm/', views.CustomerImportConfirmView.as_view(), name='customer-import-confirm'),
    path('customers/duplicates/', views.CustomerDuplicatesListView.as_view(), name='customer-duplicates-list'),
    path('customers/merge/review/', views.CustomerMergeReviewView.as_view(), name='customer-merge-review'),
    path('customers/merge/confirm/', views.CustomerMergeConfirmView.as_view(), name='customer-merge-confirm'),

    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
    path('suppliers/<int:pk>/pdf/', views.SupplierPDFView.as_view(), name='supplier-pdf'),
    path('suppliers/<int:pk>/email/', views.SupplierEmailView.as_view(), name='supplier-email'),
    path('suppliers/<int:pk>/comments/', views.SupplierCommentView.as_view(), name='supplier-comments'),
    path('suppliers/<int:pk>/attachments/', views.SupplierAttachmentView.as_view(), name='supplier-attachments'),
    path('suppliers/<int:pk>/history/', views.SupplierHistoryView.as_view(), name='supplier-history'),

] + static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)