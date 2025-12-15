from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Enquiry, EnquiryItem
from .serializers import EnquirySerializer, EnquiryCreateSerializer
from django.core.exceptions import ObjectDoesNotExist

class EnquiryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # LIST ALL ENQUIRIES FOR LOGGED-IN USER
    def get(self, request):
        enquiries = Enquiry.objects.filter(user=request.user).order_by('-created_at')
        serializer = EnquirySerializer(enquiries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # CREATE NEW ENQUIRY
    def post(self, request):
        serializer = EnquiryCreateSerializer(data=request.data)
        if serializer.is_valid():
            enquiry = serializer.save(user=request.user)
            return Response(EnquirySerializer(enquiry).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE ENQUIRY
    def delete(self, request):
        enquiry_id = request.data.get("id")
        if not enquiry_id:
            return Response({"error": "id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            enquiry = Enquiry.objects.get(id=enquiry_id, user=request.user)
            enquiry.delete()
            return Response({"message": "Deleted successfully"}, status=status.HTTP_200_OK)
        except Enquiry.DoesNotExist:
            return Response({"error": "Enquiry not found"}, status=status.HTTP_404_NOT_FOUND)

class EnquiryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # GET SINGLE ENQUIRY
    def get(self, request, pk):
        try:
            enquiry = Enquiry.objects.get(id=pk, user=request.user)
            serializer = EnquirySerializer(enquiry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Enquiry.DoesNotExist:
            return Response({"error": "Enquiry not found"}, status=status.HTTP_404_NOT_FOUND)

    # UPDATE SINGLE ENQUIRY
    def put(self, request, pk):
        try:
            enquiry = Enquiry.objects.get(id=pk, user=request.user)
            serializer = EnquiryCreateSerializer(enquiry, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(EnquirySerializer(enquiry).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Enquiry.DoesNotExist:
            return Response({"error": "Enquiry not found"}, status=status.HTTP_404_NOT_FOUND)

        


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Quotation, QuotationItem, QuotationAttachment, QuotationComment, QuotationHistory
from .serializers import QuotationSerializer, QuotationCreateSerializer, QuotationAttachmentSerializer, QuotationCommentSerializer, QuotationHistorySerializer, QuotationItemSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io

class QuotationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        quotations = Quotation.objects.all().order_by('-created_at')
        serializer = QuotationSerializer(quotations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = QuotationCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            quotation = serializer.save()
            return Response(QuotationSerializer(quotation).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

class QuotationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            serializer = QuotationSerializer(quotation)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            action = request.data.get('action')
            if action == 'save_draft':
                quotation.status = 'Draft'
            elif action == 'submit':
                quotation.status = 'Send'
            elif action == 'approve':
                quotation.status = 'Approved'
            elif action == 'reject':
                quotation.status = 'Rejected'
            elif action == 'convert_to_so':
                quotation.status = 'Converted (SO)'
            elif action == 'cancel':
                quotation.status = 'Expired'  # Or handle cancellation differently if needed
            else:
                serializer = QuotationCreateSerializer(quotation, data=request.data, partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return Response(QuotationSerializer(quotation).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            quotation.save()
            QuotationHistory.objects.create(quotation=quotation, status=quotation.status, action_by=request.user)
            return Response(QuotationSerializer(quotation).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            quotation.delete()
            return Response({'message': 'Quotation deleted successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)
        

class QuotationAttachmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            attachment_data = {
                'file': request.FILES.get('file'),
                'uploaded_by': request.user,
            }
            attachment = QuotationAttachment.objects.create(quotation=quotation, **attachment_data)
            serializer = QuotationAttachmentSerializer(attachment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'error': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            attachments = quotation.attachments.all()
            serializer = QuotationAttachmentSerializer(attachments, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, attachment_id):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            attachment = QuotationAttachment.objects.get(id=attachment_id, quotation=quotation)
            attachment.delete()
            return Response({'message': 'Attachment deleted'}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'error': 'Attachment or Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

class QuotationCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            comment_data = {
                'person_name': request.user,
                'comment': request.data.get('comment'),
            }
            comment = QuotationComment.objects.create(quotation=quotation, **comment_data)
            serializer = QuotationCommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'error': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            comments = quotation.comments.all()
            serializer = QuotationCommentSerializer(comments, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

class QuotationHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            history = quotation.history.all()
            serializer = QuotationHistorySerializer(history, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            history_data = {
                'status': request.data.get('status'),
                'action_by': request.user,
            }
            history = QuotationHistory.objects.create(quotation=quotation, **history_data)
            serializer = QuotationHistorySerializer(history)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'error': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)






from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import pdfkit
import os

from .models import Quotation
from .serializers import QuotationSerializer    # ⬅ FIXED (you forgot this import)


# Path for wkhtmltopdf
WKHTMLTOPDF_PATH = (
    r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    if os.name == "nt"
    else "/usr/bin/wkhtmltopdf"
)
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)



# ---------------------------------------------------------
# PDF GENERATION VIEW
# ---------------------------------------------------------
class QuotationPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            items = quotation.items.all()

            subtotal = sum(item.total for item in items)
            global_discount_amount = subtotal * (quotation.globalDiscount / 100)
            grand_total = subtotal - global_discount_amount + quotation.shippingCharges

            context = {
                "quotation": quotation,
                "items": items,
                "subtotal": subtotal,
                "global_discount_amount": global_discount_amount,
                "grand_total": grand_total,
                "comments": quotation.comments.all(),
                "attachments": quotation.attachments.all(),
                "revisions": quotation.revisions.all(),
                "history": quotation.history.all(),
            }

            html = render_to_string("quotation_pdf.html", context)

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
            }

            pdf = pdfkit.from_string(html, False, configuration=config, options=options)

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="quotation_{quotation.quotation_id}.pdf"'
            )
            return response

        except ObjectDoesNotExist:
            return Response(
                {"error": "Quotation not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": f"PDF generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



# ---------------------------------------------------------
# EMAIL QUOTATION VIEW
# ---------------------------------------------------------
class QuotationEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk, user=request.user)
            email = request.data.get('email')

            if not email:
                return Response(
                    {'error': 'Email is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ----- Calculate grand total -----
            items = quotation.items.all()
            subtotal = sum(item.total for item in items)
            global_discount_amount = subtotal * (quotation.globalDiscount / 100)
            grand_total = subtotal - global_discount_amount + quotation.shippingCharges

            # ----- Email HTML -----
            html_content = f"""
                <html>
                    <body>
                        <h2>Quotation Details</h2>
                        <p><strong>Quotation ID:</strong> {quotation.quotation_id}</p>
                        <p><strong>Customer:</strong> {quotation.customer_name}</p>
                        <p><strong>Date:</strong> {quotation.quotation_date}</p>
                        <p><strong>Total:</strong> ₹{grand_total}</p>
                        <br>
                        <p>Thank you for your business!</p>
                    </body>
                </html>
            """

            subject = f'Quotation {quotation.quotation_id}'

            msg = EmailMessage(subject, html_content, to=[email])
            msg.content_subtype = 'html'  # send as HTML
            msg.send()

            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response(
                {'error': 'Quotation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import SalesOrder, SalesOrderItem, SalesOrderComment, SalesOrderHistory, DeliveryNote, DeliveryNoteItem, DeliveryNoteCustomerAcknowledgement, DeliveryNoteAttachment, DeliveryNoteRemark, Invoice, InvoiceItem, InvoiceAttachment, InvoiceRemark, OrderSummary
from .serializers import SalesOrderSerializer, SalesOrderCreateSerializer, SalesOrderCommentSerializer, SalesOrderHistorySerializer, DeliveryNoteSerializer, DeliveryNoteItemSerializer, DeliveryNoteCustomerAcknowledgementSerializer, DeliveryNoteAttachmentSerializer, DeliveryNoteRemarkSerializer, InvoiceSerializer, InvoiceItemSerializer, OrderSummarySerializer
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io
from django.utils import timezone

# Existing SalesOrder views
class SalesOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sales_orders = SalesOrder.objects.all().order_by('-created_at')
        serializer = SalesOrderSerializer(sales_orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SalesOrderCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            sales_order = serializer.save()
            return Response(SalesOrderSerializer(sales_order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

class SalesOrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            sales_order = SalesOrder.objects.get(id=pk)
            serializer = SalesOrderSerializer(sales_order)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            sales_order = SalesOrder.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'save_draft':
                sales_order.status = 'Draft'
            elif action == 'submit':
                sales_order.status = 'Submitted'
            elif action == 'submit_pd':
                sales_order.status = 'Submitted(PD)'
            elif action == 'cancel':
                sales_order.status = 'Cancelled'
            elif action == 'convert_to_delivery':
                return Response(self.convert_to_delivery_note(sales_order))
            elif action == 'convert_to_invoice':
                return Response(self.convert_to_invoice(sales_order))
            else:
                serializer = SalesOrderCreateSerializer(sales_order, data=request.data, partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return Response(SalesOrderSerializer(sales_order).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            sales_order.save()
            SalesOrderHistory.objects.create(sales_order=sales_order, action=action, user=request.user)
            return Response(SalesOrderSerializer(sales_order).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request, pk):
        try:
            sales_order = SalesOrder.objects.get(id=pk)
            sales_order.delete()
            return Response({'message': 'Sales Order deleted successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)

    def convert_to_delivery_note(self, sales_order):
        delivery_data = {
            'delivery_date': timezone.now().date(),
            'sales_order_reference': sales_order.id,
            'customer_name': sales_order.customer.name,
            'delivery_type': 'Regular',
            'destination_address': sales_order.customer.address,
            'delivery_status': 'Draft',
        }
        serializer = DeliveryNoteSerializer(data=delivery_data)
        if serializer.is_valid():
            delivery_note = serializer.save()
            for item in sales_order.items.all():
                item_data = {
                    'product': item.product.id,
                    'quantity': item.quantity,
                }
                item_serializer = DeliveryNoteItemSerializer(data=item_data)
                if item_serializer.is_valid():
                    delivery_item = item_serializer.save()
                    delivery_note.items.add(delivery_item)
            return DeliveryNoteSerializer(delivery_note).data
        return serializer.errors

    def convert_to_invoice(self, sales_order):
        invoice_data = {
            'invoice_date': timezone.now().date(),
            'due_date': timezone.now().date() + timezone.timedelta(days=30),
            'sales_order_reference': sales_order.id,
            'customer': sales_order.customer.id,
            'billing_address': sales_order.customer.address,
            'shipping_address': sales_order.customer.address,
            'email_id': sales_order.customer.email,
            'phone_number': sales_order.customer.phone_number,
            'payment_terms': 'Net 30',
            'currency': sales_order.currency,
        }
        serializer = InvoiceSerializer(data=invoice_data)
        if serializer.is_valid():
            invoice = serializer.save()
            for item in sales_order.items.all():
                item_data = {
                    'product': item.product.id,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'discount': item.discount,
                }
                item_serializer = InvoiceItemSerializer(data=item_data)
                if item_serializer.is_valid():
                    invoice_item = item_serializer.save()
                    invoice.items.add(invoice_item)
            summary_data = {'invoice': invoice.id, 'subtotal': sum(i.total for i in invoice.items.all())}
            OrderSummarySerializer().create(summary_data)
            return InvoiceSerializer(invoice).data
        return serializer.errors

class SalesOrderCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            sales_order = SalesOrder.objects.get(id=pk, sales_rep=request.user)
            comment_data = {'user': request.user, 'comment': request.data.get('comment')}
            comment = SalesOrderComment.objects.create(sales_order=sales_order, **comment_data)
            serializer = SalesOrderCommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        try:
            sales_order = SalesOrder.objects.get(id=pk, sales_rep=request.user)
            comments = sales_order.comments.all()
            serializer = SalesOrderCommentSerializer(comments, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)

class SalesOrderHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            sales_order = SalesOrder.objects.get(id=pk, sales_rep=request.user)
            history = sales_order.history.all()
            serializer = SalesOrderHistorySerializer(history, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)

class SalesOrderPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            sales_order = SalesOrder.objects.get(id=pk, sales_rep=request.user)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = [
                Paragraph(f"Sales Order ID: {sales_order.sales_order_id}", style={'fontName': 'Helvetica-Bold', 'fontSize': 14}),
                Paragraph(f"Date: {sales_order.order_date}", style={'fontName': 'Helvetica', 'fontSize': 12}),
                Paragraph(f"Customer: {sales_order.customer.name}", style={'fontName': 'Helvetica', 'fontSize': 12}),
            ]
            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="sales_order_{sales_order.sales_order_id}.pdf"'
            return response
        except ObjectDoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)

class SalesOrderEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            sales_order = SalesOrder.objects.get(id=pk, sales_rep=request.user)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            subject = f'Sales Order {sales_order.sales_order_id}'
            html_message = render_to_string('sales_order_email_template.html', {'sales_order': sales_order})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Sales Order not found'}, status=status.HTTP_404_NOT_FOUND)

# Existing DeliveryNote views
class DeliveryNoteListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        delivery_notes = DeliveryNote.objects.all().order_by('-delivery_date')
        serializer = DeliveryNoteSerializer(delivery_notes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DeliveryNoteSerializer(data=request.data)
        if serializer.is_valid():
            delivery_note = serializer.save()
            return Response(DeliveryNoteSerializer(delivery_note).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeliveryNoteDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            delivery_note = DeliveryNote.objects.get(id=pk)
            serializer = DeliveryNoteSerializer(delivery_note)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            delivery_note = DeliveryNote.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'cancel_dn':
                delivery_note.delete()
            elif action == 'cancel':
                delivery_note.delivery_status = 'Cancelled'
            elif action == 'save_draft':
                delivery_note.delivery_status = 'Draft'
            elif action == 'convert_to_invoice':
                return Response(self.convert_to_invoice_from_delivery(delivery_note))
            else:
                serializer = DeliveryNoteSerializer(delivery_note, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(DeliveryNoteSerializer(delivery_note).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            delivery_note.save()
            return Response(DeliveryNoteSerializer(delivery_note).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note not found'}, status=status.HTTP_404_NOT_FOUND)

    def convert_to_invoice_from_delivery(self, delivery_note):
        invoice_data = {
            'invoice_date': timezone.now().date(),
            'due_date': timezone.now().date() + timezone.timedelta(days=30),
            'sales_order_reference': delivery_note.sales_order_reference.id,
            'customer': delivery_note.sales_order_reference.customer.id,
            'billing_address': delivery_note.sales_order_reference.customer.address,
            'shipping_address': delivery_note.destination_address,
            'email_id': delivery_note.sales_order_reference.customer.email,
            'phone_number': delivery_note.sales_order_reference.customer.phone_number,
            'payment_terms': 'Net 30',
            'currency': delivery_note.sales_order_reference.currency,
        }
        serializer = InvoiceSerializer(data=invoice_data)
        if serializer.is_valid():
            invoice = serializer.save()
            for item in delivery_note.items.all():
                item_data = {
                    'product': item.product.id,
                    'quantity': item.quantity,
                    'unit_price': item.product.unit_price or 0.00,
                    'discount': item.product.discount or 0.00,
                }
                item_serializer = InvoiceItemSerializer(data=item_data)
                if item_serializer.is_valid():
                    invoice_item = item_serializer.save()
                    invoice.items.add(invoice_item)
            summary_data = {'invoice': invoice.id, 'subtotal': sum(i.total for i in invoice.items.all())}
            OrderSummarySerializer().create(summary_data)
            return InvoiceSerializer(invoice).data
        return serializer.errors

class DeliveryNoteItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            delivery_note = DeliveryNote.objects.get(id=pk)
            item_data = request.data
            item_data['delivery_note'] = pk
            serializer = DeliveryNoteItemSerializer(data=item_data)
            if serializer.is_valid():
                item = serializer.save()
                delivery_note.items.add(item)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note not found'}, status=status.HTTP_404_NOT_FOUND)

from purchase.models import SerialNumber
from purchase.serializers import SerialNumber,SerialNumberSerializer
class DeliveryNoteSerialNumbersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, item_pk):
        try:
            delivery_note_item = DeliveryNoteItem.objects.get(id=item_pk, delivery_note_id=pk)
            available_serials = SerialNumber.objects.filter(product=delivery_note_item.product).exclude(
                id__in=delivery_note_item.serial_numbers.values('id')
            )[:delivery_note_item.quantity - delivery_note_item.serial_numbers.count()]
            serializer = SerialNumberSerializer(available_serials, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note Item or Serial Numbers not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk, item_pk):
        try:
            delivery_note_item = DeliveryNoteItem.objects.get(id=item_pk, delivery_note_id=pk)
            serial_ids = request.data.get('serial_numbers', [])
            if len(serial_ids) <= delivery_note_item.quantity - delivery_note_item.serial_numbers.count():
                delivery_note_item.serial_numbers.add(*serial_ids)
                return Response({'message': 'Serial numbers added'}, status=status.HTTP_200_OK)
            return Response({'error': 'Exceeds quantity limit'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note Item not found'}, status=status.HTTP_404_NOT_FOUND)

class DeliveryNotePDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            delivery_note = DeliveryNote.objects.get(id=pk)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = [
                Paragraph(f"DN ID: {delivery_note.DN_ID}", style={'fontName': 'Helvetica-Bold', 'fontSize': 14}),
                Paragraph(f"Date: {delivery_note.delivery_date}", style={'fontName': 'Helvetica', 'fontSize': 12}),
                Paragraph(f"Customer: {delivery_note.customer_name}", style={'fontName': 'Helvetica', 'fontSize': 12}),
            ]
            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="delivery_note_{delivery_note.DN_ID}.pdf"'
            return response
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note not found'}, status=status.HTTP_404_NOT_FOUND)

class DeliveryNoteEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            delivery_note = DeliveryNote.objects.get(id=pk)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            subject = f'Delivery Note {delivery_note.DN_ID}'
            html_message = render_to_string('delivery_note_email_template.html', {'delivery_note': delivery_note})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note not found'}, status=status.HTTP_404_NOT_FOUND)

# New Invoice views
class InvoiceListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invoices = Invoice.objects.all().order_by('-invoice_date')
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InvoiceSerializer(data=request.data)
        if serializer.is_valid():
            invoice = serializer.save()
            return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InvoiceDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            invoice = Invoice.objects.get(id=pk)
            serializer = InvoiceSerializer(invoice)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            invoice = Invoice.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'cancel_invoice':
                invoice.delete()
            elif action == 'cancel':
                invoice.invoice_status = 'Cancelled'
            elif action == 'save_draft':
                invoice.invoice_status = 'Draft'
            elif action == 'send_invoice':
                invoice.invoice_status = 'Sent'
            elif action == 'mark_as_paid':
                invoice.payment_status = 'Paid'
            else:
                serializer = InvoiceSerializer(invoice, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            invoice.save()
            if invoice.summary:
                invoice.summary.save()
            return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

class InvoiceItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            invoice = Invoice.objects.get(id=pk)
            item_data = request.data
            item_data['invoice'] = pk
            serializer = InvoiceItemSerializer(data=item_data)
            if serializer.is_valid():
                item = serializer.save()
                invoice.items.add(item)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

class InvoicePDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            invoice = Invoice.objects.get(id=pk)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = [
                Paragraph(f"Invoice ID: {invoice.INVOICE_ID}", style={'fontName': 'Helvetica-Bold', 'fontSize': 14}),
                Paragraph(f"Date: {invoice.invoice_date}", style={'fontName': 'Helvetica', 'fontSize': 12}),
                Paragraph(f"Customer: {invoice.customer.name}", style={'fontName': 'Helvetica', 'fontSize': 12}),
            ]
            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.INVOICE_ID}.pdf"'
            return response
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

class InvoiceEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            invoice = Invoice.objects.get(id=pk)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            subject = f'Invoice {invoice.INVOICE_ID}'
            html_message = render_to_string('invoice_email_template.html', {'invoice': invoice})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
        


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io
from .models import InvoiceReturn, InvoiceReturnItem, InvoiceReturnAttachment, InvoiceReturnRemark, InvoiceReturnSummary, InvoiceReturnHistory, InvoiceReturnComment
from .serializers import InvoiceReturnSerializer, InvoiceReturnItemSerializer, InvoiceReturnAttachmentSerializer, InvoiceReturnRemarkSerializer, InvoiceReturnSummarySerializer, InvoiceReturnHistorySerializer, InvoiceReturnCommentSerializer

class InvoiceReturnListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invoice_returns = InvoiceReturn.objects.all().order_by('-invoice_return_date')
        status_filter = request.query_params.get('status', 'All')
        customer_filter = request.query_params.get('customer', 'All')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if status_filter != 'All':
            invoice_returns = invoice_returns.filter(status=status_filter)
        if customer_filter != 'All':
            invoice_returns = invoice_returns.filter(customer__name__icontains=customer_filter)
        if date_from:
            invoice_returns = invoice_returns.filter(invoice_return_date__gte=date_from)
        if date_to:
            invoice_returns = invoice_returns.filter(invoice_return_date__lte=date_to)
        serializer = InvoiceReturnSerializer(invoice_returns, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InvoiceReturnSerializer(data=request.data)
        if serializer.is_valid():
            invoice_return = serializer.save()
            return Response(InvoiceReturnSerializer(invoice_return).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InvoiceReturnDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            invoice_return = InvoiceReturn.objects.get(id=pk)
            serializer = InvoiceReturnSerializer(invoice_return)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice Return not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            invoice_return = InvoiceReturn.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'cancel':
                invoice_return.status = 'Cancelled'
            elif action == 'save_draft':
                invoice_return.status = 'Draft'
            elif action == 'submit':
                invoice_return.status = 'Submitted'
            else:
                serializer = InvoiceReturnSerializer(invoice_return, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(InvoiceReturnSerializer(invoice_return).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            invoice_return.save()
            if invoice_return.summary:
                invoice_return.summary.save()
            return Response(InvoiceReturnSerializer(invoice_return).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice Return not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            invoice_return = InvoiceReturn.objects.get(id=pk)
            invoice_return.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice Return not found'}, status=status.HTTP_404_NOT_FOUND)

class InvoiceReturnItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            invoice_return = InvoiceReturn.objects.get(id=pk)
            item_data = request.data
            item_data['invoice_return'] = pk
            serializer = InvoiceReturnItemSerializer(data=item_data)
            if serializer.is_valid():
                item = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice Return not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, item_pk):
        try:
            item = InvoiceReturnItem.objects.get(id=item_pk, invoice_return_id=pk)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice Return Item not found'}, status=status.HTTP_404_NOT_FOUND)

class InvoiceReturnPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            invoice_return = InvoiceReturn.objects.get(id=pk)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = [
                Paragraph(f"Invoice Return ID: {invoice_return.INVOICE_RETURN_ID}", style={'fontName': 'Helvetica-Bold', 'fontSize': 14}),
                Paragraph(f"Date: {invoice_return.invoice_return_date}", style={'fontName': 'Helvetica', 'fontSize': 12}),
                Paragraph(f"Customer: {invoice_return.customer.name}", style={'fontName': 'Helvetica', 'fontSize': 12}),
            ]
            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_return_{invoice_return.INVOICE_RETURN_ID}.pdf"'
            return response
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice Return not found'}, status=status.HTTP_404_NOT_FOUND)

class InvoiceReturnEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            invoice_return = InvoiceReturn.objects.get(id=pk)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            subject = f'Invoice Return {invoice_return.INVOICE_RETURN_ID}'
            html_message = render_to_string('invoice_return_email.html', {'invoice_return': invoice_return})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Invoice Return not found'}, status=status.HTTP_404_NOT_FOUND)
        


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io
from .models import DeliveryNoteReturn, DeliveryNoteReturnItem, DeliveryNoteReturnAttachment, DeliveryNoteReturnRemark, DeliveryNoteReturnHistory, DeliveryNoteReturnComment
from .serializers import DeliveryNoteReturnSerializer, DeliveryNoteReturnItemSerializer, DeliveryNoteReturnAttachmentSerializer, DeliveryNoteReturnRemarkSerializer, DeliveryNoteReturnHistorySerializer, DeliveryNoteReturnCommentSerializer

class DeliveryNoteReturnListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        returns = DeliveryNoteReturn.objects.all().order_by('-dnr_date')
        status_filter = request.query_params.get('status', 'All')
        customer_filter = request.query_params.get('customer', 'All')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if status_filter != 'All':
            returns = returns.filter(status=status_filter)
        if customer_filter != 'All':
            returns = returns.filter(customer__name__icontains=customer_filter)
        if date_from:
            returns = returns.filter(dnr_date__gte=date_from)
        if date_to:
            returns = returns.filter(dnr_date__lte=date_to)
        serializer = DeliveryNoteReturnSerializer(returns, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DeliveryNoteReturnSerializer(data=request.data)
        if serializer.is_valid():
            return_obj = serializer.save()
            return Response(DeliveryNoteReturnSerializer(return_obj).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeliveryNoteReturnDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            return_obj = DeliveryNoteReturn.objects.get(id=pk)
            serializer = DeliveryNoteReturnSerializer(return_obj)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note Return not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            return_obj = DeliveryNoteReturn.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'cancel':
                return_obj.status = 'Cancelled'
            elif action == 'save_draft':
                return_obj.status = 'Draft'
            elif action == 'submit':
                return_obj.status = 'Submitted'
            else:
                serializer = DeliveryNoteReturnSerializer(return_obj, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(DeliveryNoteReturnSerializer(return_obj).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return_obj.save()
            return Response(DeliveryNoteReturnSerializer(return_obj).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note Return not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            return_obj = DeliveryNoteReturn.objects.get(id=pk)
            return_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note Return not found'}, status=status.HTTP_404_NOT_FOUND)

class DeliveryNoteReturnItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            return_obj = DeliveryNoteReturn.objects.get(id=pk)
            item_data = request.data
            item_data['delivery_note_return'] = pk
            serializer = DeliveryNoteReturnItemSerializer(data=item_data)
            if serializer.is_valid():
                item = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note Return not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, item_pk):
        try:
            item = DeliveryNoteReturnItem.objects.get(id=item_pk, delivery_note_return_id=pk)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note Return Item not found'}, status=status.HTTP_404_NOT_FOUND)

class DeliveryNoteReturnPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            return_obj = DeliveryNoteReturn.objects.get(id=pk)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = [
                Paragraph(f"DNR ID: {return_obj.DNR_ID}", style={'fontName': 'Helvetica-Bold', 'fontSize': 14}),
                Paragraph(f"Date: {return_obj.dnr_date}", style={'fontName': 'Helvetica', 'fontSize': 12}),
                Paragraph(f"Customer: {return_obj.customer.name}", style={'fontName': 'Helvetica', 'fontSize': 12}),
            ]
            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="delivery_note_return_{return_obj.DNR_ID}.pdf"'
            return response
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note Return not found'}, status=status.HTTP_404_NOT_FOUND)

class DeliveryNoteReturnEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            return_obj = DeliveryNoteReturn.objects.get(id=pk)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            subject = f'Delivery Note Return {return_obj.DNR_ID}'
            html_message = render_to_string('delivery_note_return_email.html', {'delivery_note_return': return_obj})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Delivery Note Return not found'}, status=status.HTTP_404_NOT_FOUND)