from rest_framework import serializers
from .models import PurchaseOrder, PurchaseOrderItem, PurchaseOrderHistory, PurchaseOrderComment 

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'product', 'qty_ordered', 'insufficient_stock', 'unit_price', 'tax', 'discount', 'total']
        read_only_fields = ['total', 'purchase_order']

class PurchaseOrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderHistory
        fields = ['id', 'action', 'performed_by', 'timestamp', 'details']
        read_only_fields = ['purchase_order']

class PurchaseOrderCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderComment
        fields = ['id', 'comment', 'created_by', 'timestamp']
        read_only_fields = ['purchase_order']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, required=False)
    history = PurchaseOrderHistorySerializer(many=True, required=False)
    comments = PurchaseOrderCommentSerializer(many=True, required=False)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'PO_ID', 'PO_date', 'delivery_date', 'status', 'sales_order_reference', 'supplier', 'supplier_name', 'payment_terms', 'inco_terms', 'currency', 'notes_comments', 'subtotal', 'global_discount', 'tax_summary', 'shipping_charges', 'rounding_adjustment', 'total_order_value', 'upload_file_path', 'items', 'history', 'comments']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        history_data = validated_data.pop('history', [])
        comments_data = validated_data.pop('comments', [])
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase_order=purchase_order, **item_data)
        for history_entry in history_data:
            PurchaseOrderHistory.objects.create(purchase_order=purchase_order, **history_entry)
        for comment_data in comments_data:
            PurchaseOrderComment.objects.create(purchase_order=purchase_order, **comment_data)
        return purchase_order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        history_data = validated_data.pop('history', [])
        comments_data = validated_data.pop('comments', [])
        instance = super().update(instance, validated_data)
        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                PurchaseOrderItem.objects.create(purchase_order=instance, **item_data)
        if history_data:
            instance.history.all().delete()
            for history_entry in history_data:
                PurchaseOrderHistory.objects.create(purchase_order=instance, **history_entry)
        if comments_data:
            instance.comments.all().delete()
            for comment_data in comments_data:
                PurchaseOrderComment.objects.create(purchase_order=instance, **comment_data)
        return instance
    

from rest_framework import serializers
from .models import StockReceipt, StockReceiptItem, SerialNumber, BatchNumber, BatchSerialNumber, StockReceiptRemark, StockReceiptAttachment

class StockReceiptAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReceiptAttachment
        fields = ['id', 'file']

class StockReceiptRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReceiptRemark
        fields = ['id', 'text', 'created_by', 'timestamp']

class SerialNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SerialNumber
        fields = ['id', 'serial_no']

    def create(self, validated_data):
        stock_receipt_item = self.context.get('stock_receipt_item')
        return SerialNumber.objects.create(stock_receipt_item=stock_receipt_item, **validated_data)

class BatchSerialNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchSerialNumber
        fields = ['id', 'serial_no']

class BatchNumberSerializer(serializers.ModelSerializer):
    serial_numbers = BatchSerialNumberSerializer(many=True, required=False)

    class Meta:
        model = BatchNumber
        fields = ['id', 'batch_no', 'batch_qty', 'mfg_date', 'expiry_date', 'serial_numbers']

    def create(self, validated_data):
        stock_receipt_item = self.context.get('stock_receipt_item')
        serial_numbers_data = validated_data.pop('serial_numbers', [])
        batch = BatchNumber.objects.create(stock_receipt_item=stock_receipt_item, **validated_data)
        for serial_data in serial_numbers_data:
            BatchSerialNumber.objects.create(batch_number=batch, **serial_data)
        return batch

class StockReceiptItemSerializer(serializers.ModelSerializer):
    serial_numbers = SerialNumberSerializer(many=True, required=False)
    batch_numbers = BatchNumberSerializer(many=True, required=False)

    class Meta:
        model = StockReceiptItem
        fields = ['id', 'product', 'uom', 'qty_ordered', 'qty_received', 'accepted_qty', 'rejected_qty', 'qty_returned', 'stock_dim', 'warehouse', 'unit_price', 'tax', 'discount', 'total', 'serial_numbers', 'batch_numbers']
        extra_kwargs = {
            'uom': {'required': False, 'allow_blank': True},
            'qty_ordered': {'required': False, 'allow_null': True},
            'unit_price': {'required': True},
            'tax': {'required': True},
            'discount': {'required': True},
            'total': {'read_only': True},
        }

    def create(self, validated_data):
        serial_numbers_data = validated_data.pop('serial_numbers', [])
        batch_numbers_data = validated_data.pop('batch_numbers', [])
        item = StockReceiptItem.objects.create(**validated_data)
        for serial_data in serial_numbers_data:
            SerialNumberSerializer(context={'stock_receipt_item': item}).create(serial_data)
        for batch_data in batch_numbers_data:
            BatchNumberSerializer(context={'stock_receipt_item': item}).create(batch_data)
        return item

    def update(self, instance, validated_data):
        serial_numbers_data = validated_data.pop('serial_numbers', [])
        batch_numbers_data = validated_data.pop('batch_numbers', [])
        instance = super().update(instance, validated_data)
        if serial_numbers_data:
            instance.serial_numbers.all().delete()
            for serial_data in serial_numbers_data:
                SerialNumberSerializer(context={'stock_receipt_item': instance}).create(serial_data)
        if batch_numbers_data:
            instance.batch_numbers.all().delete()
            for batch_data in batch_numbers_data:
                BatchNumberSerializer(context={'stock_receipt_item': instance}).create(batch_data)
        return instance

class StockReceiptSerializer(serializers.ModelSerializer):
    items = StockReceiptItemSerializer(many=True, required=False)
    attachments = StockReceiptAttachmentSerializer(many=True, required=False)
    remarks = StockReceiptRemarkSerializer(many=True, required=False)

    class Meta:
        model = StockReceipt
        fields = ['id', 'GRN_ID', 'PO_reference', 'received_date', 'supplier', 'supplier_dn_no', 'supplier_invoice_no', 'received_by', 'qc_done_by', 'status', 'remarks', 'attachments', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        stock_receipt = StockReceipt.objects.create(**validated_data)
        for item_data in items_data:
            StockReceiptItemSerializer().create(item_data)
        for attachment_data in attachments_data:
            StockReceiptAttachment.objects.create(stock_receipt=stock_receipt, **attachment_data)
        for remark_data in remarks_data:
            StockReceiptRemark.objects.create(stock_receipt=stock_receipt, **remark_data)
        return stock_receipt

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        instance = super().update(instance, validated_data)
        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                StockReceiptItemSerializer().create(item_data)
        if attachments_data:
            instance.attachments.all().delete()
            for attachment_data in attachments_data:
                StockReceiptAttachment.objects.create(stock_receipt=instance, **attachment_data)
        if remarks_data:
            instance.remarks.all().delete()
            for remark_data in remarks_data:
                StockReceiptRemark.objects.create(stock_receipt=instance, **remark_data)
        return instance
    
from rest_framework import serializers
from .models import StockReturn, StockReturnItem, SerialNumberReturn, StockReturnRemark, StockReturnAttachment
from .models import StockReceiptItem
from .serializers import SerialNumberSerializer

class StockReturnAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReturnAttachment
        fields = ['id', 'file']

class StockReturnRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReturnRemark
        fields = ['id', 'text', 'created_by', 'timestamp']

class SerialNumberReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = SerialNumberReturn
        fields = ['id', 'serial_no']

class StockReturnItemSerializer(serializers.ModelSerializer):
    serial_numbers = SerialNumberReturnSerializer(many=True, required=False)
    available_serials = serializers.SerializerMethodField()  # For popup data

    class Meta:
        model = StockReturnItem
        fields = ['id', 'stock_return', 'stock_receipt_item', 'product', 'uom', 'qty_ordered', 'qty_rejected', 'qty_returned', 'return_reason', 'unit_price', 'tax', 'discount', 'total', 'serial_numbers', 'available_serials']
        extra_kwargs = {
            'uom': {'required': False, 'allow_blank': True},
            'qty_ordered': {'required': False, 'allow_null': True},
            'qty_rejected': {'required': False, 'allow_null': True},
            'unit_price': {'required': False},
            'tax': {'required': False},
            'discount': {'required': False},
            'total': {'read_only': True},
            'stock_return': {'required': False},
        }

    def get_available_serials(self, obj):
        if obj.stock_receipt_item and obj.stock_receipt_item.stock_dim == 'Serial':
            return SerialNumberSerializer(obj.stock_receipt_item.serial_numbers.all(), many=True).data
        return []

    def create(self, validated_data):
        serial_numbers_data = validated_data.pop('serial_numbers', [])
        item = StockReturnItem.objects.create(**validated_data)
        for serial_data in serial_numbers_data:
            SerialNumberReturn.objects.create(stock_return_item=item, **serial_data)
        return item

    def update(self, instance, validated_data):
        serial_numbers_data = validated_data.pop('serial_numbers', [])
        instance = super().update(instance, validated_data)
        if serial_numbers_data:
            instance.serial_numbers.all().delete()
            for serial_data in serial_numbers_data:
                SerialNumberReturn.objects.create(stock_return_item=instance, **serial_data)
        return instance

class StockReturnSerializer(serializers.ModelSerializer):
    items = StockReturnItemSerializer(many=True, required=False)
    attachments = StockReturnAttachmentSerializer(many=True, required=False)
    remarks = StockReturnRemarkSerializer(many=True, required=False)

    class Meta:
        model = StockReturn
        fields = ['id', 'SRN_ID', 'PO_reference', 'GRN_reference', 'received_date', 'return_date', 'return_initiated_by', 'supplier', 'status', 'original_purchased_total', 'global_discount', 'return_subtotal', 'global_discount_amount', 'rounding_adjustment', 'amount_to_recover', 'remarks', 'attachments', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        stock_return = StockReturn.objects.create(**validated_data)
        for item_data in items_data:
            StockReturnItemSerializer().create(item_data)
        for attachment_data in attachments_data:
            StockReturnAttachment.objects.create(stock_return=stock_return, **attachment_data)
        for remark_data in remarks_data:
            StockReturnRemark.objects.create(stock_return=stock_return, **remark_data)
        return stock_return

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        instance = super().update(instance, validated_data)
        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                StockReturnItemSerializer().create(item_data)
        if attachments_data:
            instance.attachments.all().delete()
            for attachment_data in attachments_data:
                StockReturnAttachment.objects.create(stock_return=instance, **attachment_data)
        if remarks_data:
            instance.remarks.all().delete()
            for remark_data in remarks_data:
                StockReturnRemark.objects.create(stock_return=instance, **remark_data)
        return instance