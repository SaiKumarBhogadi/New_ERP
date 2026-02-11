from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Enquiry, EnquiryItem
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import RoleBasedPermission
from .models import Enquiry
from .serializers import EnquirySerializer, EnquiryWriteSerializer


class EnquiryListCreateView(generics.ListCreateAPIView):
    queryset = Enquiry.objects.select_related('user').order_by('-created_at')
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EnquirySerializer
        return EnquiryWriteSerializer

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.role.role.lower() == 'admin':
            return Enquiry.objects.all()
        return Enquiry.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Enquiries fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        detail_serializer = EnquirySerializer(instance, context={'request': request})
        return Response({
            "message": "Enquiry created successfully",
            "data": detail_serializer.data
        }, status=status.HTTP_201_CREATED)


class EnquiryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enquiry.objects.select_related('user')
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EnquirySerializer
        return EnquiryWriteSerializer

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.role.role.lower() == 'admin':
            return Enquiry.objects.all()
        return Enquiry.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Enquiry fetched successfully",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)  # partial update works perfectly
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Enquiry updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Enquiry deleted successfully"
        })

# views.py (replace relevant parts)

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import RoleBasedPermission
from rest_framework.views import APIView
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from .models import Quotation, QuotationItem, QuotationAttachment, QuotationComment, QuotationHistory, QuotationRevision
from .serializers import QuotationSerializer, QuotationWriteSerializer, QuotationRevisionSerializer

class QuotationListCreateView(generics.ListCreateAPIView):
    queryset = Quotation.objects.select_related('customer', 'sales_rep').order_by('-created_at')
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get_queryset(self):
        expired = self.queryset.filter(
            expiry_date__lt=timezone.now().date(),
            status__in=['Draft', 'Submitted', 'Approved']
        )
        expired.update(status='Expired')
        return self.queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return QuotationWriteSerializer
        return QuotationSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Quotations fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })

    def create(self, request, *args, **kwargs):
        write_serializer = QuotationWriteSerializer(
            data=request.data,
            context={'request': request}
        )
        write_serializer.is_valid(raise_exception=True)
        quotation = write_serializer.save()

        read_serializer = QuotationSerializer(quotation)
        return Response({
            "message": "Quotation created successfully",
            "data": read_serializer.data
        }, status=201)


class QuotationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quotation.objects.select_related('customer', 'sales_rep')
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return QuotationSerializer
        return QuotationWriteSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Quotation fetched successfully",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = QuotationWriteSerializer(
            instance,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        quotation = serializer.save()

        return Response({
            "message": "Quotation updated successfully"
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Quotation deleted successfully"
        })


class QuotationActionView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk)
            action = request.data.get('action')

            allowed_transitions = {
                'Draft': ['save_draft', 'submit'],
                'Submitted': ['approve', 'reject', 'revise'],
                'Approved': ['convert_to_so'],
                'Rejected': [],
                'Converted to SO': [],
                'Expired': []
            }

            if action not in allowed_transitions.get(quotation.status, []):
                return Response({'message': f'Action {action} not allowed in {quotation.status} state'}, status=400)

            old_status = quotation.status

            message = "Action performed successfully"

            if action == 'save_draft':
                quotation.status = 'Draft'
                message = "Quotation saved as draft"
            elif action == 'submit':
                quotation.status = 'Submitted'
                message = "Quotation submitted successfully"
            elif action == 'approve':
                quotation.status = 'Approved'
                message = "Quotation approved successfully"
            elif action == 'reject':
                quotation.status = 'Rejected'
                message = "Quotation rejected successfully"
            elif action == 'convert_to_so':
                quotation.status = 'Converted to SO'
                message = "Quotation converted to Sales Order successfully"
            elif action == 'revise':
                revision_no = quotation.revise_count + 1
                QuotationRevision.objects.create(
                    quotation=quotation,
                    revision_no=revision_no,
                    created_by=request.user,
                    comment=request.data.get('comment', ''),
                    status='Submitted'
                )
                quotation.revise_count = revision_no
                quotation.status = 'Submitted'
                message = "Quotation revised successfully"

            quotation.updated_by = request.user
            quotation.save()

            if quotation.status != old_status:
                QuotationHistory.objects.create(
                    quotation=quotation,
                    event_type='status_change',
                    status=quotation.status,
                    action_by=request.user
                )

            return Response({"message": message})
        except Quotation.DoesNotExist:
            return Response({'message': 'Quotation not found'}, status=404)


from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from .models import QuotationAttachment, Quotation
from .serializers import QuotationAttachmentSerializer


class QuotationAttachmentView(generics.ListCreateAPIView):
    serializer_class = QuotationAttachmentSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        quotation_id = self.kwargs['pk']
        return QuotationAttachment.objects.filter(quotation_id=quotation_id)

    def perform_create(self, serializer):
        quotation = Quotation.objects.get(id=self.kwargs['pk'])
        serializer.save(
            quotation=quotation,
            uploaded_by=self.request.user
        )

class QuotationAttachmentDeleteView(generics.DestroyAPIView):
    queryset = QuotationAttachment.objects.all()
    serializer_class = QuotationAttachmentSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]


class QuotationPDFView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk)
            context = {
                'quotation': quotation,
                'items': quotation.items.all(),
                'subtotal': quotation.subtotal,
                'tax_summary': quotation.tax_summary,
                'global_discount': quotation.global_discount,
                'shipping_charges': quotation.shipping_charges,
                'rounding_adjustment': quotation.rounding_adjustment,
                'grand_total': quotation.grand_total,
                'comments': quotation.comments.all(),
                'history': quotation.history.all(),
                'revisions': quotation.revisions.all()
            }

            html_string = render_to_string('quotation_pdf.html', context)
            html = HTML(string=html_string, base_url=request.build_absolute_uri())
            pdf_buffer = BytesIO()
            html.write_pdf(pdf_buffer)

            # Log PDF generation
            QuotationHistory.objects.create(
                quotation=quotation,
                event_type='pdf_generated',
                action_by=request.user
            )

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Quotation_{quotation.quotation_id}.pdf"'
            response.write(pdf_buffer.getvalue())
            return response
        except Quotation.DoesNotExist:
            return Response({'error': 'Quotation not found'}, status=404)


class QuotationMailView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.get(id=pk)
            recipient = request.data.get('email', quotation.customer.email)

            context = {
                'quotation': quotation,
                'items': quotation.items.all(),
                'subtotal': quotation.subtotal,
                'tax_summary': quotation.tax_summary,
                'grand_total': quotation.grand_total
            }

            html_message = render_to_string('quotation_email.html', context)

            email = EmailMessage(
                subject=f'Quotation {quotation.quotation_id}',
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient]
            )
            email.content_subtype = 'html'
            email.send()

            # Log email sent
            QuotationHistory.objects.create(
                quotation=quotation,
                event_type='email_sent',
                extra_info=f"sent to {recipient}",
                action_by=request.user
            )

            return Response({'message': 'Email sent successfully'}, status=200)
        except Quotation.DoesNotExist:
            return Response({'error': 'Quotation not found'}, status=404)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import SalesOrder, SalesOrderItem, SalesOrderComment, SalesOrderHistory, DeliveryNote, DeliveryNoteItem, DeliveryNoteCustomerAcknowledgement, DeliveryNoteAttachment, DeliveryNoteRemark, Invoice, InvoiceItem, InvoiceAttachment, InvoiceRemark, OrderSummary
from .serializers import  SalesOrderHistorySerializer, DeliveryNoteSerializer, DeliveryNoteItemSerializer, DeliveryNoteCustomerAcknowledgementSerializer, DeliveryNoteAttachmentSerializer, DeliveryNoteRemarkSerializer, InvoiceSerializer, InvoiceItemSerializer, OrderSummarySerializer
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io
from django.utils import timezone
# views.py

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.utils import timezone

from io import BytesIO
from weasyprint import HTML

from .models import SalesOrder, SalesOrderHistory
from .serializers import SalesOrderSerializer, SalesOrderWriteSerializer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from core.permissions import RoleBasedPermission  

# Placeholder for PurchaseOrder generation (to be implemented later)
def generate_purchase_order(sales_order, partial=False):
    # TODO: Implement full PurchaseOrder creation logic
    # For insufficient items, create PO for (quantity - product.quantity_in_stock)
    # If partial, create for partial quantities or handle differently
    insufficient = []
    for item in sales_order.items.all():
        available = item.product.quantity # Assuming field exists in Product model
        if available < item.quantity:
            deficient = item.quantity - available if not partial else item.quantity  # Adjust logic as needed for partial
            insufficient.append({'product': item.product, 'quantity': deficient})
    
    # Create PurchaseOrder with insufficient items
    # Example placeholder:
    # from purchases.models import PurchaseOrder, PurchaseOrderItem  # Assume imports
    # purchase_order = PurchaseOrder.objects.create(...)  # Fill with relevant data from sales_order
    # for def_item in insufficient:
    #     PurchaseOrderItem.objects.create(purchase_order=purchase_order, **def_item)
    
    # Return purchase_order or success message
    return {'message': f'Purchase Order generated ({"partial" if partial else "full"} placeholder)'}

# Placeholder for DeliveryNote generation
def generate_delivery_note(sales_order):
    # TODO: Implement full DeliveryNote creation
    # from deliveries.models import DeliveryNote, DeliveryNoteItem  # Assume
    # delivery_note = DeliveryNote.objects.create(
    #     delivery_date=timezone.now().date(),
    #     sales_order=sales_order,
    #     customer=sales_order.customer,
    #     # ... other fields
    # )
    # for item in sales_order.items.all():
    #     DeliveryNoteItem.objects.create(
    #         delivery_note=delivery_note,
    #         product=item.product,
    #         quantity=item.quantity
    #     )
    # Update inventory, etc.
    return {'message': 'Delivery Note generated (placeholder)'}

# Placeholder for Invoice generation
def generate_invoice(sales_order):
    # TODO: Implement full Invoice creation
    # from invoices.models import Invoice, InvoiceItem  # Assume
    # invoice = Invoice.objects.create(
    #     invoice_date=timezone.now().date(),
    #     due_date=sales_order.due_date,
    #     sales_order=sales_order,
    #     customer=sales_order.customer,
    #     # ... other fields
    # )
    # for item in sales_order.items.all():
    #     InvoiceItem.objects.create(
    #         invoice=invoice,
    #         product=item.product,
    #         quantity=item.quantity,
    #         unit_price=item.unit_price,
    #         discount=item.discount,
    #         tax=item.tax
    #     )
    # Calculate summary, etc.
    return {'message': 'Invoice generated (placeholder)'}

class SalesOrderListCreateView(generics.ListCreateAPIView):
    queryset = SalesOrder.objects.select_related('customer', 'sales_rep').order_by('-created_at')
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SalesOrderWriteSerializer
        return SalesOrderSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('limit', 10))

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.get_serializer(page, many=True)

        from_count = (page.number - 1) * page_size + 1
        to_count = from_count + len(page.object_list) - 1 if page.object_list else 0

        return Response({
            "message": "Sales Orders fetched successfully",
            "data": {
                "from": from_count,
                "to": to_count,
                "totalCount": paginator.count,
                "totalPages": paginator.num_pages,
                "data": serializer.data
            }
        })

    def create(self, request, *args, **kwargs):
        write_serializer = SalesOrderWriteSerializer(
            data=request.data,
            context={'request': request}
        )
        write_serializer.is_valid(raise_exception=True)
        sales_order = write_serializer.save()

        read_serializer = SalesOrderSerializer(sales_order)
        return Response({
            "message": "Sales Order created successfully",
            "data": read_serializer.data
        }, status=status.HTTP_201_CREATED)


class SalesOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SalesOrder.objects.select_related('customer', 'sales_rep')
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SalesOrderSerializer
        return SalesOrderWriteSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Sales Order fetched successfully",
            "data": serializer.data
        })

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SalesOrderWriteSerializer(
            instance,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        sales_order = serializer.save()
        return Response({
            "message": "Sales Order updated successfully"
        })


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Sales Order deleted successfully"
        })


class SalesOrderActionView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request, pk):
        sales_order = get_object_or_404(SalesOrder, id=pk)
        action = request.data.get('action')

        allowed_transitions = {
            'Draft': ['save_draft', 'submit', 'submit_pd', 'cancel', 'generate_po'],
            'Ready to Submit': ['submit', 'submit_pd', 'cancel'],
            'Submitted': ['convert_to_delivery', 'convert_to_invoice', 'cancel'],
            'Submitted(PD)': ['convert_to_delivery', 'convert_to_invoice', 'cancel'],
            'Partially Delivered': ['convert_to_delivery', 'convert_to_invoice'],
            'Delivered': [],
            'Cancelled': [],
        }

        if action not in allowed_transitions.get(sales_order.status, []):
            return Response({'error': f'Action {action} not allowed in {sales_order.status} state'}, status=400)

        old_status = sales_order.status

        if action == 'save_draft':
            sales_order.status = 'Draft'
        elif action == 'submit':
            insufficient = []
            for item in sales_order.items.all():
                available = item.product.quantity  # Assuming field
                if available < item.quantity:
                    insufficient.append({
                        'product': item.product.id,
                        'required': item.quantity,
                        'available': available
                    })
            if insufficient:
                return Response({'error': 'insufficient_stock', 'details': insufficient}, status=400)
            sales_order.status = 'Submitted'
        elif action == 'submit_pd':
            # For partial, assume some logic, perhaps no full check
            sales_order.status = 'Submitted(PD)'
        elif action == 'cancel':
            sales_order.status = 'Cancelled'
        elif action == 'generate_po':
            partial = request.data.get('partial', False)
            result = generate_purchase_order(sales_order, partial)
            SalesOrderHistory.objects.create(
                sales_order=sales_order,
                event_type='po_generated',
                extra_info=str(result),
                action_by=request.user
            )
            sales_order.status = 'Ready to Submit'  # After PO, ready to submit again
        elif action == 'convert_to_delivery':
            result = generate_delivery_note(sales_order)
            # Update status based on full or partial
            sales_order.status = 'Delivered' if sales_order.status == 'Submitted' else 'Partially Delivered'
            # Log if needed
        elif action == 'convert_to_invoice':
            result = generate_invoice(sales_order)
            # No status change assumed, or adjust as needed

        sales_order.updated_by = request.user
        sales_order.save()

        if sales_order.status != old_status:
            SalesOrderHistory.objects.create(
                sales_order=sales_order,
                event_type='status_change',
                status=sales_order.status,
                action_by=request.user
            )

        return Response(SalesOrderSerializer(sales_order).data, status=200)


class SalesOrderPDFView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get(self, request, pk):
        sales_order = get_object_or_404(SalesOrder, id=pk)
        context = {
            'sales_order': sales_order,
            'items': sales_order.items.all(),
            'subtotal': sales_order.subtotal,
            'tax_summary': sales_order.tax_summary,
            'global_discount': sales_order.global_discount,
            'shipping_charges': sales_order.shipping_charges,
            'rounding_adjustment': sales_order.rounding_adjustment,
            'grand_total': sales_order.grand_total,
            'comments': sales_order.comments.all(),
            'history': sales_order.history.all()
        }

        html_string = render_to_string('sales_order_pdf.html', context)  # Assume template exists
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf_buffer = BytesIO()
        html.write_pdf(pdf_buffer)

        SalesOrderHistory.objects.create(
            sales_order=sales_order,
            event_type='pdf_generated',
            action_by=request.user
        )

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="SalesOrder_{sales_order.sales_order_id}.pdf"'
        response.write(pdf_buffer.getvalue())
        return response


class SalesOrderMailView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request, pk):
        sales_order = get_object_or_404(SalesOrder, id=pk)
        recipient = request.data.get('email', sales_order.customer.email)  # Assume customer has email

        context = {
            'sales_order': sales_order,
            'items': sales_order.items.all(),
            'subtotal': sales_order.subtotal,
            'tax_summary': sales_order.tax_summary,
            'grand_total': sales_order.grand_total
        }

        html_message = render_to_string('sales_order_email.html', context)  # Assume template

        email = EmailMessage(
            subject=f'Sales Order {sales_order.sales_order_id}',
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        email.content_subtype = 'html'
        email.send()

        SalesOrderHistory.objects.create(
            sales_order=sales_order,
            event_type='email_sent',
            extra_info=f"sent to {recipient}",
            action_by=request.user
        )

        return Response({'message': 'Email sent successfully'}, status=200)




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