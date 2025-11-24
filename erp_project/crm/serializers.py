from rest_framework import serializers
from .models import Enquiry, EnquiryItem
from core.models import Candidate

class EnquiryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnquiryItem
        fields = ['id', 'item_code', 'product_description', 'cost_price', 'selling_price', 'quantity', 'total_amount']

class EnquirySerializer(serializers.ModelSerializer):
    items = EnquiryItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = Enquiry
        fields = [
            'id', 'enquiry_id', 'first_name', 'last_name', 'email', 'phone_number',
            'street_address', 'apartment', 'city', 'state', 'postal', 'country',
            'enquiry_type', 'enquiry_description', 'enquiry_channels', 'source',
            'how_heard_this', 'urgency_level', 'enquiry_status', 'priority',
            'created_at', 'items', 'grand_total'
        ]

    def get_grand_total(self, obj):
        return sum(item.total_amount for item in obj.items.all()) if obj.items.exists() else 0
    
    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        if len(value) < 10 or len(value) > 15:
            raise serializers.ValidationError("Phone number must be between 10 and 15 digits.")
        return value


class EnquiryCreateSerializer(serializers.ModelSerializer):
    items = EnquiryItemSerializer(many=True, required=False)

    class Meta:
        model = Enquiry
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'street_address',
            'apartment', 'city', 'state', 'postal', 'country', 'enquiry_type',
            'enquiry_description', 'enquiry_channels', 'source', 'how_heard_this',
            'urgency_level', 'enquiry_status', 'priority', 'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        enquiry = Enquiry.objects.create(enquiry_id=self._generate_enquiry_id(), **validated_data)
        for item_data in items_data:
            EnquiryItem.objects.create(enquiry=enquiry, **item_data)
        return enquiry

    def _generate_enquiry_id(self):
        last_enquiry = Enquiry.objects.order_by('-id').first()
        if last_enquiry:
            last_id = int(last_enquiry.enquiry_id.replace('ENQ', '')) + 1
        else:
            last_id = 1
        return f'ENQ{last_id:03d}'  # e.g., ENQ001, ENQ002
    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        if len(value) < 10 or len(value) > 15:
            raise serializers.ValidationError("Phone number must be between 10 and 15 digits.")
        return value

    

from rest_framework import serializers
from .models import Quotation, QuotationItem, QuotationAttachment, QuotationComment, QuotationHistory, QuotationRevision
from masters.models import Customer, Role
from masters.models import Product, UOM
from django.contrib.auth import get_user_model

User = get_user_model()

class QuotationItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    uom = serializers.PrimaryKeyRelatedField(queryset=UOM.objects.all())
    product_name = serializers.CharField(source='product_id.name', read_only=True)

    class Meta:
        model = QuotationItem
        fields = ['id', 'product_id', 'product_name', 'uom', 'unit_price', 'discount', 'tax', 'quantity', 'total']

class QuotationAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())
    file = serializers.FileField(required = False,allow_null=True)

    class Meta:
        model = QuotationAttachment
        fields = ['id', 'file', 'uploaded_by', 'timestamp']

class QuotationCommentSerializer(serializers.ModelSerializer):
    person_name = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())

    class Meta:
        model = QuotationComment
        fields = ['id', 'person_name', 'comment', 'timestamp']

class QuotationHistorySerializer(serializers.ModelSerializer):
    action_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())

    class Meta:
        model = QuotationHistory
        fields = ['id', 'status', 'timestamp', 'action_by']

class QuotationRevisionSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=serializers.CurrentUserDefault())

    class Meta:
        model = QuotationRevision
        fields = ['id', 'revision_number', 'date', 'created_by', 'status', 'comment', 'revise_history']

class QuotationSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True, read_only=True)
    attachments = QuotationAttachmentSerializer(many=True, read_only=True)
    comments = QuotationCommentSerializer(many=True, read_only=True)
    history = QuotationHistorySerializer(many=True, read_only=True)
    revisions = QuotationRevisionSerializer(many=True, read_only=True)
    customer_name = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    sales_rep = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role__role='Sales Representative'),allow_null=True)
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = Quotation
        fields = [
            'id', 'quotation_id', 'quotation_type', 'quotation_date', 'expiry_date', 'customer_name',
            'customer_po_referance', 'sales_rep', 'currency', 'payment_terms', 'expected_delivery',
            'status', 'revise_count', 'globalDiscount', 'shippingCharges', 'created_at', 'items',
            'attachments', 'comments', 'history', 'revisions', 'grand_total'
        ]

    def get_grand_total(self, obj):
        subtotal = sum(item.total for item in obj.items.all())
        discount_amount = subtotal * (obj.globalDiscount / 100)
        return round(subtotal - discount_amount + obj.shippingCharges, 2)

class QuotationCreateSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True, required=False)
    attachments = QuotationAttachmentSerializer(many=True, required=False)
    comments = QuotationCommentSerializer(many=True, required=False)
    history = QuotationHistorySerializer(many=True, required=False)
    revisions = QuotationRevisionSerializer(many=True, required=False)
    customer_name = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    sales_rep = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role__role='Sales Representative'),allow_null=True)
    class Meta:
        model = Quotation
        fields = [
            'quotation_type', 'quotation_date', 'expiry_date', 'customer_name', 'customer_po_referance',
            'sales_rep', 'currency', 'payment_terms', 'expected_delivery', 'status', 'revise_count',
            'globalDiscount', 'shippingCharges', 'items', 'attachments', 'comments', 'history', 'revisions'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        comments_data = validated_data.pop('comments', [])
        history_data = validated_data.pop('history', [])
        revisions_data = validated_data.pop('revisions', [])
        quotation = Quotation.objects.create(quotation_id=self._generate_quotation_id(), user=self.context['request'].user, **validated_data)
        for item_data in items_data:
            QuotationItem.objects.create(quotation=quotation, **item_data)
        for attachment_data in attachments_data:
            QuotationAttachment.objects.create(quotation=quotation, **attachment_data)
        for comment_data in comments_data:
            QuotationComment.objects.create(quotation=quotation, **comment_data)
        for history_data in history_data:
            QuotationHistory.objects.create(quotation=quotation, **history_data)
        for revision_data in revisions_data:
            QuotationRevision.objects.create(quotation=quotation, **revision_data)
        return quotation

    def _generate_quotation_id(self):
        last_quotation = Quotation.objects.order_by('-id').first()
        if last_quotation:
            last_id = int(last_quotation.quotation_id.replace('QUO', '')) + 1
        else:
            last_id = 1
        return f'QUO{last_id:03d}'
    

from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem, SalesOrderComment, SalesOrderHistory, DeliveryNote, DeliveryNoteItem, DeliveryNoteCustomerAcknowledgement, DeliveryNoteAttachment, DeliveryNoteRemark, Invoice, InvoiceItem, InvoiceAttachment, InvoiceRemark, OrderSummary
from masters.serializers import CustomerSerializer, ProductSerializer
from purchase.serializers import SerialNumberSerializer

# Existing SalesOrder serializers
class SalesOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = SalesOrderItem
        fields = ['id', 'product', 'quantity', 'uom', 'unit_price', 'discount', 'total']

class SalesOrderCreateSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    sales_rep = serializers.PrimaryKeyRelatedField(queryset=Candidate.objects.filter(designation__role="Sales Representative"),
        allow_null=True)

    class Meta:
        model = SalesOrder
        fields = ['id', 'order_date', 'sales_rep', 'order_type', 'customer', 'payment_method', 'currency', 'due_date', 'terms_conditions', 'shipping_method', 'expected_delivery', 'tracking_number', 'internal_notes', 'customer_notes', 'global_discount', 'shipping_charges', 'status']

class SalesOrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    sales_rep = serializers.CharField(source='sales_rep.username')
    items = SalesOrderItemSerializer(many=True, required=False)
    comments = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()

    class Meta:
        model = SalesOrder
        fields = ['id', 'sales_order_id', 'order_date', 'sales_rep', 'order_type', 'customer', 'payment_method', 'currency', 'due_date', 'terms_conditions', 'shipping_method', 'expected_delivery', 'tracking_number', 'internal_notes', 'customer_notes', 'global_discount', 'shipping_charges', 'status', 'items', 'comments', 'history']

    def get_comments(self, obj):
        return [{'id': c.id, 'user': c.user.username, 'comment': c.comment, 'timestamp': c.timestamp} for c in obj.comments.all()]

    def get_history(self, obj):
        return [{'id': h.id, 'user': h.user.username, 'action': h.action, 'timestamp': h.timestamp} for h in obj.history.all()]

class SalesOrderCommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')

    class Meta:
        model = SalesOrderComment
        fields = ['id', 'user', 'comment', 'timestamp']

class SalesOrderHistorySerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')

    class Meta:
        model = SalesOrderHistory
        fields = ['id', 'user', 'action', 'timestamp']

# Existing DeliveryNote serializers
class DeliveryNoteAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryNoteAttachment
        fields = ['id', 'file']

class DeliveryNoteRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryNoteRemark
        fields = ['id', 'text', 'created_by', 'timestamp']

class DeliveryNoteItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    serial_numbers = SerialNumberSerializer(many=True, required=False)

    class Meta:
        model = DeliveryNoteItem
        fields = ['id', 'product', 'quantity', 'uom', 'serial_numbers']

    def validate(self, data):
        if data.get('product'):
            data['product_id'] = data['product'].product_id
            data['uom'] = data['product'].uom
        return data

class DeliveryNoteCustomerAcknowledgementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryNoteCustomerAcknowledgement
        fields = ['id', 'received_by', 'contact_number', 'proof_of_delivery']

class DeliveryNoteSerializer(serializers.ModelSerializer):
    items = DeliveryNoteItemSerializer(many=True, required=False)
    attachments = DeliveryNoteAttachmentSerializer(many=True, required=False)
    remarks = DeliveryNoteRemarkSerializer(many=True, required=False)
    acknowledgement = DeliveryNoteCustomerAcknowledgementSerializer(required=False)

    class Meta:
        model = DeliveryNote
        fields = ['id', 'DN_ID', 'delivery_date', 'sales_order_reference', 'customer_name', 'delivery_type', 'destination_address', 'delivery_status', 'partially_delivered', 'items', 'attachments', 'remarks', 'acknowledgement']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        acknowledgement_data = validated_data.pop('acknowledgement', None)
        delivery_note = DeliveryNote.objects.create(**validated_data)
        for item_data in items_data:
            item = DeliveryNoteItemSerializer().create(item_data)
            delivery_note.items.add(item)
        for attachment_data in attachments_data:
            DeliveryNoteAttachment.objects.create(delivery_note=delivery_note, **attachment_data)
        for remark_data in remarks_data:
            DeliveryNoteRemark.objects.create(delivery_note=delivery_note, **remark_data)
        if acknowledgement_data:
            DeliveryNoteCustomerAcknowledgement.objects.create(delivery_note=delivery_note, **acknowledgement_data)
        return delivery_note

# New Invoice serializers
class InvoiceAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceAttachment
        fields = ['id', 'file']

class InvoiceRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceRemark
        fields = ['id', 'text', 'created_by', 'timestamp']

class InvoiceItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = InvoiceItem
        fields = ['id', 'product',  'quantity', 'returned_qty', 'uom', 'unit_price', 'tax', 'discount', 'total']

    def validate(self, data):
        if data.get('product'):
            data['product_id'] = data['product'].product_id
            data['uom'] = data['product'].uom
            data['unit_price'] = data['product'].unit_price or 0.00
            data['tax'] = data['product'].tax or 0.00
            data['discount'] = data['product'].discount or 0.00
        return data

class OrderSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderSummary
        fields = ['id', 'subtotal', 'global_discount', 'tax_summary', 'shipping_charges', 'rounding_adjustment', 'credit_note_applied', 'amount_paid', 'grand_total', 'balance_due']

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, required=False)
    attachments = InvoiceAttachmentSerializer(many=True, required=False)
    remarks = InvoiceRemarkSerializer(many=True, required=False)
    summary = OrderSummarySerializer(required=False)

    class Meta:
        model = Invoice
        fields = ['id', 'INVOICE_ID', 'invoice_date', 'due_date', 'sales_order_reference', 'customer', 'customer_ref_no', 'invoice_tags', 'terms_conditions', 'invoice_status', 'payment_terms', 'billing_address', 'shipping_address', 'email_id', 'phone_number', 'contact_person', 'payment_method', 'currency', 'payment_ref_number', 'transaction_date', 'payment_status', 'invoice_total', 'items', 'attachments', 'remarks', 'summary']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        summary_data = validated_data.pop('summary', None)
        invoice = Invoice.objects.create(**validated_data)
        for item_data in items_data:
            item = InvoiceItemSerializer().create(item_data)
            invoice.items.add(item)
        for attachment_data in attachments_data:
            InvoiceAttachment.objects.create(invoice=invoice, **attachment_data)
        for remark_data in remarks_data:
            InvoiceRemark.objects.create(invoice=invoice, **remark_data)
        if summary_data:
            OrderSummary.objects.create(invoice=invoice, **summary_data)
        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        attachments_data = validated_data.pop('attachments', None)
        remarks_data = validated_data.pop('remarks', None)
        summary_data = validated_data.pop('summary', None)
        instance = super().update(instance, validated_data)
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                item = InvoiceItemSerializer().create(item_data)
                instance.items.add(item)
        if attachments_data is not None:
            instance.attachments.all().delete()
            for attachment_data in attachments_data:
                InvoiceAttachment.objects.create(invoice=instance, **attachment_data)
        if remarks_data is not None:
            instance.remarks.all().delete()
            for remark_data in remarks_data:
                InvoiceRemark.objects.create(invoice=instance, **remark_data)
        if summary_data is not None:
            instance.summary.delete()
            OrderSummary.objects.create(invoice=instance, **summary_data)
        return instance
    


from rest_framework import serializers
from .models import InvoiceReturn, InvoiceReturnItem, InvoiceReturnAttachment, InvoiceReturnRemark, InvoiceReturnSummary, InvoiceReturnHistory, InvoiceReturnComment
from masters.serializers import CustomerSerializer, ProductSerializer
from crm.serializers import  SalesOrderSerializer
from purchase.serializers import SerialNumberSerializer  # Assumed

class InvoiceReturnAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceReturnAttachment
        fields = ['id', 'file']

class InvoiceReturnRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceReturnRemark
        fields = ['id', 'text', 'created_by', 'timestamp']

class InvoiceReturnItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    serial_numbers = SerialNumberSerializer(many=True, read_only=True)

    class Meta:
        model = InvoiceReturnItem
        fields = ['id', 'product', 'uom', 'invoiced_qty', 'returned_qty', 'serial_numbers', 'return_reason', 'unit_price', 'tax', 'discount', 'total']

    def create(self, validated_data):
        serial_numbers_data = validated_data.pop('serial_numbers', [])
        item = InvoiceReturnItem.objects.create(**validated_data)
        if serial_numbers_data:
            item.serial_numbers.set(serial_numbers_data)
        return item

class InvoiceReturnSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceReturnSummary
        fields = ['id', 'original_grand_total', 'global_discount', 'return_subtotal', 'global_discount_amount', 'rounding_adjustment', 'amount_to_refund']

class InvoiceReturnHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceReturnHistory
        fields = ['id', 'user', 'action', 'timestamp']

class InvoiceReturnCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceReturnComment
        fields = ['id', 'user', 'comment', 'timestamp']

class InvoiceReturnSerializer(serializers.ModelSerializer):
    items = InvoiceReturnItemSerializer(many=True, required=False)
    attachments = InvoiceReturnAttachmentSerializer(many=True, required=False)
    remarks = InvoiceReturnRemarkSerializer(many=True, required=False)
    summary = InvoiceReturnSummarySerializer(required=False)
    sales_order_reference = SalesOrderSerializer()
    customer = CustomerSerializer()

    class Meta:
        model = InvoiceReturn
        fields = ['id', 'INVOICE_RETURN_ID', 'invoice_return_date', 'sales_order_reference', 'customer_reference_no', 'customer', 'email_id', 'phone_number', 'contact_person', 'status', 'items', 'attachments', 'remarks', 'summary', 'history', 'comments']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        summary_data = validated_data.pop('summary', None)
        invoice_return = InvoiceReturn.objects.create(**validated_data)
        for item_data in items_data:
            item_serializer = InvoiceReturnItemSerializer(data=item_data)
            if item_serializer.is_valid():
                item = item_serializer.save(invoice_return=invoice_return)
        for attachment_data in attachments_data:
            InvoiceReturnAttachment.objects.create(invoice_return=invoice_return, **attachment_data)
        for remark_data in remarks_data:
            InvoiceReturnRemark.objects.create(invoice_return=invoice_return, **remark_data)
        if summary_data:
            InvoiceReturnSummary.objects.create(invoice_return=invoice_return, **summary_data)
        return invoice_return
    

from rest_framework import serializers
from .models import DeliveryNoteReturn, DeliveryNoteReturnItem, DeliveryNoteReturnAttachment, DeliveryNoteReturnRemark, DeliveryNoteReturnHistory, DeliveryNoteReturnComment
from masters.serializers import CustomerSerializer, ProductSerializer
from purchase.serializers import SerialNumberSerializer  
from .serializers import InvoiceReturnSerializer  

class DeliveryNoteReturnAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryNoteReturnAttachment
        fields = ['id', 'file']

class DeliveryNoteReturnRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryNoteReturnRemark
        fields = ['id', 'text', 'created_by', 'timestamp']

class DeliveryNoteReturnItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    serial_numbers = SerialNumberSerializer(many=True, read_only=True)

    class Meta:
        model = DeliveryNoteReturnItem
        fields = ['id', 'product', 'uom', 'invoiced_qty', 'returned_qty', 'serial_numbers', 'return_reason']

    def create(self, validated_data):
        serial_numbers_data = validated_data.pop('serial_numbers', [])
        item = DeliveryNoteReturnItem.objects.create(**validated_data)
        if serial_numbers_data:
            item.serial_numbers.set(serial_numbers_data)
        return item

class DeliveryNoteReturnHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryNoteReturnHistory
        fields = ['id', 'user', 'action', 'timestamp']

class DeliveryNoteReturnCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryNoteReturnComment
        fields = ['id', 'user', 'comment', 'timestamp']

class DeliveryNoteReturnSerializer(serializers.ModelSerializer):
    items = DeliveryNoteReturnItemSerializer(many=True, required=False)
    attachments = DeliveryNoteReturnAttachmentSerializer(many=True, required=False)
    remarks = DeliveryNoteReturnRemarkSerializer(many=True, required=False)
    invoice_return_reference = InvoiceReturnSerializer()

    class Meta:
        model = DeliveryNoteReturn
        fields = ['id', 'DNR_ID', 'dnr_date', 'invoice_return_reference', 'customer_reference_no', 'customer', 'email_id', 'phone_number', 'contact_person', 'status', 'items', 'attachments', 'remarks', 'history', 'comments']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        delivery_note_return = DeliveryNoteReturn.objects.create(**validated_data)
        for item_data in items_data:
            item_serializer = DeliveryNoteReturnItemSerializer(data=item_data)
            if item_serializer.is_valid():
                item = item_serializer.save(delivery_note_return=delivery_note_return)
        for attachment_data in attachments_data:
            DeliveryNoteReturnAttachment.objects.create(delivery_note_return=delivery_note_return, **attachment_data)
        for remark_data in remarks_data:
            DeliveryNoteReturnRemark.objects.create(delivery_note_return=delivery_note_return, **remark_data)
        return delivery_note_return