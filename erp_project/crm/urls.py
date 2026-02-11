from django.urls import path
from . import views

urlpatterns = [
    path('enquiries/', views.EnquiryListCreateView.as_view(), name='enquiry-list-create'),
    path('enquiries/<int:pk>/', views.EnquiryDetailView.as_view(), name='enquiry-detail'),

    path('quotations/', views.QuotationListCreateView.as_view(), name='quotation-list-create'),
    path('quotations/<int:pk>/', views.QuotationDetailView.as_view(), name='quotation-detail'),
    path('quotations/<int:pk>/action/', views.QuotationActionView.as_view(), name='quotation-action'),
    path('quotations/<int:pk>/attachments/',views.QuotationAttachmentView.as_view(),name='quotation-attachments'),
    path('attachments/<int:pk>/delete/',views.QuotationAttachmentDeleteView.as_view(),name='quotation-attachment-delete'),

    path('quotations/<int:pk>/pdf/', views.QuotationPDFView.as_view(), name='quotation-pdf'),
    path('quotations/<int:pk>/email/', views.QuotationMailView.as_view(), name='quotation-email'),

    # SalesOrder URLs


    path('sales-orders/', views.SalesOrderListCreateView.as_view(), name='sales-order-list-create'),
    path('sales-orders/<int:pk>/', views.SalesOrderDetailView.as_view(), name='sales-order-detail'),
    path('sales-orders/<int:pk>/action/', views.SalesOrderActionView.as_view(), name='sales-order-action'),
    path('sales-orders/<int:pk>/pdf/', views.SalesOrderPDFView.as_view(), name='sales-order-pdf'),
    path('sales-orders/<int:pk>/email/', views.SalesOrderMailView.as_view(), name='sales-order-email'),

    # DeliveryNote URLs
    path('delivery-notes/', views.DeliveryNoteListView.as_view(), name='delivery-note-list'),
    path('delivery-notes/<int:pk>/', views.DeliveryNoteDetailView.as_view(), name='delivery-note-detail'),
    path('delivery-notes/<int:pk>/items/', views.DeliveryNoteItemView.as_view(), name='delivery-note-items'),
    path('delivery-notes/<int:pk>/items/<int:item_pk>/serial-numbers/', views.DeliveryNoteSerialNumbersView.as_view(), name='delivery-note-serial-numbers'),
    path('delivery-notes/<int:pk>/pdf/', views.DeliveryNotePDFView.as_view(), name='delivery-note-pdf'),
    path('delivery-notes/<int:pk>/email/', views.DeliveryNoteEmailView.as_view(), name='delivery-note-email'),
   
    # Invoice URLs
    path('invoices/', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/<int:pk>/items/', views.InvoiceItemView.as_view(), name='invoice-items'),
    path('invoices/<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice-pdf'),
    path('invoices/<int:pk>/email/', views.InvoiceEmailView.as_view(), name='invoice-email'),

    path('invoice-returns/', views.InvoiceReturnListView.as_view(), name='invoice-return-list'),
    path('invoice-returns/<int:pk>/', views.InvoiceReturnDetailView.as_view(), name='invoice-return-detail'),
    path('invoice-returns/<int:pk>/items/', views.InvoiceReturnItemView.as_view(), name='invoice-return-items'),
    path('invoice-returns/<int:pk>/items/<int:item_pk>/', views.InvoiceReturnItemView.as_view(), name='invoice-return-item-delete'),
    path('invoice-returns/<int:pk>/pdf/', views.InvoiceReturnPDFView.as_view(), name='invoice-return-pdf'),
    path('invoice-returns/<int:pk>/email/', views.InvoiceReturnEmailView.as_view(), name='invoice-return-email'),

    path('delivery-note-returns/', views.DeliveryNoteReturnListView.as_view(), name='delivery-note-return-list'),
    path('delivery-note-returns/<int:pk>/', views.DeliveryNoteReturnDetailView.as_view(), name='delivery-note-return-detail'),
    path('delivery-note-returns/<int:pk>/items/', views.DeliveryNoteReturnItemView.as_view(), name='delivery-note-return-items'),
    path('delivery-note-returns/<int:pk>/items/<int:item_pk>/', views.DeliveryNoteReturnItemView.as_view(), name='delivery-note-return-item-delete'),
    path('delivery-note-returns/<int:pk>/pdf/', views.DeliveryNoteReturnPDFView.as_view(), name='delivery-note-return-pdf'),
    path('delivery-note-returns/<int:pk>/email/', views.DeliveryNoteReturnEmailView.as_view(), name='delivery-note-return-email'),
]