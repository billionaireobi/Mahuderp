"""
Core Models for Mahad Group Accounting Suite
File: core/models.py

This module contains all core business models including Company, Branch,
Employers, Vendors, Job Orders, Candidates, Invoices, Bills, and Journals.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid


User = get_user_model()


# ============================================================
# COMPANY & ORGANIZATION
# ============================================================

class Company(models.Model):
    """Company model - represents each country operation"""
    
    COUNTRY_CHOICES = [
        ('IN', 'India'),
        ('KE', 'Kenya'),
        ('AE', 'UAE'),
        ('QA', 'Qatar'),
        ('PH', 'Philippines'),
    ]
    
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('KES', 'Kenyan Shilling'),
        ('AED', 'UAE Dirham'),
        ('QAR', 'Qatari Riyal'),
        ('PHP', 'Philippine Peso'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Company name")
    short_name = models.CharField(max_length=50, help_text="Short display name")
    code = models.CharField(max_length=10, unique=True, help_text="Company code (e.g., IN, KE)")
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    
    # Currency & Tax
    base_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    tax_name = models.CharField(max_length=50, default='VAT', help_text="Tax name (VAT, GST, etc.)")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Tax rate (%)")
    
    # Invoice Settings
    invoice_prefix = models.CharField(max_length=10, default='INV')
    invoice_counter = models.IntegerField(default=1)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        ordering = ['name']
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
    
    def __str__(self):
        return self.name
    
    def next_invoice_number(self):
        """Generate next invoice number"""
        num = str(self.invoice_counter).zfill(6)
        self.invoice_counter += 1
        self.save(update_fields=['invoice_counter'])
        return f"{self.invoice_prefix}-{num}"


class CompanyProfile(models.Model):
    """Company Profile - branding and legal details"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='profile')
    
    # Legal Information
    legal_name = models.CharField(max_length=200)
    tax_registration_number = models.CharField(max_length=100, blank=True, null=True)
    trade_license = models.CharField(max_length=100, blank=True, null=True)
    
    # Branding
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    stamp = models.ImageField(upload_to='stamps/', blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    
    # Contact Information
    address = models.TextField()
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    
    # Banking Information
    bank_name = models.CharField(max_length=200)
    bank_account_name = models.CharField(max_length=200)
    bank_account_number = models.CharField(max_length=50)
    iban = models.CharField(max_length=50, blank=True, null=True)
    swift = models.CharField(max_length=20, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'company_profiles'
        verbose_name = 'Company Profile'
        verbose_name_plural = 'Company Profiles'
    
    def __str__(self):
        return f"Profile: {self.legal_name or self.company.name}"


class Branch(models.Model):
    """Branch model - office locations within a company"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    
    name = models.CharField(max_length=200, help_text="Branch name")
    code = models.CharField(max_length=20, help_text="Branch code")
    
    # Contact Information
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    
    # Branch Manager
    manager_name = models.CharField(max_length=100, blank=True, null=True)
    manager_email = models.EmailField(blank=True, null=True)
    manager_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_headquarters = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'branches'
        ordering = ['company', 'name']
        unique_together = ['company', 'code']
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
    
    def __str__(self):
        return f"{self.company.short_name if hasattr(self.company, 'short_name') else self.company.code} - {self.name}"


class Currency(models.Model):
    """Currency model - supported currencies"""
    
    code = models.CharField(max_length=3, primary_key=True, help_text="ISO currency code")
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'currencies'
        ordering = ['code']
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


# ============================================================
# MASTERS (Employers & Vendors)
# ============================================================

class Employer(models.Model):
    """Employer (Client) model - companies that hire candidates"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    
    # Contact Information
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    address = models.TextField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employers'
        ordering = ['name']
        verbose_name = 'Employer'
        verbose_name_plural = 'Employers'
    
    def __str__(self):
        return self.name


class Vendor(models.Model):
    """Vendor (Supplier) model - service providers"""
    
    VENDOR_TYPE_CHOICES = [
        ('VISA_AGENT', 'Visa Agent'),
        ('MEDICAL', 'Medical Center'),
        ('AIRLINE', 'Airline'),
        ('TRAINING', 'Training Center'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=VENDOR_TYPE_CHOICES, default='OTHER')
    country = models.CharField(max_length=100)
    
    # Contact Information
    contact = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    address = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendors'
        ordering = ['name']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


# ============================================================
# RECRUITMENT (Job Orders & Candidates)
# ============================================================

class JobOrder(models.Model):
    """Job Order model - recruitment assignments from employers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_orders')
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='job_orders')
    
    position_title = models.CharField(max_length=200)
    num_positions = models.IntegerField(help_text="Number of positions to fill")
    agreed_fee = models.DecimalField(max_digits=12, decimal_places=2, help_text="Fee per candidate")
    currency = models.CharField(max_length=3, choices=Company.CURRENCY_CHOICES, default='USD')
    
    notes = models.TextField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_orders'
        ordering = ['-created_at']
        verbose_name = 'Job Order'
        verbose_name_plural = 'Job Orders'
    
    def __str__(self):
        return f"{self.position_title} - {self.employer.name}"


class Candidate(models.Model):
    """Candidate model - individuals being processed for deployment"""
    
    STAGE_CHOICES = [
        ('SOURCING', 'Sourcing'),
        ('SCREENING', 'Screening'),
        ('DOCUMENTATION', 'Documentation'),
        ('VISA', 'Visa Processing'),
        ('MEDICAL', 'Medical'),
        ('TICKET', 'Ticket Issued'),
        ('DEPLOYED', 'Deployed'),
        ('INVOICED', 'Invoiced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, related_name='candidates')
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    passport_number = models.CharField(max_length=50)
    nationality = models.CharField(max_length=100)
    
    # Processing Status
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='SOURCING')
    deployed_date = models.DateField(blank=True, null=True)
    
    # Notes
    remarks = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'candidates'
        ordering = ['-created_at']
        verbose_name = 'Candidate'
        verbose_name_plural = 'Candidates'
    
    def __str__(self):
        return f"{self.full_name} ({self.passport_number})"


class CandidateCost(models.Model):
    """Candidate Cost model - tracks costs per candidate (WIP)"""
    
    COST_TYPE_CHOICES = [
        ('VISA', 'Visa Fee'),
        ('MEDICAL', 'Medical Test'),
        ('TICKET', 'Air Ticket'),
        ('TRAINING', 'Training'),
        ('DOCUMENTATION', 'Documentation'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='costs')
    
    cost_type = models.CharField(max_length=20, choices=COST_TYPE_CHOICES)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, blank=True, null=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Company.CURRENCY_CHOICES)
    reimbursable = models.BooleanField(default=True, help_text="Can be billed to employer")
    
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    
    # Link to bill if paid
    bill = models.ForeignKey('Bill', on_delete=models.SET_NULL, blank=True, null=True, related_name='candidate_costs')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'candidate_costs'
        ordering = ['-date']
        verbose_name = 'Candidate Cost'
        verbose_name_plural = 'Candidate Costs'
    
    def __str__(self):
        return f"{self.get_cost_type_display()} - {self.amount} {self.currency}"


# ============================================================
# ACCOUNTING (Invoices & Bills)
# ============================================================

class Invoice(models.Model):
    """Invoice model - Accounts Receivable"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='invoices')
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, blank=True, null=True, related_name='invoices')
    candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, blank=True, null=True, related_name='invoices')
    
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    
    currency = models.CharField(max_length=3, choices=Company.CURRENCY_CHOICES)
    
    # Amounts
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    posted_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-invoice_date']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.company.next_invoice_number()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.invoice_number


class InvoiceLine(models.Model):
    """Invoice Line model - line items on invoices"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    
    description = models.CharField(max_length=500)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    
    # Optional link to candidate
    candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, blank=True, null=True)
    
    class Meta:
        db_table = 'invoice_lines'
        verbose_name = 'Invoice Line'
        verbose_name_plural = 'Invoice Lines'
    
    def save(self, *args, **kwargs):
        self.amount = Decimal(self.quantity) * self.unit_price
        super().save(*args, **kwargs)
        # Recalculate invoice totals
        self.invoice.total_amount = sum(line.amount for line in self.invoice.lines.all())
        self.invoice.save(update_fields=['total_amount'])
    
    def __str__(self):
        return f"{self.description} - {self.amount}"


class Bill(models.Model):
    """Bill model - Accounts Payable (Vendor Bills)"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bills')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='bills')
    
    bill_number = models.CharField(max_length=50, unique=True)
    bill_date = models.DateField()
    due_date = models.DateField()
    
    currency = models.CharField(max_length=3, choices=Company.CURRENCY_CHOICES)
    
    # Amounts
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    posted_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bills'
        ordering = ['-bill_date']
        verbose_name = 'Bill'
        verbose_name_plural = 'Bills'
    
    def save(self, *args, **kwargs):
        if not self.bill_number:
            prefix = "BILL-"
            count = Bill.objects.filter(company=self.company).count() + 1
            self.bill_number = f"{prefix}{count:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.bill_number


class BillLine(models.Model):
    """Bill Line model - line items on bills"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='lines')
    
    description = models.CharField(max_length=500)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    
    class Meta:
        db_table = 'bill_lines'
        verbose_name = 'Bill Line'
        verbose_name_plural = 'Bill Lines'
    
    def save(self, *args, **kwargs):
        self.amount = Decimal(self.quantity) * self.unit_price
        super().save(*args, **kwargs)
        # Recalculate bill totals
        self.bill.total_amount = sum(line.amount for line in self.bill.lines.all())
        self.bill.save(update_fields=['total_amount'])
    
    def __str__(self):
        return self.description


# ============================================================
# PAYMENTS & RECEIPTS
# ============================================================

class Receipt(models.Model):
    """Receipt model - payments received from customers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='receipts')
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='receipts')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, blank=True, null=True, related_name='receipts')
    
    receipt_number = models.CharField(max_length=50, unique=True)
    receipt_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Company.CURRENCY_CHOICES)
    
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'receipts'
        ordering = ['-receipt_date']
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'
    
    def __str__(self):
        return f"{self.receipt_number} - {self.amount} {self.currency}"


class Payment(models.Model):
    """Payment model - payments made to vendors"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payments')
    bill = models.ForeignKey(Bill, on_delete=models.SET_NULL, blank=True, null=True, related_name='payments')
    
    payment_number = models.CharField(max_length=50, unique=True)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Company.CURRENCY_CHOICES)
    
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"{self.payment_number} - {self.amount} {self.currency}"


# ============================================================
# GENERAL LEDGER (Journals)
# ============================================================

class Journal(models.Model):
    """Journal model - general ledger entries"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journals')
    
    journal_number = models.CharField(max_length=50, unique=True)
    reference = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField()
    
    posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(blank=True, null=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='posted_journals')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_journals')
    
    class Meta:
        db_table = 'journals'
        ordering = ['-date']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'
    
    def __str__(self):
        return f"{self.journal_number} - {self.reference}"


class JournalLine(models.Model):
    """Journal Line model - individual debit/credit entries"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='lines')
    
    account = models.CharField(max_length=100, help_text="Account code/name")
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    description = models.CharField(max_length=500, blank=True, null=True)
    
    class Meta:
        db_table = 'journal_lines'
        verbose_name = 'Journal Line'
        verbose_name_plural = 'Journal Lines'
    
    def __str__(self):
        return f"{self.account} - Dr: {self.debit} Cr: {self.credit}"