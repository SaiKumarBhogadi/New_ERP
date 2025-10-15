from django.db import models
from django.conf import settings

class Enquiry(models.Model):
    enquiry_id = models.CharField(max_length=10, unique=True)  # e.g., ENQ001
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone_number = models.IntegerField()
    street_address = models.CharField(max_length=200, blank=True)
    apartment = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    enquiry_type = models.CharField(max_length=50, choices=[('Product', 'Product'), ('Service', 'Service')])
    enquiry_description = models.TextField(blank=True)
    enquiry_channels = models.CharField(max_length=50, blank=True, choices=[
        ('Phone', 'Phone'), ('Email', 'Email'), ('Web Form', 'Web Form'),
        ('Facebook', 'Facebook'), ('Twitter', 'Twitter'), ('Instagram', 'Instagram'), ('LinkedIn', 'LinkedIn')
    ])
    source = models.CharField(max_length=50, choices=[
        ('WebSite', 'WebSite'), ('Referral', 'Referral'), ('Online Advertising', 'Online Advertising'),
        ('Offline Advertising', 'Offline Advertising'), ('Facebook', 'Facebook'), ('Twitter', 'Twitter'),
        ('Instagram', 'Instagram'), ('LinkedIn', 'LinkedIn')
    ])
    how_heard_this = models.CharField(max_length=50, blank=True, choices=[
        ('WebSite', 'WebSite'), ('Referral', 'Referral'), ('Social Media', 'Social Media'),
        ('Event', 'Event'), ('Search Engine', 'Search Engine'), ('Other', 'Other')
    ])
    urgency_level = models.CharField(max_length=50, blank=True, choices=[
        ('Immediately', 'Immediately'), ('Within 1-3 Months', 'Within 1-3 Months'),
        ('Within 6 Months', 'Within 6 Months'), ('Just Researching', 'Just Researching')
    ])
    enquiry_status = models.CharField(max_length=20, choices=[
        ('New', 'New'), ('In Process', 'In Process'), ('Closed', 'Closed')
    ])
    priority = models.CharField(max_length=20, blank=True, choices=[
        ('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.enquiry_id} - {self.first_name} {self.last_name}"

class EnquiryItem(models.Model):
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='items')
    item_code = models.CharField(max_length=10)
    product_description = models.CharField(max_length=200)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.item_code} - {self.product_description}"
    

from django.db import models
from django.contrib.auth import get_user_model
from masters.models import Branch, Department, Role
from masters.models import Product, UOM,Customer


User = get_user_model()

class Quotation(models.Model):
    quotation_id = models.CharField(max_length=10, unique=True)  # e.g., QUO001
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_name = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    customer_po_referance = models.CharField(max_length=100, blank=True, null=True)
    sales_rep = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'Sales Representative'}, related_name='quotations')
    quotation_type = models.CharField(max_length=50, choices=[('Standard', 'Standard'), ('Blanket', 'Blanket'), ('Service', 'Service')])
    quotation_date = models.DateField()
    expiry_date = models.DateField()
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('INR', 'INR'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('SGD', 'SGD')])
    payment_terms = models.CharField(max_length=50, blank=True, choices=[('Net 15', 'Net 15'), ('Net 30', 'Net 30'), ('Net 45', 'Net 45'), ('Net 60', 'Net 60'), ('Advance', 'Advance'), ('COD', 'COD')])
    expected_delivery = models.DateField()
    status = models.CharField(max_length=20, choices=[('Draft', 'Draft'), ('Send', 'Send'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Converted (SO)', 'Converted (SO)'), ('Expired', 'Expired')])
    revise_count = models.PositiveIntegerField(default=1)
    globalDiscount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    shippingCharges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quotation_id} - {self.customer_name}"

class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quotation_items')
    product_name = models.CharField(max_length=200, editable=False)  # Populated from Product.name
    uom = models.ForeignKey(UOM, on_delete=models.CASCADE, related_name='quotation_items')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=5, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.product_name = self.product_id.name  # Auto-populate product name
        self.total = self.unit_price * self.quantity * (1 - self.discount / 100) * (1 + self.tax / 100)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_id} - {self.product_name}"

class QuotationAttachment(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/', blank=True, null=True)  # Replaced URL with FileField
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_attachments')

class QuotationComment(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='comments')
    person_name = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    comment = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.person_name} - {self.comment[:20]}"

class QuotationHistory(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='history_actions')

    def __str__(self):
        return f"{self.status} by {self.action_by}"

class QuotationRevision(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='revisions')
    revision_number = models.PositiveIntegerField()
    date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='revisions')
    status = models.CharField(max_length=20, default='Draft')
    comment = models.TextField(blank=True)
    revise_history = models.JSONField(default=dict)

    def __str__(self):
        return f"Rev {self.revision_number} - {self.quotation.quotation_id}"
    

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from masters.models import Customer, Product, Branch
from purchase.models import SerialNumber

User = get_user_model()


class SalesOrder(models.Model):
    SALES_STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Submitted(PD)', 'Submitted(PD)'),
        ('Cancelled', 'Cancelled'),
    ]
    sales_order_id = models.CharField(max_length=50, unique=True, editable=False)
    order_date = models.DateField(default=timezone.now)
    sales_rep = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, limit_choices_to={'role__role': 'Sales Representative'})
    order_type = models.CharField(max_length=50, choices=[('Standard', 'Standard'), ('Rush', 'Rush'), ('Backorder', 'Backorder')])
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=10, choices=[('IND', 'IND'), ('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('SGD', 'SGD')])
    due_date = models.DateField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True)
    shipping_method = models.CharField(max_length=50, blank=True)
    expected_delivery = models.DateField(blank=True, null=True)
    tracking_number = models.CharField(max_length=50, blank=True)
    internal_notes = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)
    global_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=SALES_STATUS_CHOICES, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.sales_order_id:
            last_order = SalesOrder.objects.order_by('id').last()
            new_num = last_order.id + 1 if last_order else 1
            self.sales_order_id = f'SO{new_num:04d}'
        super().save(*args, **kwargs)

class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    uom = models.CharField(max_length=50, blank=True)
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        subtotal = self.quantity * self.unit_price
        discount_amount = (subtotal * self.discount) / 100
        self.total = subtotal - discount_amount
        super().save(*args, **kwargs)

class SalesOrderComment(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

class SalesOrderHistory(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)

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
from django.contrib.auth import get_user_model
from masters.models import Customer, Product, UOM
from purchase.models import SerialNumber
from .models import Invoice, SalesOrder

User = get_user_model()

def generate_invoice_return_id():
    last_return = InvoiceReturn.objects.order_by('-id').first()
    return f'INVR-{str(last_return.id + 1).zfill(4) if last_return else "0001"}' if last_return else "INVR-0001"

class InvoiceReturnAttachment(models.Model):
    invoice_return = models.ForeignKey('InvoiceReturn', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='invoice_return_attachments/')

class InvoiceReturnRemark(models.Model):
    invoice_return = models.ForeignKey('InvoiceReturn', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)

class InvoiceReturnComment(models.Model):
    invoice_return = models.ForeignKey('InvoiceReturn', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
from django.contrib.auth import get_user_model
from masters.models import Customer, Product, UOM
from purchase.models import SerialNumber
from .models import InvoiceReturn, SalesOrder

User = get_user_model()

def generate_delivery_note_return_id():
    last_return = DeliveryNoteReturn.objects.order_by('-id').first()
    return f'DNR-{str(last_return.id + 1).zfill(4) if last_return else "0001"}' if last_return else "DNR-0001"

class DeliveryNoteReturnAttachment(models.Model):
    delivery_note_return = models.ForeignKey('DeliveryNoteReturn', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='delivery_note_return_attachments/')

class DeliveryNoteReturnRemark(models.Model):
    delivery_note_return = models.ForeignKey('DeliveryNoteReturn', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)

class DeliveryNoteReturnComment(models.Model):
    delivery_note_return = models.ForeignKey('DeliveryNoteReturn', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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