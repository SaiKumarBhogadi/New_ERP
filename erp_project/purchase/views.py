from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import PurchaseOrder,  PurchaseOrderHistory
from .serializers import PurchaseOrderSerializer, PurchaseOrderItemSerializer, PurchaseOrderHistorySerializer, PurchaseOrderCommentSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from reportlab.lib import colors
# from reportlab.lib.pagesizes = letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io

class PurchaseOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        purchase_orders = PurchaseOrder.objects.all().order_by('-PO_date')
        serializer = PurchaseOrderSerializer(purchase_orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            purchase_order = serializer.save()
            return Response(PurchaseOrderSerializer(purchase_order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PurchaseOrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            purchase_order = PurchaseOrder.objects.get(id=pk)
            serializer = PurchaseOrderSerializer(purchase_order)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            purchase_order = PurchaseOrder.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'submit_draft':
                purchase_order.status = 'Submitted'
            elif action == 'cancel':
                purchase_order.status = 'Canceled'
            else:
                serializer = PurchaseOrderSerializer(purchase_order, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(PurchaseOrderSerializer(purchase_order).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            purchase_order.save()
            PurchaseOrderHistory.objects.create(purchase_order=purchase_order, action=action, performed_by=request.user.username)
            return Response(PurchaseOrderSerializer(purchase_order).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)

class PurchaseOrderItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            purchase_order = PurchaseOrder.objects.get(id=pk)
            item_data = request.data
            item_data['purchase_order'] = pk
            serializer = PurchaseOrderItemSerializer(data=item_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)

class PurchaseOrderHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            purchase_order = PurchaseOrder.objects.get(id=pk)
            history = purchase_order.history.all()
            serializer = PurchaseOrderHistorySerializer(history, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        try:
            purchase_order = PurchaseOrder.objects.get(id=pk)
            history_data = request.data
            history_data['purchase_order'] = pk
            serializer = PurchaseOrderHistorySerializer(data=history_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)

class PurchaseOrderCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            purchase_order = PurchaseOrder.objects.get(id=pk)
            comments = purchase_order.comments.all()
            serializer = PurchaseOrderCommentSerializer(comments, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        try:
            purchase_order = PurchaseOrder.objects.get(id=pk)
            comment_data = request.data
            comment_data['purchase_order'] = pk
            serializer = PurchaseOrderCommentSerializer(data=comment_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)

# class PurchaseOrderPDFView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, pk):
#         try:
#             purchase_order = PurchaseOrder.objects.get(id=pk)
#             buffer = io.BytesIO()
#             doc = SimpleDocTemplate(buffer, pagesize=letter)
#             elements = []

#             data = [
#                 ['PO ID', purchase_order.PO_ID],
#                 ['PO Date', purchase_order.PO_date],
#                 ['Supplier', purchase_order.supplier_name],
#                 ['Total', purchase_order.total_order_value],
#             ]
#             table = Table(data)
#             table.setStyle(TableStyle([
#                 ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#                 ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                 ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                 ('FONTSIZE', (0, 0), (-1, 0), 14),
#                 ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                 ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                 ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
#                 ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
#                 ('FONTSIZE', (0, 1), (-1, -1), 12),
#             ]))
#             elements.append(table)

#             doc.build(elements)
#             buffer.seek(0)
#             response = HttpResponse(buffer, content_type='application/pdf')
#             response['Content-Disposition'] = f'attachment; filename="purchase_order_{purchase_order.PO_ID}.pdf"'
#             return response
#         except ObjectDoesNotExist:
#             return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PurchaseOrderEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            purchase_order = PurchaseOrder.objects.get(id=pk)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

            subject = f'Purchase Order {purchase_order.PO_ID}'
            html_message = render_to_string('purchase_order_email_template.html', {'purchase_order': purchase_order})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import StockReceipt, StockReceiptItem, SerialNumber, BatchNumber, BatchSerialNumber, StockReceiptRemark, StockReceiptAttachment
from .serializers import StockReceiptSerializer, StockReceiptItemSerializer, SerialNumberSerializer, BatchNumberSerializer, StockReceiptAttachmentSerializer, StockReceiptRemarkSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io

class StockReceiptListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stock_receipts = StockReceipt.objects.all().order_by('-received_date')
        serializer = StockReceiptSerializer(stock_receipts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StockReceiptSerializer(data=request.data)
        if serializer.is_valid():
            stock_receipt = serializer.save()
            return Response(StockReceiptSerializer(stock_receipt).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StockReceiptDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            stock_receipt = StockReceipt.objects.get(id=pk)
            serializer = StockReceiptSerializer(stock_receipt)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Receipt not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            stock_receipt = StockReceipt.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'cancel':
                stock_receipt.status = 'Cancelled'
            else:
                serializer = StockReceiptSerializer(stock_receipt, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(StockReceiptSerializer(stock_receipt).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            stock_receipt.save()
            return Response(StockReceiptSerializer(stock_receipt).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Receipt not found'}, status=status.HTTP_404_NOT_FOUND)

class StockReceiptItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            stock_receipt = StockReceipt.objects.get(id=pk)
            item_data = request.data
            item_data['stock_receipt'] = pk
            serializer = StockReceiptItemSerializer(data=item_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Receipt not found'}, status=status.HTTP_404_NOT_FOUND)

class SerialNumberListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, item_pk):
        try:
            stock_receipt_item = StockReceiptItem.objects.get(id=item_pk, stock_receipt_id=pk)
            serial_numbers = stock_receipt_item.serial_numbers.all()
            serializer = SerialNumberSerializer(serial_numbers, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Receipt Item or Serial Numbers not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk, item_pk):
        try:
            stock_receipt_item = StockReceiptItem.objects.get(id=item_pk, stock_receipt_id=pk)
            serializer = SerialNumberSerializer(data=request.data, many=True, context={'stock_receipt_item': stock_receipt_item})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Receipt Item not found'}, status=status.HTTP_404_NOT_FOUND)

class BatchNumberListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, item_pk):
        try:
            stock_receipt_item = StockReceiptItem.objects.get(id=item_pk, stock_receipt_id=pk)
            batch_numbers = stock_receipt_item.batch_numbers.all()
            serializer = BatchNumberSerializer(batch_numbers, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Receipt Item or Batch Numbers not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk, item_pk):
        try:
            stock_receipt_item = StockReceiptItem.objects.get(id=item_pk, stock_receipt_id=pk)
            serializer = BatchNumberSerializer(data=request.data, many=True, context={'stock_receipt_item': stock_receipt_item})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Receipt Item not found'}, status=status.HTTP_404_NOT_FOUND)

class StockReceiptPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            stock_receipt = StockReceipt.objects.get(id=pk)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            header_data = [
                ['GRN ID', stock_receipt.GRN_ID],
                ['Received Date', stock_receipt.received_date],
                ['Supplier', stock_receipt.supplier.name if stock_receipt.supplier else 'N/A'],
                ['Total Items', len(stock_receipt.items.all())],
            ]
            header_table = Table(header_data)
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
            ]))
            elements.append(header_table)

            items_data = [['Product', 'UOM', 'Qty Ordered', 'Qty Received', 'Accepted Qty', 'Unit Price', 'Tax (%)', 'Discount (%)', 'Total', 'Serials', 'Batches']]
            for item in stock_receipt.items.all():
                serials = ', '.join(sn.serial_no for sn in item.serial_numbers.all()) if item.serial_numbers.exists() else 'N/A'
                batches = ', '.join(bn.batch_no for bn in item.batch_numbers.all()) if item.batch_numbers.exists() else 'N/A'
                items_data.append([
                    item.product.name if item.product else 'N/A',
                    item.uom,
                    item.qty_ordered or 0,
                    item.qty_received,
                    item.accepted_qty,
                    f"{item.unit_price:.2f}",
                    f"{item.tax:.2f}",
                    f"{item.discount:.2f}",
                    f"{item.total:.2f}",
                    serials,
                    batches
                ])
            items_table = Table(items_data)
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(items_table)

            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="stock_receipt_{stock_receipt.GRN_ID}.pdf"'
            return response
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Receipt not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StockReceiptEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            stock_receipt = StockReceipt.objects.get(id=pk)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

            subject = f'Stock Receipt {stock_receipt.GRN_ID}'
            html_message = render_to_string('stock_receipt_email_template.html', {'stock_receipt': stock_receipt})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Receipt not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import StockReturn, StockReturnItem, SerialNumberReturn, StockReturnRemark, StockReturnAttachment
from .serializers import StockReturnSerializer, StockReturnItemSerializer, SerialNumberReturnSerializer, StockReturnAttachmentSerializer, StockReturnRemarkSerializer
from .models import StockReceiptItem, SerialNumber
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io

class StockReturnListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stock_returns = StockReturn.objects.all().order_by('-return_date')
        serializer = StockReturnSerializer(stock_returns, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StockReturnSerializer(data=request.data)
        if serializer.is_valid():
            stock_return = serializer.save()
            return Response(StockReturnSerializer(stock_return).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StockReturnDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            stock_return = StockReturn.objects.get(id=pk)
            serializer = StockReturnSerializer(stock_return)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Return not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            stock_return = StockReturn.objects.get(id=pk)
            action = request.data.get('action')
            if action == 'cancel':
                stock_return.status = 'Cancelled'
            else:
                serializer = StockReturnSerializer(stock_return, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(StockReturnSerializer(stock_return).data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            stock_return.save()
            return Response(StockReturnSerializer(stock_return).data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Return not found'}, status=status.HTTP_404_NOT_FOUND)

class StockReturnItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            stock_return = StockReturn.objects.get(id=pk)
            item_data = request.data
            item_data['stock_return'] = pk
            serializer = StockReturnItemSerializer(data=item_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Return not found'}, status=status.HTTP_404_NOT_FOUND)

class SerialNumberReturnListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, item_pk):
        try:
            stock_return_item = StockReturnItem.objects.get(id=item_pk, stock_return_id=pk)
            if stock_return_item.stock_receipt_item and stock_return_item.stock_receipt_item.stock_dim == 'Serial':
                available_serials = SerialNumber.objects.filter(stock_receipt_item=stock_return_item.stock_receipt_item).exclude(
                    id__in=SerialNumberReturn.objects.filter(stock_return_item=stock_return_item).values('serial_no')
                )
                serializer = SerialNumberReturnSerializer(available_serials, many=True, context={'stock_return_item': stock_return_item})
                return Response(serializer.data)
            return Response({'error': 'No serial numbers available or item not serial-tracked'}, status=status.HTTP_404_NOT_FOUND)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Return Item or Serial Numbers not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk, item_pk):
        try:
            stock_return_item = StockReturnItem.objects.get(id=item_pk, stock_return_id=pk)
            serializer = SerialNumberReturnSerializer(data=request.data, many=True, context={'stock_return_item': stock_return_item})
            if serializer.is_valid():
                for serial_data in serializer.validated_data:
                    if stock_return_item.qty_returned > stock_return_item.serial_numbers.count() and SerialNumber.objects.filter(
                        stock_receipt_item=stock_return_item.stock_receipt_item, serial_no=serial_data['serial_no']
                    ).exists():
                        SerialNumberReturn.objects.create(stock_return_item=stock_return_item, **serial_data)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Return Item not found'}, status=status.HTTP_404_NOT_FOUND)

class StockReturnPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            stock_return = StockReturn.objects.get(id=pk)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            header_data = [
                ['SRN ID', stock_return.SRN_ID],
                ['Return Date', stock_return.return_date],
                ['Supplier', stock_return.supplier.name if stock_return.supplier else 'N/A'],
                ['Total Items', len(stock_return.items.all())],
            ]
            header_table = Table(header_data)
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
            ]))
            elements.append(header_table)

            items_data = [['Product', 'UOM', 'Qty Ordered', 'Qty Rejected', 'Qty Returned', 'Unit Price', 'Tax (%)', 'Discount (%)', 'Total', 'Serials']]
            for item in stock_return.items.all():
                serials = ', '.join(sn.serial_no for sn in item.serial_numbers.all()) if item.serial_numbers.exists() else 'N/A'
                items_data.append([
                    item.product.name if item.product else 'N/A',
                    item.uom,
                    item.qty_ordered or 0,
                    item.qty_rejected or 0,
                    item.qty_returned,
                    f"{item.unit_price:.2f}",
                    f"{item.tax:.2f}",
                    f"{item.discount:.2f}",
                    f"{item.total:.2f}",
                    serials
                ])
            items_table = Table(items_data)
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(items_table)

            calc_data = [
                ['Original Purchased Total', f"₹{stock_return.original_purchased_total:.2f}"],
                ['Global Discount (%)', f"{stock_return.global_discount:.2f}%"],
                ['Return Subtotal', f"₹{stock_return.return_subtotal:.2f}"],
                ['Global Discount Amount', f"₹{stock_return.global_discount_amount:.2f}"],
                ['Rounding Adjustment', f"₹{stock_return.rounding_adjustment:.2f}"],
                ['Amount to Recover', f"₹{stock_return.amount_to_recover:.2f}"],
            ]
            calc_table = Table(calc_data)
            calc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            elements.append(calc_table)

            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="stock_return_{stock_return.SRN_ID}.pdf"'
            return response
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Return not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StockReturnEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            stock_return = StockReturn.objects.get(id=pk)
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

            subject = f'Stock Return {stock_return.SRN_ID}'
            html_message = render_to_string('stock_return_email_template.html', {'stock_return': stock_return})
            msg = EmailMessage(subject, html_message, to=[email])
            msg.content_subtype = 'html'
            msg.send()
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error': 'Stock Return not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)