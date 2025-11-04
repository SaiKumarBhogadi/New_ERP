from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('users/', views.ManageUsersView.as_view(), name='manage-users'),
    path('users/<int:pk>/', views.ManageUserDetailView.as_view(), name='manage-user-detail'),
    path('branches/', views.BranchListView.as_view(), name='branch-list'),
    path('branches/<int:pk>/', views.BranchDetailView.as_view(), name='branch-detail'),
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    path('roles/', views.RoleView.as_view(), name='role-create'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role-detail'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/import/', views.ProductImportView.as_view(), name='product-import'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('tax-codes/', views.TaxCodeListView.as_view(), name='tax-code-list'),
    path('tax-codes/<int:pk>/', views.TaxCodeDetailView.as_view(), name='tax-code-detail'),
    path('uoms/', views.UOMListView.as_view(), name='uom-list'),
    path('uoms/<int:pk>/', views.UOMDetailView.as_view(), name='uom-detail'),
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse-detail'),
    path('sizes/', views.SizeListView.as_view(), name='size-list'),
    path('sizes/<int:pk>/', views.SizeDetailView.as_view(), name='size-detail'),
    path('colors/', views.ColorListView.as_view(), name='color-list'),
    path('colors/<int:pk>/', views.ColorDetailView.as_view(), name='color-detail'),
    path('suppliers/', views.SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/summary/', views.CustomerSummaryView.as_view(), name='customer_summary'),
    path('customers/duplicates/', views.CustomerDuplicatesView.as_view(), name='customer_duplicates'),
    path('customers/merge/', views.CustomerMergeView.as_view(), name='customer_merge'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)