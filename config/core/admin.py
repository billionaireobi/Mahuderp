"""
Django Admin Configuration for Core Models
File: core/admin.py
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Company, CompanyProfile, Branch, Currency,
    Employer, Vendor,
    JobOrder, Candidate, CandidateCost,
    Invoice, InvoiceLine, Bill, BillLine,
    Receipt, Payment, Journal, JournalLine
)


# ============================================================
# COMPANY & ORGANIZATION
# ============================================================

class CompanyProfileInline(admin.StackedInline):
    """Inline for Company Profile"""
    model = CompanyProfile
    can_delete = False
    verbose_name = 'Company Profile'
    verbose_name_plural = 'Company Profile'
    extra = 0
    fields = [
        'legal_name', 'tax_registration_number', 'trade_license',
        'logo', 'stamp', 'signature',
        'address', 'phone', 'email', 'website',
        'bank_name', 'bank_account_name', 'bank_account_number', 'iban', 'swift'
    ]


class BranchInline(admin.TabularInline):
    """Inline for Branches"""
    model = Branch
    extra = 0
    fields = ['name', 'code', 'city', 'phone', 'is_headquarters', 'is_active']
    readonly_fields = []


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin for Company model"""
    
    list_display = [
        'name', 'short_name', 'code', 'country', 'base_currency',
        'tax_rate', 'is_active', 'created_at'
    ]
    list_filter = ['country', 'base_currency', 'is_active', 'created_at']
    search_fields = ['name', 'short_name', 'code']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'short_name', 'code', 'country')
        }),
        ('Currency & Tax Settings', {
            'fields': ('base_currency', 'tax_name', 'tax_rate')
        }),
        ('Invoice Settings', {
            'fields': ('invoice_prefix', 'invoice_counter')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CompanyProfileInline, BranchInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('profile')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """Admin for Branch model"""
    
    list_display = [
        'name', 'code', 'company', 'city', 'phone',
        'is_headquarters', 'is_active', 'created_at'
    ]
    list_filter = ['company', 'is_headquarters', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'city', 'manager_name']
    ordering = ['company', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'name', 'code')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'postal_code', 'phone', 'email')
        }),
        ('Branch Manager', {
            'fields': ('manager_name', 'manager_email', 'manager_phone'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_headquarters', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """Admin for Currency model"""
    
    list_display = ['code', 'name', 'symbol', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    ordering = ['code']
    
    fieldsets = (
        ('Currency Information', {
            'fields': ('code', 'name', 'symbol', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


# ============================================================
# MASTERS (Employers & Vendors)
# ============================================================

@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    """Admin for Employer model"""
    
    list_display = ['code', 'name', 'country', 'email', 'phone', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['code', 'name', 'email', 'contact_person']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'country')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'email', 'phone', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Admin for Vendor model"""
    
    list_display = ['name', 'type', 'country', 'contact', 'email', 'phone', 'created_at']
    list_filter = ['type', 'country', 'created_at']
    search_fields = ['name', 'contact', 'email']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'country')
        }),
        ('Contact Information', {
            'fields': ('contact', 'email', 'phone', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


# ============================================================
# RECRUITMENT
# ============================================================

class CandidateInline(admin.TabularInline):
    """Inline for Candidates in Job Order"""
    model = Candidate
    extra = 0
    fields = ['full_name', 'passport_number', 'nationality', 'current_stage', 'deployed_date']
    readonly_fields = ['created_at']


@admin.register(JobOrder)
class JobOrderAdmin(admin.ModelAdmin):
    """Admin for Job Order model"""
    
    list_display = [
        'position_title', 'company', 'employer', 'num_positions',
        'agreed_fee', 'currency', 'is_active', 'created_at'
    ]
    list_filter = ['company', 'is_active', 'created_at']
    search_fields = ['position_title', 'employer__name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Job Information', {
            'fields': ('company', 'employer', 'position_title', 'num_positions')
        }),
        ('Financial', {
            'fields': ('agreed_fee', 'currency')
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CandidateInline]


class CandidateCostInline(admin.TabularInline):
    """Inline for Candidate Costs"""
    model = CandidateCost
    extra = 0
    fields = ['cost_type', 'vendor', 'amount', 'currency', 'reimbursable', 'date']
    readonly_fields = ['created_at']


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Admin for Candidate model"""
    
    list_display = [
        'full_name', 'passport_number', 'nationality', 'job_order',
        'current_stage', 'deployed_date', 'created_at'
    ]
    list_filter = ['current_stage', 'nationality', 'created_at']
    search_fields = ['full_name', 'passport_number']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Job Order', {
            'fields': ('job_order',)
        }),
        ('Personal Information', {
            'fields': ('full_name', 'passport_number', 'nationality')
        }),
        ('Processing Status', {
            'fields': ('current_stage', 'deployed_date', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CandidateCostInline]


@admin.register(CandidateCost)
class CandidateCostAdmin(admin.ModelAdmin):
    """Admin for Candidate Cost model"""
    
    list_display = [
        'candidate', 'cost_type', 'vendor', 'amount', 'currency',
        'reimbursable', 'date', 'created_at'
    ]
    list_filter = ['cost_type', 'reimbursable', 'currency', 'date']
    search_fields = ['candidate__full_name', 'vendor__name', 'description']
    ordering = ['-date']
    
    fieldsets = (
        ('Candidate', {
            'fields': ('candidate',)
        }),
        ('Cost Details', {
            'fields': ('cost_type', 'vendor', 'amount', 'currency', 'reimbursable')
        }),
        ('Additional Information', {
            'fields': ('description', 'date', 'bill')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


# ============================================================
# INVOICES (Accounts Receivable)
# ============================================================

class InvoiceLineInline(admin.TabularInline):
    """Inline for Invoice Lines"""
    model = InvoiceLine
    extra = 1
    fields = ['description', 'candidate', 'quantity', 'unit_price', 'amount']
    readonly_fields = ['amount']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin for Invoice model"""
    
    list_display = [
        'invoice_number', 'employer', 'invoice_date', 'due_date',
        'total_amount', 'currency', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'company', 'currency', 'invoice_date']
    search_fields = ['invoice_number', 'employer__name']
    ordering = ['-invoice_date']
    date_hierarchy = 'invoice_date'
    
    fieldsets = (
        ('Reference', {
            'fields': ('company', 'employer', 'job_order', 'candidate')
        }),
        ('Invoice Details', {
            'fields': ('invoice_number', 'invoice_date', 'due_date', 'currency')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'tax_amount', 'net_amount', 'amount_paid')
        }),
        ('Status', {
            'fields': ('status', 'posted_at', 'paid_at')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['invoice_number', 'created_at', 'updated_at', 'posted_at', 'paid_at']
    inlines = [InvoiceLineInline]
    
    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'DRAFT': 'gray',
            'POSTED': 'blue',
            'SENT': 'orange',
            'PAID': 'green',
            'CANCELLED': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ============================================================
# BILLS (Accounts Payable)
# ============================================================

class BillLineInline(admin.TabularInline):
    """Inline for Bill Lines"""
    model = BillLine
    extra = 1
    fields = ['description', 'quantity', 'unit_price', 'amount']
    readonly_fields = ['amount']


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    """Admin for Bill model"""
    
    list_display = [
        'bill_number', 'vendor', 'bill_date', 'due_date',
        'total_amount', 'currency', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'company', 'currency', 'bill_date']
    search_fields = ['bill_number', 'vendor__name']
    ordering = ['-bill_date']
    date_hierarchy = 'bill_date'
    
    fieldsets = (
        ('Reference', {
            'fields': ('company', 'vendor')
        }),
        ('Bill Details', {
            'fields': ('bill_number', 'bill_date', 'due_date', 'currency')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'tax_amount', 'amount_paid')
        }),
        ('Status', {
            'fields': ('status', 'posted_at', 'paid_at')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['bill_number', 'created_at', 'updated_at', 'posted_at', 'paid_at']
    inlines = [BillLineInline]
    
    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'DRAFT': 'gray',
            'POSTED': 'blue',
            'PAID': 'green',
            'CANCELLED': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ============================================================
# RECEIPTS & PAYMENTS
# ============================================================

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """Admin for Receipt model"""
    
    list_display = [
        'receipt_number', 'employer', 'receipt_date', 'amount',
        'currency', 'payment_method', 'created_at'
    ]
    list_filter = ['company', 'currency', 'receipt_date', 'payment_method']
    search_fields = ['receipt_number', 'employer__name', 'reference_number']
    ordering = ['-receipt_date']
    date_hierarchy = 'receipt_date'
    
    fieldsets = (
        ('Reference', {
            'fields': ('company', 'employer', 'invoice')
        }),
        ('Receipt Details', {
            'fields': ('receipt_number', 'receipt_date', 'amount', 'currency')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'reference_number')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment model"""
    
    list_display = [
        'payment_number', 'vendor', 'payment_date', 'amount',
        'currency', 'payment_method', 'created_at'
    ]
    list_filter = ['company', 'currency', 'payment_date', 'payment_method']
    search_fields = ['payment_number', 'vendor__name', 'reference_number']
    ordering = ['-payment_date']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Reference', {
            'fields': ('company', 'vendor', 'bill')
        }),
        ('Payment Details', {
            'fields': ('payment_number', 'payment_date', 'amount', 'currency')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'reference_number')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


# ============================================================
# JOURNALS (General Ledger)
# ============================================================

class JournalLineInline(admin.TabularInline):
    """Inline for Journal Lines"""
    model = JournalLine
    extra = 2
    fields = ['account', 'description', 'debit', 'credit']


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    """Admin for Journal model"""
    
    list_display = [
        'journal_number', 'reference', 'date', 'description',
        'posted', 'created_at'
    ]
    list_filter = ['posted', 'company', 'date']
    search_fields = ['journal_number', 'reference', 'description']
    ordering = ['-date']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Journal Information', {
            'fields': ('company', 'journal_number', 'reference', 'date', 'description')
        }),
        ('Posting Status', {
            'fields': ('posted', 'posted_at', 'posted_by')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'posted_at']
    inlines = [JournalLineInline]


# Customize admin site header
admin.site.site_header = 'Mahad Group Accounting Administration'
admin.site.site_title = 'Mahad Admin'
admin.site.index_title = 'Welcome to Mahad Group Accounting Admin'