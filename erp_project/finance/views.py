from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import CreditNote, CreditNoteItem, CreditNoteAttachment, CreditNoteRemark, CreditNotePaymentRefund, DebitNote, DebitNoteItem, DebitNoteAttachment, DebitNoteRemark, DebitNotePaymentRecover
from .serializers import CreditNoteSerializer, CreditNoteItemSerializer, CreditNoteAttachmentSerializer, CreditNoteRemarkSerializer, CreditNotePaymentRefundSerializer, DebitNoteSerializer, DebitNoteItemSerializer, DebitNoteAttachmentSerializer, DebitNoteRemarkSerializer, DebitNotePaymentRecoverSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io
from django.utils import timezone

class CreditNoteListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        credit_notes = CreditNote.objects.all().order_by('-credit_note_date')
        serializer = CreditNoteSerializer(credit_notes, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Ensure created_by is a valid Candidate from sales department
        request_data = request.data.copy()
        if 'created_by' in request_data and not request_data['created_by']:
            request_data['created_by'] = request.user.profile.candidate.id if hasattr(request.user.profile, 'candidate') else None
        serializer = CreditNoteSerializer(data=request_data)
        if serializer.is_valid():
            credit_note = serializer.save()
            return Response(CreditNoteSerializer(credit_note).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreditNoteDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            credit_note = CreditNote.objects.get(id=pk)
            serializer = CreditNoteSerializer(credit_note)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Credit Note not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            credit_note = CreditNote.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'delete_credit_note':
                credit_note.delete()
            elif action == 'cancel':
                credit_note.invoice_status = 'Cancelled'
            elif action == 'save_draft':
                credit_note.invoice_status = 'Draft'
            elif action == 'mark_as_paid':
                credit_note.payment_status = 'Paid'
            else:
                serializer = CreditNoteSerializer(credit_note, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(CreditNoteSerializer(credit_note).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            credit_note.save()
            if credit_note.payment_refund:
                credit_note.payment_refund.save()
            return Response(CreditNoteSerializer(credit_note).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Credit Note not found'}, status=status.HTTP_404_NOT_FOUND)

class CreditNoteItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            credit_note = CreditNote.objects.get(id=pk)
            item_data = request.data
            item_data['credit_note'] = pk
            serializer = CreditNoteItemSerializer(data=item_data)
            if serializer.is_valid():
                item = serializer.save()
                credit_note.items.add(item)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Credit Note not found'}, status=status.HTTP_404_NOT_FOUND)

class CreditNotePDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            credit_note = CreditNote.objects.get(id=pk)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = [
                Paragraph(f"Credit Note ID: {credit_note.CREDIT_NOTE_ID}", style={'fontName': 'Helvetica-Bold', 'fontSize': 14}),
                Paragraph(f"Date: {credit_note.credit_note_date}", style={'fontName': 'Helvetica', 'fontSize': 12}),
                Paragraph(f"Customer: {credit_note.customer.name}", style={'fontName': 'Helvetica', 'fontSize': 12}),
            ]
            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="credit_note_{credit_note.CREDIT_NOTE_ID}.pdf"'
            return response
        except ObjectDoesNotExist:
            return Response({'error': 'Credit Note not found'}, status=status.HTTP_404_NOT_FOUND)

class CreditNoteEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            credit_note = CreditNote.objects.get(id=pk)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            subject = f'Credit Note {credit_note.CREDIT_NOTE_ID}'
            html_message = render_to_string('credit_note_email_template.html', {'credit_note': credit_note})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Credit Note not found'}, status=status.HTTP_404_NOT_FOUND)

class DebitNoteListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        debit_notes = DebitNote.objects.all().order_by('-debit_note_date')
        serializer = DebitNoteSerializer(debit_notes, many=True)
        return Response(serializer.data)

    def post(self, request):
        request_data = request.data.copy()
        if 'created_by' in request_data and not request_data['created_by']:
            request_data['created_by'] = request.user.profile.candidate.id if hasattr(request.user.profile, 'candidate') else None
        serializer = DebitNoteSerializer(data=request_data)
        if serializer.is_valid():
            debit_note = serializer.save()
            return Response(DebitNoteSerializer(debit_note).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DebitNoteDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            debit_note = DebitNote.objects.get(id=pk)
            serializer = DebitNoteSerializer(debit_note)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Debit Note not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            debit_note = DebitNote.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'delete_debit_note':
                debit_note.delete()
            elif action == 'cancel':
                debit_note.payment_status = 'Cancelled'
            elif action == 'save_draft':
                debit_note.payment_status = 'Draft'
            elif action == 'mark_as_settled':
                debit_note.payment_status = 'Paid'
            else:
                serializer = DebitNoteSerializer(debit_note, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(DebitNoteSerializer(debit_note).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            debit_note.save()
            if debit_note.payment_recover:
                debit_note.payment_recover.save()
            return Response(DebitNoteSerializer(debit_note).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Debit Note not found'}, status=status.HTTP_404_NOT_FOUND)

class DebitNoteItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            debit_note = DebitNote.objects.get(id=pk)
            item_data = request.data
            item_data['debit_note'] = pk
            serializer = DebitNoteItemSerializer(data=item_data)
            if serializer.is_valid():
                item = serializer.save()
                debit_note.items.add(item)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Debit Note not found'}, status=status.HTTP_404_NOT_FOUND)

class DebitNotePDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            debit_note = DebitNote.objects.get(id=pk)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = [
                Paragraph(f"Debit Note ID: {debit_note.DEBIT_NOTE_ID}", style={'fontName': 'Helvetica-Bold', 'fontSize': 14}),
                Paragraph(f"Date: {debit_note.debit_note_date}", style={'fontName': 'Helvetica', 'fontSize': 12}),
                Paragraph(f"Supplier: {debit_note.supplier.name}", style={'fontName': 'Helvetica', 'fontSize': 12}),
            ]
            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="debit_note_{debit_note.DEBIT_NOTE_ID}.pdf"'
            return response
        except ObjectDoesNotExist:
            return Response({'error': 'Debit Note not found'}, status=status.HTTP_404_NOT_FOUND)

class DebitNoteEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            debit_note = DebitNote.objects.get(id=pk)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            subject = f'Debit Note {debit_note.DEBIT_NOTE_ID}'
            html_message = render_to_string('debit_note_email_template.html', {'debit_note': debit_note})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Debit Note not found'}, status=status.HTTP_404_NOT_FOUND)