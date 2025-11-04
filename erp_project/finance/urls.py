from django.urls import path
from .views import CreditNoteListView, CreditNoteDetailView, CreditNoteItemView, CreditNotePDFView, CreditNoteEmailView, DebitNoteListView, DebitNoteDetailView, DebitNoteItemView, DebitNotePDFView, DebitNoteEmailView

urlpatterns = [
    # CreditNote URLs
    path('credit-notes/', CreditNoteListView.as_view(), name='credit-note-list'),
    path('credit-notes/<int:pk>/', CreditNoteDetailView.as_view(), name='credit-note-detail'),
    path('credit-notes/<int:pk>/items/', CreditNoteItemView.as_view(), name='credit-note-items'),
    path('credit-notes/<int:pk>/pdf/', CreditNotePDFView.as_view(), name='credit-note-pdf'),
    path('credit-notes/<int:pk>/email/', CreditNoteEmailView.as_view(), name='credit-note-email'),
    # DebitNote URLs
    path('debit-notes/', DebitNoteListView.as_view(), name='debit-note-list'),
    path('debit-notes/<int:pk>/', DebitNoteDetailView.as_view(), name='debit-note-detail'),
    path('debit-notes/<int:pk>/items/', DebitNoteItemView.as_view(), name='debit-note-items'),
    path('debit-notes/<int:pk>/pdf/', DebitNotePDFView.as_view(), name='debit-note-pdf'),
    path('debit-notes/<int:pk>/email/', DebitNoteEmailView.as_view(), name='debit-note-email'),
]