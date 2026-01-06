from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from masters.models import Branch, Department,Supplier,Customer, Product
from core.models import Candidate
from crm.models import Invoice
from purchase.models import PurchaseOrder

User = get_user_model()

def generate_credit_note_id():  
    last_cn = CreditNote.objects.order_by('-id').first()
    return f'CRN-{str(last_cn.id + 1).zfill(4) if last_cn else "0001"}' if last_cn else "CRN-0001"



class CreditNoteAttachment(models.Model):
    credit_note = models.ForeignKey('CreditNote', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='credit_note_attachments/')

class CreditNoteRemark(models.Model):
    credit_note = models.ForeignKey('CreditNote', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

class CreditNote(models.Model):
    CREDIT_NOTE_ID = models.CharField(max_length=20, unique=True, editable=False, default=generate_credit_note_id)
    credit_note_date = models.DateField(default=timezone.now)
    invoice_reference = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True, limit_choices_to={'department__department_name__icontains': 'sales'})
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('EUR', 'EUR'), ('INR', 'INR'), ('GBP', 'GBP'), ('SGD', 'SGD')], default='INR')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    # Removed customer_id since it clashes with customer
    billing_address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    invoice_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    payment_terms = models.CharField(max_length=20, choices=[('Net 15', 'Net 15'), ('Net 30', 'Net 30'), ('Net 45', 'Net 45'), ('Due on Receipt', 'Due on Receipt')], default='Net 30')
    invoice_status = models.CharField(max_length=20, choices=[('Draft', 'Draft'), ('Sent', 'Sent'), ('Paid', 'Paid'), ('Overdue', 'Overdue'), ('Cancelled', 'Cancelled')], default='Draft')
    payment_status = models.CharField(max_length=20, choices=[('Paid', 'Paid'), ('Partial', 'Partial'), ('Unpaid', 'Unpaid')], default='Unpaid')
    invoice_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class CreditNoteItem(models.Model):
    credit_note = models.ForeignKey(CreditNote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    # Removed product_id since it clashes with product
    returned_qty = models.IntegerField(default=0)
    uom = models.CharField(max_length=50, blank=True)
    return_reason = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Fixed to use max_digits
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

class CreditNotePaymentRefund(models.Model):
    credit_note = models.OneToOneField(CreditNote, on_delete=models.CASCADE, related_name='payment_refund')
    amount_paid_by_customer = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance_due_by_customer = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    invoice_return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    balance_to_refund = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    refund_mode = models.CharField(max_length=20, choices=[('None', 'None'), ('Refund', 'Refund'), ('Adjust', 'Adjust'), ('Refund & Adjust', 'Refund & Adjust')], default='None')
    refund_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    refund_date = models.DateField(blank=True, null=True, editable=False)
    adjusted_invoice_reference = models.CharField(max_length=100, blank=True, editable=False)

    def save(self, *args, **kwargs):
        credit_note = self.credit_note
        self.balance_due_by_customer = credit_note.invoice_total - self.amount_paid_by_customer
        if credit_note.invoice_reference and credit_note.invoice_reference.summary:
            self.invoice_return_amount = sum(item.total for item in credit_note.items.all())  # Simplified
            self.balance_to_refund = self.invoice_return_amount - self.refund_paid
            if self.refund_mode in ['Refund', 'Refund & Adjust'] and self.invoice_return_amount > 0:
                self.editable = True
            else:
                self.editable = False
        super().save(*args, **kwargs)


def generate_debit_note_id():
    last_dn = DebitNote.objects.order_by('-id').first()
    return f'DBN-{str(last_dn.id + 1).zfill(4) if last_dn else "0001"}' if last_dn else "DBN-0001"

class DebitNoteAttachment(models.Model):
    debit_note = models.ForeignKey('DebitNote', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='debit_note_attachments/')

class DebitNoteRemark(models.Model):
    debit_note = models.ForeignKey('DebitNote', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

class DebitNote(models.Model):
    DEBIT_NOTE_ID = models.CharField(max_length=20, unique=True, editable=False, default=generate_debit_note_id)
    debit_note_date = models.DateField(default=timezone.now)
    po_reference = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True, limit_choices_to={'department__department_name__icontains': 'sales'})
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    currency = models.CharField(max_length=3, choices=[('USD', 'USD'), ('EUR', 'EUR'), ('INR', 'INR'), ('GBP', 'GBP'), ('SGD', 'SGD')], default='INR')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    # Removed supplier_id since it clashes with supplier
    po_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    payment_terms = models.CharField(max_length=20, choices=[('Net 30', 'Net 30'), ('Net 45', 'Net 45'), ('Net 90', 'Net 90'), ('Credit', 'Credit'), ('Advance', 'Advance'), ('Partial Advance', 'Partial Advance'), ('On Delivery (COD)', 'On Delivery (COD)'), ('Upon Invoice', 'Upon Invoice')], default='Net 30')
    inco_terms = models.CharField(max_length=30, choices=[('FOB', 'FOB (Free On Board)'), ('CIF', 'CIF (Cost, Insurance & Freight)'), ('EXW', 'EXW (Ex Works)'), ('DDP', 'DDP (Delivered Duty Paid)'), ('DAP', 'DAP (Delivered at Place)'), ('FCA', 'FCA (Free Carrier)'), ('CFR', 'CFR (Cost and Freight)')], default='FOB')
    payment_status = models.CharField(max_length=20, choices=[('Paid', 'Paid'), ('Partial', 'Partial'), ('Unpaid', 'Unpaid')], default='Unpaid')
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    purchase_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class DebitNoteItem(models.Model):
    debit_note = models.ForeignKey(DebitNote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    # Removed product_id since it clashes with product
    returned_qty = models.IntegerField(default=0)
    uom = models.CharField(max_length=50, blank=True)
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

class DebitNotePaymentRecover(models.Model):
    debit_note = models.OneToOneField(DebitNote, on_delete=models.CASCADE, related_name='payment_recover')
    amount_paid_to_vendor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance_due_to_vendor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    purchase_return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    balance_to_recover = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    refund_mode = models.CharField(max_length=20, choices=[('None', 'None'), ('Refund', 'Refund'), ('Adjust', 'Adjust'), ('Refund & Adjust', 'Refund & Adjust')], default='None')
    refund_received = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    refund_date = models.DateField(blank=True, null=True, editable=False)
    adjusted_invoice_reference = models.CharField(max_length=100, blank=True, editable=False)

    def save(self, *args, **kwargs):
        debit_note = self.debit_note
        self.balance_due_to_vendor = debit_note.purchase_total - self.amount_paid_to_vendor
        if debit_note.po_reference:
            self.purchase_return_amount = sum(item.total for item in debit_note.items.all())  # Simplified
            self.balance_to_recover = self.purchase_return_amount - self.refund_received
            if self.refund_mode in ['Refund', 'Refund & Adjust'] and self.purchase_return_amount > 0:
                self.editable = True
            else:
                self.editable = False
        super().save(*args, **kwargs)