from rest_framework import serializers
from .models import CreditNote, CreditNoteItem, CreditNoteAttachment, CreditNoteRemark, CreditNotePaymentRefund, DebitNote, DebitNoteItem, DebitNoteAttachment, DebitNoteRemark, DebitNotePaymentRecover
from core.serializers import BranchSerializer, CandidateSerializer  , SupplierSerializer
from crm.serializers import CustomerSerializer, ProductSerializer, InvoiceSerializer
from purchase.serializers import PurchaseOrderSerializer

class CreditNoteAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNoteAttachment
        fields = ['id', 'file']

class CreditNoteRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNoteRemark
        fields = ['id', 'text', 'created_by', 'timestamp']

class CreditNoteItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CreditNoteItem
        fields = ['id', 'product', 'product_id', 'returned_qty', 'uom', 'return_reason', 'unit_price', 'tax', 'discount', 'total']

    def validate(self, data):
        if data.get('product'):
            data['product_id'] = data['product'].product_id
            data['uom'] = data['product'].uom
            data['unit_price'] = data['product'].unit_price or 0.00
            data['tax'] = data['product'].tax or 0.00
            data['discount'] = data['product'].discount or 0.00
        return data

class CreditNotePaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNotePaymentRefund
        fields = ['id', 'amount_paid_by_customer', 'balance_due_by_customer', 'invoice_return_amount', 'balance_to_refund', 'refund_mode', 'refund_paid', 'refund_date', 'adjusted_invoice_reference']

class CreditNoteSerializer(serializers.ModelSerializer):
    items = CreditNoteItemSerializer(many=True, required=False)
    attachments = CreditNoteAttachmentSerializer(many=True, required=False)
    remarks = CreditNoteRemarkSerializer(many=True, required=False)
    payment_refund = CreditNotePaymentRefundSerializer(required=False)
    invoice_reference = InvoiceSerializer()
    customer = CustomerSerializer()
    created_by = CandidateSerializer()
    branch = BranchSerializer()

    class Meta:
        model = CreditNote
        fields = ['id', 'CREDIT_NOTE_ID', 'credit_note_date', 'invoice_reference', 'created_by', 'branch', 'currency', 'customer', 'customer_id', 'billing_address', 'phone_number', 'invoice_date', 'due_date', 'payment_terms', 'invoice_status', 'payment_status', 'invoice_total', 'items', 'attachments', 'remarks', 'payment_refund']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        payment_refund_data = validated_data.pop('payment_refund', None)
        credit_note = CreditNote.objects.create(**validated_data)
        for item_data in items_data:
            item = CreditNoteItemSerializer().create(item_data)
            credit_note.items.add(item)
        for attachment_data in attachments_data:
            CreditNoteAttachment.objects.create(credit_note=credit_note, **attachment_data)
        for remark_data in remarks_data:
            CreditNoteRemark.objects.create(credit_note=credit_note, **remark_data)
        if payment_refund_data:
            CreditNotePaymentRefund.objects.create(credit_note=credit_note, **payment_refund_data)
        return credit_note

class DebitNoteAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebitNoteAttachment
        fields = ['id', 'file']

class DebitNoteRemarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebitNoteRemark
        fields = ['id', 'text', 'created_by', 'timestamp']

class DebitNoteItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = DebitNoteItem
        fields = ['id', 'product', 'product_id', 'returned_qty', 'uom', 'return_reason', 'unit_price', 'tax', 'discount', 'total']

    def validate(self, data):
        if data.get('product'):
            data['product_id'] = data['product'].product_id
            data['uom'] = data['product'].uom
            data['unit_price'] = data['product'].unit_price or 0.00
            data['tax'] = data['product'].tax or 0.00
            data['discount'] = data['product'].discount or 0.00
        return data

class DebitNotePaymentRecoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebitNotePaymentRecover
        fields = ['id', 'amount_paid_to_vendor', 'balance_due_to_vendor', 'purchase_return_amount', 'balance_to_recover', 'refund_mode', 'refund_received', 'refund_date', 'adjusted_invoice_reference']

class DebitNoteSerializer(serializers.ModelSerializer):
    items = DebitNoteItemSerializer(many=True, required=False)
    attachments = DebitNoteAttachmentSerializer(many=True, required=False)
    remarks = DebitNoteRemarkSerializer(many=True, required=False)
    payment_recover = DebitNotePaymentRecoverSerializer(required=False)
    po_reference = PurchaseOrderSerializer()
    supplier = SupplierSerializer()
    created_by = CandidateSerializer()
    branch = BranchSerializer()

    class Meta:
        model = DebitNote
        fields = ['id', 'DEBIT_NOTE_ID', 'debit_note_date', 'po_reference', 'created_by', 'branch', 'currency', 'supplier', 'supplier_id', 'po_date', 'due_date', 'payment_terms', 'inco_terms', 'payment_status', 'credit_limit', 'purchase_total', 'items', 'attachments', 'remarks', 'payment_recover']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        attachments_data = validated_data.pop('attachments', [])
        remarks_data = validated_data.pop('remarks', [])
        payment_recover_data = validated_data.pop('payment_recover', None)
        debit_note = DebitNote.objects.create(**validated_data)
        for item_data in items_data:
            item = DebitNoteItemSerializer().create(item_data)
            debit_note.items.add(item)
        for attachment_data in attachments_data:
            DebitNoteAttachment.objects.create(debit_note=debit_note, **attachment_data)
        for remark_data in remarks_data:
            DebitNoteRemark.objects.create(debit_note=debit_note, **remark_data)
        if payment_recover_data:
            DebitNotePaymentRecover.objects.create(debit_note=debit_note, **payment_recover_data)
        return debit_note