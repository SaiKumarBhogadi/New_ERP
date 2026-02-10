from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class Enquiry(models.Model):
    enquiry_id = models.CharField(max_length=10, unique=True, editable=False)  # ENQ001
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enquiries')
    
    # Customer Info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    
    # Address
    street_address = models.CharField(max_length=200, blank=True)
    apartment = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default="India")
    
    # Enquiry Details
    enquiry_type = models.CharField(max_length=50, choices=[('Product', 'Product'), ('Service', 'Service'), ('Both', 'Both')])
    enquiry_description = models.TextField(blank=True)
    
    # Channel & Source (with sub-options)
    enquiry_channel = models.CharField(
        max_length=50,
        choices=[
            ('Phone', 'Phone'),
            ('Email', 'Email'),
            ('Web Form', 'Web Form'),
            ('Social Media', 'Social Media'),
            ('Other', 'Other')
        ],
        blank=True
    )
    social_media_platform = models.CharField(
        max_length=50,
        choices=[
            ('Facebook', 'Facebook'),
            ('Twitter', 'Twitter'),
            ('Instagram', 'Instagram'),
            ('LinkedIn', 'LinkedIn'),
            ('WhatsApp', 'WhatsApp')
        ],
        blank=True,
        null=True
    )
    
    source = models.CharField(
        max_length=50,
        choices=[
            ('Website', 'Website'),
            ('Referral', 'Referral'),
            ('Online Advertising', 'Online Advertising'),
            ('Offline Advertising', 'Offline Advertising'),
            ('Social Media', 'Social Media'),
            ('Event', 'Event'),
            ('Search Engine', 'Search Engine'),
            ('Other', 'Other')
        ],
        blank=True
    )
    source_social_media = models.CharField(
        max_length=50,
        choices=[
            ('Facebook', 'Facebook'),
            ('Twitter', 'Twitter'),
            ('Instagram', 'Instagram'),
            ('LinkedIn', 'LinkedIn'),
            ('WhatsApp', 'WhatsApp')
        ],
        blank=True,
        null=True
    )
    
    how_heard = models.CharField(
        max_length=50,
        choices=[
            ('Website', 'Website'),
            ('Referral', 'Referral'),
            ('Social Media', 'Social Media'),
            ('Event', 'Event'),
            ('Search Engine', 'Search Engine'),
            ('Other', 'Other')
        ],
        blank=True
    )
    
    urgency_level = models.CharField(
        max_length=50,
        choices=[
            ('Immediately', 'Immediately'),
            ('Within 1-3 Months', 'Within 1-3 Months'),
            ('Within 6 Months', 'Within 6 Months'),
            ('Just Researching', 'Just Researching')
        ],
        blank=True
    )
    
    enquiry_status = models.CharField(
        max_length=20,
        choices=[
            ('New', 'New'),
            ('In Process', 'In Process'),
            ('Converted', 'Converted'),
            ('Lost', 'Lost'),
            ('Closed', 'Closed')
        ],
        default='New'
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
        blank=True
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_enquiries')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_enquiries')

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Enquiries"

    def __str__(self):
        return f"{self.enquiry_id} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.enquiry_id:
            last = Enquiry.objects.order_by('-id').first()
            num = 1
            if last and last.enquiry_id:
                try:
                    num = int(last.enquiry_id.replace('ENQ', '')) + 1
                except:
                    pass
            self.enquiry_id = f"ENQ{num:04d}"
        super().save(*args, **kwargs)


class EnquiryItem(models.Model):
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='items')
    item_code = models.CharField(max_length=50, blank=True)
    product_description = models.CharField(max_length=500)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, editable=False)  # auto-calculated

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item_code or 'Item'} - {self.product_description[:50]}"

    def save(self, *args, **kwargs):
        self.total_amount = self.selling_price * self.quantity
        super().save(*args, **kwargs)



# crm/models.py

from django.db import models

from masters.models import Product, UOM, Customer, TaxCode
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models import Sum, F
from decimal import Decimal, ROUND_HALF_UP




class Quotation(models.Model):
    quotation_id = models.CharField(max_length=10, unique=True, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_quotations')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_quotations')

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    customer_po_reference = models.CharField(max_length=100, blank=True, null=True)

    sales_rep = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_rep_quotations',
        limit_choices_to={'role__role': 'Sales Representative'},
    )

    quotation_type = models.CharField(
        max_length=50,
        choices=[('Standard', 'Standard'), ('Blanket', 'Blanket'), ('Service', 'Service')],
        default='Standard',
    )

    quotation_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(blank=True, null=True)

    currency = models.CharField(
        max_length=3,
        choices=[('INR', 'INR'), ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('SGD', 'SGD')],
        default='INR',
    )

    payment_terms = models.CharField(max_length=50, blank=True)
    expected_delivery = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('Draft', 'Draft'),
            ('Submitted', 'Submitted'),
            ('Approved', 'Approved'),
            ('Rejected', 'Rejected'),
            ('Converted to SO', 'Converted to SO'),
            ('Expired', 'Expired')
        ],
        default='Draft',
    )

    revise_count = models.PositiveIntegerField(default=0)
    global_discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    rounding_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.quotation_id:
            last = Quotation.objects.order_by('-id').first()
            num = 1
            if last and last.quotation_id:
                try:
                    num = int(last.quotation_id.replace('QUO', '')) + 1
                except:
                    pass
            self.quotation_id = f"QUO{num:04d}"

        if self.expiry_date and self.expiry_date < timezone.now().date():
            if self.status not in ['Expired', 'Rejected', 'Converted to SO']:
                self.status = 'Expired'

        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.items.aggregate(subtotal=Sum('total'))['subtotal'] or Decimal("0.00")

    @property
    def tax_summary(self):
        return self.items.aggregate(
            tax=Sum(F('total') * F('tax_rate') / Decimal("100"))
        )['tax'] or Decimal("0.00")

    @property
    def grand_total(self):
        subtotal = self.subtotal
        discount_rate = self.global_discount or Decimal("0.00")
        shipping = self.shipping_charges or Decimal("0.00")
        tax = self.tax_summary

        discount = subtotal * (discount_rate / Decimal("100"))
        total = subtotal - discount + tax + shipping

        rounded_total = total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        self.rounding_adjustment = rounded_total - total

        return (total + self.rounding_adjustment).quantize(Decimal("0.01"))

    def __str__(self):
        return self.quotation_id


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    product_name = models.CharField(max_length=200, editable=False)
    product_id_display = models.CharField(max_length=20, editable=False)

    uom = models.ForeignKey(UOM, on_delete=models.SET_NULL, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax = models.ForeignKey(TaxCode, on_delete=models.SET_NULL, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), editable=False)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.product_name = self.product.name
        self.product_id_display = self.product.product_id
        self.tax_rate = self.tax.percentage if self.tax else Decimal("0.00")

        qty = Decimal(str(self.quantity))
        subtotal = qty * self.unit_price

        discount_amount = subtotal * (self.discount / Decimal("100"))
        after_discount = subtotal - discount_amount

        tax_amount = after_discount * (self.tax_rate / Decimal("100"))
        self.total = after_discount + tax_amount

        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name



class QuotationAttachment(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='quotations/attachments/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.quotation.quotation_id}"


class QuotationComment(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='comments')
    comment_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.comment_by} on {self.quotation.quotation_id}"


class QuotationHistory(models.Model):
    EVENT_TYPES = (
        ('status_change', 'Status Change'),
        ('pdf_generated', 'PDF Generated'),
        ('email_sent', 'Email Sent'),
    )

    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='history')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='status_change')
    status = models.CharField(max_length=20, blank=True, null=True)  # only for status_change
    extra_info = models.CharField(max_length=255, blank=True, null=True)  # e.g. "sent to customer@example.com"
    action_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} for {self.quotation.quotation_id}"


class QuotationRevision(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='revisions')
    revision_no = models.PositiveIntegerField()
    revision_date = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='Submitted')

    class Meta:
        ordering = ['-revision_no']

    def __str__(self):
        return f"Revision {self.revision_no} for {self.quotation.quotation_id}"




    

from django.db import models
from django.utils import timezone
from masters.models import Customer, Product, Branch
from purchase.models import SerialNumber



# models.py

from django.db import models
from django.utils import timezone

from django.db.models import Sum, F, DecimalField as DJDecimalField
from decimal import Decimal, ROUND_HALF_UP

from masters.models import Customer, Product, UOM, TaxCode



class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Ready to Submit', 'Ready to Submit'),
        ('Submitted', 'Submitted'),
        ('Submitted(PD)', 'Submitted(PD)'),
        ('Partially Delivered', 'Partially Delivered'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    ORDER_TYPE_CHOICES = [
        ('Standard', 'Standard'),
        ('Rush', 'Rush'),
        ('Backorder', 'Backorder'),
    ]

    sales_order_id = models.CharField(max_length=10, unique=True, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_sales_orders')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_sales_orders')

    order_date = models.DateField(default=timezone.now)
    sales_rep = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_rep_orders',
        limit_choices_to={'role__role': 'Sales Representative'},
    )
    order_type = models.CharField(max_length=50, choices=ORDER_TYPE_CHOICES, default='Standard')

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales_orders')

    payment_method = models.CharField(max_length=50, blank=True)
    currency = models.CharField(
        max_length=3,
        choices=[('INR', 'INR'), ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('SGD', 'SGD')],
        default='INR',
    )
    due_date = models.DateField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True)

    shipping_method = models.CharField(max_length=50, blank=True)
    expected_delivery = models.DateField(blank=True, null=True)
    tracking_number = models.CharField(max_length=50, blank=True)

    internal_notes = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)

    global_discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    rounding_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), editable=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.sales_order_id:
            last = SalesOrder.objects.order_by('-id').first()
            num = 1
            if last and last.sales_order_id:
                try:
                    num = int(last.sales_order_id.replace('SO-', '')) + 1
                except:
                    pass
            self.sales_order_id = f"SO-{num:04d}"

        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.items.aggregate(subtotal=Sum('total', output_field=DJDecimalField()))['subtotal'] or Decimal("0.00")

    @property
    def tax_summary(self):
        return self.items.aggregate(
            tax=Sum(F('total') * F('tax_rate') / Decimal("100"), output_field=DJDecimalField())
        )['tax'] or Decimal("0.00")

    @property
    def grand_total(self):
        subtotal = self.subtotal
        discount_rate = self.global_discount or Decimal("0.00")
        shipping = self.shipping_charges or Decimal("0.00")
        tax = self.tax_summary

        discount = subtotal * (discount_rate / Decimal("100"))
        total = subtotal - discount + tax + shipping

        rounded_total = total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        self.rounding_adjustment = rounded_total - total

        return (total + self.rounding_adjustment).quantize(Decimal("0.01"))

    def __str__(self):
        return self.sales_order_id


class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    product_name = models.CharField(max_length=200, editable=False)
    product_id_display = models.CharField(max_length=20, editable=False)

    uom = models.ForeignKey(UOM, on_delete=models.SET_NULL, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax = models.ForeignKey(TaxCode, on_delete=models.SET_NULL, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), editable=False)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.product_name = self.product.name
        self.product_id_display = self.product.product_id
        self.tax_rate = self.tax.percentage if self.tax else Decimal("0.00")

        qty = Decimal(str(self.quantity))
        subtotal = qty * self.unit_price

        discount_amount = subtotal * (self.discount / Decimal("100"))
        after_discount = subtotal - discount_amount

        tax_amount = after_discount * (self.tax_rate / Decimal("100"))
        self.total = after_discount + tax_amount

        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name


class SalesOrderComment(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='comments')
    comment_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.comment_by} on {self.sales_order.sales_order_id}"


class SalesOrderHistory(models.Model):
    EVENT_TYPES = (
        ('status_change', 'Status Change'),
        ('pdf_generated', 'PDF Generated'),
        ('email_sent', 'Email Sent'),
        ('po_generated', 'PO Generated'),
    )

    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='history')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='status_change')
    status = models.CharField(max_length=20, blank=True, null=True)  # only for status_change
    extra_info = models.CharField(max_length=255, blank=True, null=True)
    action_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} for {self.sales_order.sales_order_id}"

def generate_dn_id():
    last_dn = DeliveryNote.objects.order_by('-id').first()
    new_id = f'DN-{str(last_dn.id + 1).zfill(4) if last_dn else "0001"}' if last_dn else "DN-0001"
    return new_id

class DeliveryNoteAttachment(models.Model):
    delivery_note = models.ForeignKey('DeliveryNote', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='delivery_note_attachments/', blank=True, null=True)

class DeliveryNoteRemark(models.Model):
    delivery_note = models.ForeignKey('DeliveryNote', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

class DeliveryNote(models.Model):
    DN_ID = models.CharField(max_length=20, unique=True, editable=False, default=generate_dn_id)
    delivery_date = models.DateField(default=timezone.now)
    sales_order_reference = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=100, blank=True)
    delivery_type = models.CharField(max_length=20, choices=[('Regular', 'Regular'), ('Urgent', 'Urgent'), ('Return', 'Return')], default='Regular')
    destination_address = models.TextField(blank=True)
    delivery_status = models.CharField(max_length=20, choices=[('Draft', 'Draft'), ('Partially Delivered', 'Partially Delivered'), ('Delivered', 'Delivered'), ('Returned', 'Returned'), ('Cancelled', 'Cancelled')], default='Draft')
    partially_delivered = models.BooleanField(default=False)

class DeliveryNoteItem(models.Model):
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
   
    quantity = models.IntegerField(default=0)
    uom = models.CharField(max_length=50, blank=True)
    serial_numbers = models.ManyToManyField(SerialNumber, blank=True)

    def save(self, *args, **kwargs):
        if self.product:
            self.product_id = self.product.product_id
            self.uom = self.product.uom
        super().save(*args, **kwargs)

class DeliveryNoteCustomerAcknowledgement(models.Model):
    delivery_note = models.OneToOneField(DeliveryNote, on_delete=models.CASCADE, related_name='acknowledgement')
    received_by = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    proof_of_delivery = models.FileField(upload_to='delivery_proof/', blank=True, null=True)

# New Invoice models
def generate_invoice_id():
    last_invoice = Invoice.objects.order_by('-id').first()
    new_id = f'INV-{str(last_invoice.id + 1).zfill(4) if last_invoice else "0001"}' if last_invoice else "INV-0001"
    return new_id

class InvoiceAttachment(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='invoice_attachments/', blank=True, null=True)

class InvoiceRemark(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

class Invoice(models.Model):
    INVOICE_ID = models.CharField(max_length=20, unique=True, editable=False, default=generate_invoice_id)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True, null=True)
    sales_order_reference = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    customer_ref_no = models.CharField(max_length=50, blank=True)
    invoice_tags = models.CharField(max_length=100, blank=True)  # Store as comma-separated for multi-select
    terms_conditions = models.TextField(blank=True)
    invoice_status = models.CharField(max_length=20, choices=[('Draft', 'Draft'), ('Sent', 'Sent'), ('Paid', 'Paid'), ('Overdue', 'Overdue'), ('Cancelled', 'Cancelled')], default='Draft')
    payment_terms = models.CharField(max_length=20, choices=[('Net 15', 'Net 15'), ('Net 20', 'Net 20'), ('Net 45', 'Net 45'), ('Due on Receipt', 'Due on Receipt')], default='Net 30')
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    email_id = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=20, choices=[('Credit Card', 'Credit Card'), ('Bank Transfer', 'Bank Transfer'), ('COD', 'COD'), ('PayPal', 'PayPal')], blank=True)
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('EUR', 'EUR'), ('INR', 'INR'), ('GBP', 'GBP'), ('SGD', 'SGD')], default='INR')
    payment_ref_number = models.CharField(max_length=50, blank=True)
    transaction_date = models.DateField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=[('Paid', 'Paid'), ('Partial', 'Partial'), ('Unpaid', 'Unpaid')], default='Unpaid')
    invoice_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.invoice_total:
            self.invoice_total = sum(item.total for item in self.items.all()) or 0
        super().save(*args, **kwargs)

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    
    quantity = models.IntegerField(default=0)
    returned_qty = models.IntegerField(default=0)
    uom = models.CharField(max_length=50, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if self.product:
            self.product_id = self.product.product_id
            self.uom = self.product.uom
            self.unit_price = self.product.unit_price or 0.00
            self.tax = self.product.tax or 0.00
            self.discount = self.product.discount or 0.00
        self.total = self.quantity * self.unit_price * (1 - self.discount / 100) * (1 + self.tax / 100)
        super().save(*args, **kwargs)

class OrderSummary(models.Model):
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='summary')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    global_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_summary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rounding_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    credit_note_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        invoice = self.invoice
        self.subtotal = sum(item.total for item in invoice.items.all())
        self.tax_summary = sum(item.tax * item.total / 100 for item in invoice.items.all())
        self.grand_total = self.subtotal - (self.subtotal * self.global_discount / 100) + self.tax_summary + self.shipping_charges + self.rounding_adjustment - self.credit_note_applied
        self.balance_due = self.grand_total - self.amount_paid
        super().save(*args, **kwargs)



from django.db import models
from django.utils import timezone

from masters.models import Customer, Product, UOM
from purchase.models import SerialNumber
from .models import Invoice, SalesOrder


def generate_invoice_return_id():
    last_return = InvoiceReturn.objects.order_by('-id').first()
    return f'INVR-{str(last_return.id + 1).zfill(4) if last_return else "0001"}' if last_return else "INVR-0001"

class InvoiceReturnAttachment(models.Model):
    invoice_return = models.ForeignKey('InvoiceReturn', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='invoice_return_attachments/')

class InvoiceReturnRemark(models.Model):
    invoice_return = models.ForeignKey('InvoiceReturn', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

class InvoiceReturnItem(models.Model):
    invoice_return = models.ForeignKey('InvoiceReturn', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    uom = models.CharField(max_length=50, blank=True)
    invoiced_qty = models.IntegerField(default=0)
    returned_qty = models.IntegerField(default=0)
    serial_numbers = models.ManyToManyField(SerialNumber, blank=True)
    return_reason = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if self.product:
            self.uom = self.product.uom or ''
            self.unit_price = self.product.unit_price or 0.00
            self.tax = self.product.tax or 0.00
            self.discount = self.product.discount or 0.00
        self.total = self.returned_qty * self.unit_price * (1 - self.discount / 100) * (1 + self.tax / 100)
        super().save(*args, **kwargs)

class InvoiceReturnSummary(models.Model):
    invoice_return = models.OneToOneField('InvoiceReturn', on_delete=models.CASCADE, related_name='summary')
    original_grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    global_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    return_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    global_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    rounding_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_to_refund = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)

    def save(self, *args, **kwargs):
        invoice_return = self.invoice_return
        self.return_subtotal = sum(item.total for item in invoice_return.items.all())
        self.global_discount_amount = self.return_subtotal * (self.global_discount / 100)
        self.amount_to_refund = self.return_subtotal - self.global_discount_amount + self.rounding_adjustment
        super().save(*args, **kwargs)

class InvoiceReturnHistory(models.Model):
    invoice_return = models.ForeignKey('InvoiceReturn', on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)

class InvoiceReturnComment(models.Model):
    invoice_return = models.ForeignKey('InvoiceReturn', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

class InvoiceReturn(models.Model):
    INVOICE_RETURN_ID = models.CharField(max_length=20, unique=True, editable=False, default=generate_invoice_return_id)
    invoice_return_date = models.DateField(default=timezone.now)
    sales_order_reference = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True)
    customer_reference_no = models.CharField(max_length=50, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    email_id = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=[('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Cancelled', 'Cancelled')], default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



from django.db import models
from django.utils import timezone

from masters.models import Customer, Product, UOM
from purchase.models import SerialNumber
from .models import InvoiceReturn, SalesOrder



def generate_delivery_note_return_id():
    last_return = DeliveryNoteReturn.objects.order_by('-id').first()
    return f'DNR-{str(last_return.id + 1).zfill(4) if last_return else "0001"}' if last_return else "DNR-0001"

class DeliveryNoteReturnAttachment(models.Model):
    delivery_note_return = models.ForeignKey('DeliveryNoteReturn', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='delivery_note_return_attachments/')

class DeliveryNoteReturnRemark(models.Model):
    delivery_note_return = models.ForeignKey('DeliveryNoteReturn', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

class DeliveryNoteReturnItem(models.Model):
    delivery_note_return = models.ForeignKey('DeliveryNoteReturn', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    uom = models.CharField(max_length=50, blank=True)
    invoiced_qty = models.IntegerField(default=0)
    returned_qty = models.IntegerField(default=0)
    serial_numbers = models.ManyToManyField(SerialNumber, blank=True)
    return_reason = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.product:
            self.uom = self.product.uom or ''
        super().save(*args, **kwargs)

class DeliveryNoteReturnHistory(models.Model):
    delivery_note_return = models.ForeignKey('DeliveryNoteReturn', on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)

class DeliveryNoteReturnComment(models.Model):
    delivery_note_return = models.ForeignKey('DeliveryNoteReturn', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

class DeliveryNoteReturn(models.Model):
    DNR_ID = models.CharField(max_length=20, unique=True, editable=False, default=generate_delivery_note_return_id)
    dnr_date = models.DateField(default=timezone.now)
    invoice_return_reference = models.ForeignKey(InvoiceReturn, on_delete=models.SET_NULL, null=True, blank=True)
    customer_reference_no = models.CharField(max_length=50, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    email_id = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=[('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Cancelled', 'Cancelled')], default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)