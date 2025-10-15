from django.db import models
from django.utils import timezone
from masters.models import Supplier, Product

def get_default_po_date():
    return timezone.now().date()

class PurchaseOrder(models.Model):
    PO_ID = models.CharField(max_length=20, unique=True, editable=False)
    PO_date = models.DateField(default=get_default_po_date)
    delivery_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Partially Received', 'Partially Received'), 
                ('Closed', 'Closed'), ('Canceled', 'Canceled')],
        default='Draft'
    )
    sales_order_reference = models.CharField(max_length=100)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    supplier_name = models.CharField(max_length=100)
    payment_terms = models.CharField(max_length=50)
    inco_terms = models.CharField(max_length=50)
    currency = models.CharField(max_length=10)
    notes_comments = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    global_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_summary = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2)
    rounding_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_order_value = models.DecimalField(max_digits=10, decimal_places=2)
    upload_file_path = models.FileField(upload_to='upload/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.PO_ID:
            last_po = PurchaseOrder.objects.order_by('-id').first()
            new_id = f'PO-{timezone.now().strftime("%Y%m%d")}-{str(last_po.id + 1).zfill(3) if last_po else "001"}'
            self.PO_ID = new_id
        super().save(*args, **kwargs)

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    qty_ordered = models.IntegerField()
    insufficient_stock = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.qty_ordered * self.unit_price * (1 - self.discount/100) * (1 + self.tax/100)
        super().save(*args, **kwargs)

class PurchaseOrderHistory(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=100)
    performed_by = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True)

class PurchaseOrderComment(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField(null=True, blank=True)
    created_by = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now)


from django.db import models
from django.utils import timezone
from django.conf import settings
from masters.models import Supplier, Product, Warehouse, Department

def get_default_grn_date():
    return timezone.now().date()

class StockReceiptAttachment(models.Model):
    stock_receipt = models.ForeignKey('StockReceipt', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='stock_receipt_attachments/')

class StockReceiptRemark(models.Model):
    stock_receipt = models.ForeignKey('StockReceipt', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

class StockReceipt(models.Model):
    GRN_ID = models.CharField(max_length=20, unique=True, editable=False)
    PO_reference = models.ForeignKey('purchase.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)
    received_date = models.DateField(default=get_default_grn_date)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    supplier_dn_no = models.CharField(max_length=100, blank=True)
    supplier_invoice_no = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_receipts', limit_choices_to={'department__department_name': 'Sales'})
    qc_done_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qc_receipts', limit_choices_to={'department__department_name': 'Sales'})
    status = models.CharField(
        max_length=20,
        choices=[('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Returned', 'Returned'), ('Cancelled', 'Cancelled')],
        default='Draft'
    )

    def save(self, *args, **kwargs):
        if not self.GRN_ID:
            last_grn = StockReceipt.objects.order_by('-id').first()
            new_id = f'GRN-{timezone.now().strftime("%Y%m%d")}-{str(last_grn.id + 1).zfill(4) if last_grn else "0001"}'
            self.GRN_ID = new_id
        super().save(*args, **kwargs)

class StockReceiptItem(models.Model):
    stock_receipt = models.ForeignKey(StockReceipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    uom = models.CharField(max_length=50, blank=True)
    qty_ordered = models.IntegerField(blank=True, null=True)
    qty_received = models.IntegerField()
    accepted_qty = models.IntegerField()
    rejected_qty = models.IntegerField(default=0)
    qty_returned = models.IntegerField(default=0)
    stock_dim = models.CharField(max_length=20, choices=[('None', 'None'), ('Serial', 'Serial'), ('Batch', 'Batch')], default='None')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.rejected_qty:
            self.rejected_qty = self.qty_received - self.accepted_qty
        if self.rejected_qty < 0:
            self.rejected_qty = 0
        self.total = self.qty_received * self.unit_price * (1 - self.discount / 100) * (1 + self.tax / 100)
        super().save(*args, **kwargs)

class SerialNumber(models.Model):
    stock_receipt_item = models.ForeignKey(StockReceiptItem, on_delete=models.CASCADE, related_name='serial_numbers')
    serial_no = models.CharField(max_length=50, unique=True)

class BatchNumber(models.Model):
    stock_receipt_item = models.ForeignKey(StockReceiptItem, on_delete=models.CASCADE, related_name='batch_numbers')
    batch_no = models.CharField(max_length=50, unique=True)
    batch_qty = models.IntegerField()
    mfg_date = models.DateField()
    expiry_date = models.DateField()

class BatchSerialNumber(models.Model):
    batch_number = models.ForeignKey(BatchNumber, on_delete=models.CASCADE, related_name='serial_numbers')
    serial_no = models.CharField(max_length=50, unique=True)


from django.db import models
from django.utils import timezone

from purchase.models import PurchaseOrder
from .models import StockReceipt, StockReceiptItem
from masters.models import Supplier, Product, Warehouse

def get_default_srn_date():
    return timezone.now().date()

class StockReturnAttachment(models.Model):
    stock_return = models.ForeignKey('StockReturn', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='stock_return_attachments/')

class StockReturnRemark(models.Model):
    stock_return = models.ForeignKey('StockReturn', on_delete=models.CASCADE, related_name='remarks')
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

class StockReturn(models.Model):
    SRN_ID = models.CharField(max_length=20, unique=True, editable=False)
    PO_reference = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    GRN_reference = models.ForeignKey(StockReceipt, on_delete=models.SET_NULL, null=True, blank=True)
    received_date = models.DateField()
    return_date = models.DateField(default=get_default_srn_date)
    return_initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'department__department_name': 'Sales'})
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Partially Returned', 'Partially Returned'), ('Cancelled', 'Cancelled')],
        default='Draft'
    )
    original_purchased_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    global_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    return_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    global_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rounding_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_to_recover = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.SRN_ID:
            last_srn = StockReturn.objects.order_by('-id').first()
            new_id = f'SRN-{timezone.now().strftime("%Y%m%d")}-{str(last_srn.id + 1).zfill(4) if last_srn else "0001"}'
            self.SRN_ID = new_id
        if self.pk and self.items.exists():
            self.return_subtotal = sum(item.total for item in self.items.all())
            self.global_discount_amount = self.return_subtotal * (self.global_discount / 100)
            self.amount_to_recover = self.return_subtotal - self.global_discount_amount + self.rounding_adjustment
        super().save(*args, **kwargs)

class StockReturnItem(models.Model):
    stock_return = models.ForeignKey(StockReturn, on_delete=models.CASCADE, related_name='items')
    stock_receipt_item = models.ForeignKey(StockReceiptItem, on_delete=models.SET_NULL, null=True, blank=True)  # Link to original item
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    uom = models.CharField(max_length=50, blank=True)
    qty_ordered = models.IntegerField(blank=True, null=True)
    qty_rejected = models.IntegerField(blank=True, null=True)
    qty_returned = models.IntegerField()
    return_reason = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if self.stock_receipt_item:
            self.product = self.stock_receipt_item.product
            self.uom = self.stock_receipt_item.uom
            self.qty_ordered = self.stock_receipt_item.qty_ordered
            self.qty_rejected = self.stock_receipt_item.rejected_qty
            self.unit_price = self.stock_receipt_item.unit_price
            self.tax = self.stock_receipt_item.tax
            self.discount = self.stock_receipt_item.discount
        self.total = self.qty_returned * self.unit_price * (1 - self.discount / 100) * (1 + self.tax / 100)
        if self.qty_returned > (self.qty_rejected or 0):
            raise ValueError("Qty returned cannot exceed rejected qty")
        super().save(*args, **kwargs)

class SerialNumberReturn(models.Model):
    stock_return_item = models.ForeignKey(StockReturnItem, on_delete=models.CASCADE, related_name='serial_numbers')
    serial_no = models.CharField(max_length=50)