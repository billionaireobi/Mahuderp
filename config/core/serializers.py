"""
Core Serializers for Mahad Group Accounting Suite
File: core/serializers.py
"""
from rest_framework import serializers
from .models import (
    Company, CompanyProfile, Branch, Currency,
    Employer, Vendor,
    JobOrder, Candidate, CandidateCost,
    Invoice, InvoiceLine, Bill, BillLine,
    Receipt, Payment, Journal, JournalLine
)
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


# ============================================================
# COMPANY & ORGANIZATION
# ============================================================

class CompanyProfileSerializer(serializers.ModelSerializer):
    """Serializer for Company Profile"""
    
    class Meta:
        model = CompanyProfile
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company"""
    
    profile = CompanyProfileSerializer(read_only=True)
    
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'invoice_counter']


class BranchSerializer(serializers.ModelSerializer):
    """Serializer for Branch"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for Currency"""
    
    class Meta:
        model = Currency
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================================
# MASTERS
# ============================================================

class EmployerSerializer(serializers.ModelSerializer):
    """Serializer for Employer"""
    
    class Meta:
        model = Employer
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor"""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================
# RECRUITMENT
# ============================================================

class JobOrderSerializer(serializers.ModelSerializer):
    """Serializer for Job Order"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    candidate_count = serializers.SerializerMethodField()
    
    class Meta:
        model = JobOrder
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_candidate_count(self, obj):
        return obj.candidates.count()

    # Candidate count is an integer
    get_candidate_count = extend_schema_field(OpenApiTypes.INT)(get_candidate_count)


class CandidateCostSerializer(serializers.ModelSerializer):
    """Serializer for Candidate Cost"""
    
    cost_type_display = serializers.CharField(source='get_cost_type_display', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    
    class Meta:
        model = CandidateCost
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CandidateSerializer(serializers.ModelSerializer):
    """Serializer for Candidate"""
    
    job_order_title = serializers.CharField(source='job_order.position_title', read_only=True)
    employer_name = serializers.CharField(source='job_order.employer.name', read_only=True)
    stage_display = serializers.CharField(source='get_current_stage_display', read_only=True)
    costs = CandidateCostSerializer(many=True, read_only=True)
    total_costs = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_costs(self, obj):
        return sum(cost.amount for cost in obj.costs.all())

    # Total costs are numeric (sum of amounts)
    get_total_costs = extend_schema_field(OpenApiTypes.NUMBER)(get_total_costs)


# ============================================================
# ACCOUNTING
# ============================================================

class InvoiceLineSerializer(serializers.ModelSerializer):
    """Serializer for Invoice Line"""
    
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    
    class Meta:
        model = InvoiceLine
        fields = '__all__'
        read_only_fields = ['id', 'amount']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lines = InvoiceLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['id', 'invoice_number', 'created_at', 'updated_at', 'posted_at', 'paid_at']


class BillLineSerializer(serializers.ModelSerializer):
    """Serializer for Bill Line"""
    
    class Meta:
        model = BillLine
        fields = '__all__'
        read_only_fields = ['id', 'amount']


class BillSerializer(serializers.ModelSerializer):
    """Serializer for Bill"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    lines = BillLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = Bill
        fields = '__all__'
        read_only_fields = ['id', 'bill_number', 'created_at', 'updated_at', 'posted_at', 'paid_at']


class ReceiptSerializer(serializers.ModelSerializer):
    """Serializer for Receipt"""
    
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    
    class Meta:
        model = Receipt
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment"""
    
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class JournalLineSerializer(serializers.ModelSerializer):
    """Serializer for Journal Line"""
    
    class Meta:
        model = JournalLine
        fields = '__all__'
        read_only_fields = ['id']


class JournalSerializer(serializers.ModelSerializer):
    """Serializer for Journal"""
    
    lines = JournalLineSerializer(many=True, read_only=True)
    posted_by_name = serializers.CharField(source='posted_by.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Journal
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'posted_at']