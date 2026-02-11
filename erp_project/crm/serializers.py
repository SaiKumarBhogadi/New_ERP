from rest_framework import serializers
from django.db import transaction
from .models import Enquiry, EnquiryItem

from rest_framework import serializers
from django.db import transaction
from .models import Enquiry, EnquiryItem


class EnquiryItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = EnquiryItem
        fields = ['id', 'item_code', 'product_description', 'cost_price', 'selling_price', 'quantity', 'total_amount']
        read_only_fields = ['total_amount']

    def validate_item_code(self, value):
        if not value:
            return value

        enquiry = self.context.get('enquiry')
        if not enquiry:
            return value  # skip if no context

        if self.instance:
            if EnquiryItem.objects.filter(
                enquiry=enquiry,
                item_code=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Product item with this item code already exists in this enquiry."
                )
        else:
            if EnquiryItem.objects.filter(
                enquiry=enquiry,
                item_code=value
            ).exists():
                raise serializers.ValidationError(
                    "Product item with this item code already exists in this enquiry."
                )

        return value

    def validate(self, data):
        if data.get('selling_price', 0) <= 0:
            raise serializers.ValidationError({"selling_price": "Must be positive"})
        if data.get('quantity', 0) < 1:
            raise serializers.ValidationError({"quantity": "Must be at least 1"})
        return data


class EnquirySerializer(serializers.ModelSerializer):
    items = EnquiryItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField()
    user = serializers.StringRelatedField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Enquiry
        fields = '__all__'
        read_only_fields = ['created_by', 'updated_by']

    def get_grand_total(self, obj):
        return sum(item.total_amount for item in obj.items.all())
    
    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class EnquiryWriteSerializer(serializers.ModelSerializer):
    # Make items read-only here — we handle sync manually in update/create
    
    items = EnquiryItemSerializer(many=True, read_only=True)

    class Meta:
        model = Enquiry
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'street_address', 'apartment', 'city', 'state', 'postal', 'country',
            'enquiry_type', 'enquiry_description',
            'enquiry_channel', 'social_media_platform',
            'source', 'source_social_media',
            'how_heard', 'urgency_level', 'enquiry_status', 'priority',
            'items'  # still include in fields for response
        ]

    def validate(self, data):
        if self.instance is None:
            required = ['first_name', 'email', 'phone_number', 'enquiry_type', 'enquiry_status']
            for field in required:
                if not data.get(field):
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})

        channel = data.get('enquiry_channel')
        if channel == 'Social Media' and not data.get('social_media_platform'):
            raise serializers.ValidationError({
                'social_media_platform': 'Required when channel is Social Media'
            })

        source = data.get('source')
        if source == 'Social Media' and not data.get('source_social_media'):
            raise serializers.ValidationError({
                'source_social_media': 'Required when source is Social Media'
            })

        return data

    @transaction.atomic
    def create(self, validated_data):
        # Create main enquiry
        user = self.context['request'].user
        enquiry = Enquiry.objects.create(
            user=user,
            created_by=user,
            updated_by=user,
            **validated_data
        )

        # Items are read-only here — but frontend can send them
        # So manually create if sent
        items_data = self.initial_data.get('items', [])
        if items_data:
            item_serializer = EnquiryItemSerializer(data=items_data, many=True, context={'enquiry': enquiry})
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save(enquiry=enquiry)

        return enquiry

    @transaction.atomic
    def update(self, instance, validated_data):
        # Update main enquiry fields (items is read-only, so not in validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = self.context['request'].user
        instance.save()

        # Handle items sync only if 'items' key was sent in request
        if 'items' in self.initial_data:
            items_data = self.initial_data['items']
            sent_item_ids = []

            for item_data in items_data:
                item_id = item_data.get('id')
                item_data = {k: v for k, v in item_data.items() if k != 'id'}  # remove id

                if item_id:
                    try:
                        item = EnquiryItem.objects.get(id=item_id, enquiry=instance)
                        item_serializer = EnquiryItemSerializer(item, data=item_data, partial=True, context={'enquiry': instance})
                        item_serializer.is_valid(raise_exception=True)
                        item_serializer.save()
                        sent_item_ids.append(item_id)
                    except EnquiryItem.DoesNotExist:
                        pass
                else:
                    item_serializer = EnquiryItemSerializer(data=item_data, context={'enquiry': instance})
                    item_serializer.is_valid(raise_exception=True)
                    new_item = item_serializer.save(enquiry=instance)
                    sent_item_ids.append(new_item.id)

            # Delete items not in sent list
            EnquiryItem.objects.filter(enquiry=instance).exclude(id__in=sent_item_ids).delete()

        return instance



from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model

from masters.models import Product, UOM, TaxCode, Customer
from masters.serializers import ProductSerializer, UOMSerializer, TaxCodeSerializer, CustomerSerializer

from .models import (
    Quotation, QuotationItem, QuotationAttachment,
    QuotationComment, QuotationHistory, QuotationRevision
)

User = get_user_model()

from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model

from masters.models import Product, UOM, TaxCode, Customer
from masters.serializers import ProductSerializer, UOMSerializer, TaxCodeSerializer, CustomerSerializer

from .models import (
    Quotation, QuotationItem, QuotationAttachment,
    QuotationComment, QuotationHistory, QuotationRevision
)

User = get_user_model()


# Child Serializers
class QuotationItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_id_display = serializers.CharField(source='product.product_id', read_only=True)
    uom = serializers.PrimaryKeyRelatedField(queryset=UOM.objects.all())
    tax = serializers.PrimaryKeyRelatedField(queryset=TaxCode.objects.all(), allow_null=True, required=False)

    class Meta:
        model = QuotationItem
        fields = [
            'id', 'product', 'product_name', 'product_id_display', 'uom',
            'unit_price', 'discount', 'tax', 'tax_rate', 'quantity', 'total'
        ]
        read_only_fields = ['product_name', 'product_id_display', 'tax_rate', 'total']

    def validate_product(self, value):
        quotation = self.context.get('quotation')
        if not quotation:
            return value

        if self.instance:
            if QuotationItem.objects.filter(
                quotation=quotation,
                product=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "This product is already added in this quotation. You cannot add it again."
                )
        else:
            if QuotationItem.objects.filter(
                quotation=quotation,
                product=value
            ).exists():
                raise serializers.ValidationError(
                    "This product is already added in this quotation. You cannot add it again."
                )

        return value

    def validate(self, data):
        if 'unit_price' in data and data['unit_price'] <= 0:
            raise serializers.ValidationError({"unit_price": "Must be positive"})

        if 'quantity' in data and data['quantity'] < 1:
            raise serializers.ValidationError({"quantity": "Must be at least 1"})

        return data


class QuotationAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = QuotationAttachment
        fields = ['id', 'file', 'uploaded_by', 'timestamp']


class QuotationCommentSerializer(serializers.ModelSerializer):
    comment_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = QuotationComment
        fields = ['id', 'comment_by', 'comment', 'timestamp']


class QuotationHistorySerializer(serializers.ModelSerializer):
    action_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = QuotationHistory
        fields = ['id', 'event_type', 'status', 'extra_info', 'action_by', 'timestamp']


class QuotationRevisionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = QuotationRevision
        fields = ['id', 'revision_no', 'revision_date', 'created_by', 'comment', 'status']


# Main Serializers
class QuotationSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True, read_only=True)
    attachments = QuotationAttachmentSerializer(many=True, read_only=True)
    comments = QuotationCommentSerializer(many=True, read_only=True)
    history = QuotationHistorySerializer(many=True, read_only=True)
    revisions = QuotationRevisionSerializer(many=True, read_only=True)

    customer = CustomerSerializer(read_only=True)
    sales_rep = serializers.StringRelatedField(read_only=True)

    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    subtotal = serializers.ReadOnlyField()
    tax_summary = serializers.ReadOnlyField()
    grand_total = serializers.ReadOnlyField()

    class Meta:
        model = Quotation
        fields = '__all__'

    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


class QuotationWriteSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True, required=False, allow_empty=True)
    comments = QuotationCommentSerializer(many=True, required=False, allow_empty=True)

    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    sales_rep = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__role='Sales Representative'),
        allow_null=True
    )

    class Meta:
        model = Quotation
        fields = [
            'customer', 'customer_po_reference', 'sales_rep',
            'quotation_type', 'quotation_date', 'expiry_date',
            'currency', 'payment_terms', 'expected_delivery',
            'status', 'global_discount', 'shipping_charges',
            'items', 'comments'
        ]

    def validate(self, data):
        if self.instance is None:
            required = ['customer', 'quotation_type', 'quotation_date', 'status']
            for field in required:
                if not data.get(field):
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})

        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        comments_data = validated_data.pop('comments', [])

        quotation = Quotation.objects.create(
            created_by=self.context['request'].user,
            updated_by=self.context['request'].user,
            **validated_data
        )

        for item_data in items_data:
            serializer = QuotationItemSerializer(
                data=item_data,
                context={'quotation': quotation}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(quotation=quotation)


        for comment_data in comments_data:
            QuotationComment.objects.create(
                quotation=quotation,
                comment_by=self.context['request'].user,
                **comment_data
            )

        return quotation


    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        comments_data = validated_data.pop('comments', None)

        # update quotation fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.updated_by = self.context['request'].user
        instance.save()

        # items update
        if items_data is not None:
            sent_item_ids = []

            for item_data in items_data:
                item_id = item_data.pop('id', None)

                if item_id:
                    item = QuotationItem.objects.get(
                        id=item_id,
                        quotation=instance
                    )

                    for attr, value in item_data.items():
                        setattr(item, attr, value)

                    item.save()
                    sent_item_ids.append(item.id)

                else:
                    new_item = QuotationItem.objects.create(
                        quotation=instance,
                        **item_data
                    )
                    sent_item_ids.append(new_item.id)

            QuotationItem.objects.filter(
                quotation=instance
            ).exclude(id__in=sent_item_ids).delete()

        # comments
        if comments_data:
            for comment_data in comments_data:
                QuotationComment.objects.create(
                    quotation=instance,
                    comment_by=self.context['request'].user,
                    **comment_data
                )

        return instance




from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem, SalesOrderComment, SalesOrderHistory, DeliveryNote, DeliveryNoteItem, DeliveryNoteCustomerAcknowledgement, DeliveryNoteAttachment, DeliveryNoteRemark, Invoice, InvoiceItem, InvoiceAttachment, InvoiceRemark, OrderSummary
from masters.serializers import CustomerSerializer, ProductSerializer,TaxCodeSerializer
from masters.models import TaxCode
from purchase.serializers import SerialNumberSerializer
# serializers.py

from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model

from masters.models import Customer, Product, UOM, TaxCode
from masters.serializers import CustomerSerializer

from .models import SalesOrder, SalesOrderItem, SalesOrderComment, SalesOrderHistory

User = get_user_model()

class SalesOrderItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_id_display = serializers.CharField(source='product.product_id', read_only=True)
    in_stock = serializers.IntegerField(source='product.quantity_in_stock', read_only=True)  # Assuming Product has quantity_in_stock
    uom = serializers.PrimaryKeyRelatedField(queryset=UOM.objects.all())
    tax = serializers.PrimaryKeyRelatedField(queryset=TaxCode.objects.all(), allow_null=True, required=False)

    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'product', 'product_name', 'product_id_display', 'in_stock', 'uom',
            'unit_price', 'discount', 'tax', 'tax_rate', 'quantity', 'total'
        ]
        read_only_fields = ['product_name', 'product_id_display', 'in_stock', 'tax_rate', 'total']

    def validate_product(self, value):
        sales_order = self.context.get('sales_order')
        if not sales_order:
            return value

        if self.instance:
            if SalesOrderItem.objects.filter(
                sales_order=sales_order,
                product=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("This product is already added in this sales order.")
        else:
            if SalesOrderItem.objects.filter(
                sales_order=sales_order,
                product=value
            ).exists():
                raise serializers.ValidationError("This product is already added in this sales order.")

        return value

    def validate(self, data):
        if 'unit_price' in data and data['unit_price'] <= 0:
            raise serializers.ValidationError({"unit_price": "Must be positive"})

        if 'quantity' in data and data['quantity'] < 1:
            raise serializers.ValidationError({"quantity": "Must be at least 1"})

        return data


class SalesOrderCommentSerializer(serializers.ModelSerializer):
    comment_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SalesOrderComment
        fields = ['id', 'comment_by', 'comment', 'timestamp']


class SalesOrderHistorySerializer(serializers.ModelSerializer):
    action_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SalesOrderHistory
        fields = ['id', 'event_type', 'status', 'extra_info', 'action_by', 'timestamp']


class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True, read_only=True)
    comments = SalesOrderCommentSerializer(many=True, read_only=True)
    history = SalesOrderHistorySerializer(many=True, read_only=True)

    customer = CustomerSerializer(read_only=True)
    sales_rep = serializers.StringRelatedField(read_only=True)

    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    subtotal = serializers.ReadOnlyField()
    tax_summary = serializers.ReadOnlyField()
    grand_total = serializers.ReadOnlyField()

    class Meta:
        model = SalesOrder
        fields = '__all__'  
    
    def get_created_by(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None



class SalesOrderWriteSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True, required=False, allow_empty=True)
    comments = SalesOrderCommentSerializer(many=True, required=False, allow_empty=True)

    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    sales_rep = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__role='Sales Representative'),
        allow_null=True
    )

    class Meta:
        model = SalesOrder
        fields = [
            'order_date', 'sales_rep', 'order_type', 'customer',
            'payment_method', 'currency', 'due_date', 'terms_conditions',
            'shipping_method', 'expected_delivery', 'tracking_number',
            'internal_notes', 'customer_notes', 'global_discount',
            'shipping_charges', 'status', 'items', 'comments'
        ]
    


    def validate(self, data):
        if self.instance is None:
            required = ['order_date', 'order_type', 'customer', 'status']
            for field in required:
                if not data.get(field):
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})

        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        comments_data = validated_data.pop('comments', [])

        sales_order = SalesOrder.objects.create(
            created_by=self.context['request'].user,
            updated_by=self.context['request'].user,
            **validated_data
        )

        for item_data in items_data:
            serializer = SalesOrderItemSerializer(
                data=item_data,
                context={'sales_order': sales_order}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(sales_order=sales_order)


        for comment_data in comments_data:
            SalesOrderComment.objects.create(
                sales_order=sales_order,
                comment_by=self.context['request'].user,
                **comment_data
            )

        return sales_order

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        comments_data = validated_data.pop('comments', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.updated_by = self.context['request'].user
        instance.save()

        if items_data is not None:
            sent_item_ids = []

            for item_data in items_data:
                item_id = item_data.pop('id', None)

                if item_id:
                    item = SalesOrderItem.objects.get(
                        id=item_id,
                        sales_order=instance
                    )

                    serializer = SalesOrderItemSerializer(
                        item,
                        data=item_data,
                        partial=True,
                        context={'sales_order': instance}
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                    sent_item_ids.append(item.id)

                else:
                    serializer = SalesOrderItemSerializer(
                        data=item_data,
                        context={'sales_order': instance}
                    )
                    serializer.is_valid(raise_exception=True)
                    new_item = serializer.save(sales_order=instance)

                    sent_item_ids.append(new_item.id)

            SalesOrderItem.objects.filter(
                sales_order=instance
            ).exclude(id__in=sent_item_ids).delete()

        if comments_data:
            for comment_data in comments_data:
                SalesOrderComment.objects.create(
                    sales_order=instance,
                    comment_by=self.context['request'].user,
                    **comment_data
                )

        return instance


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