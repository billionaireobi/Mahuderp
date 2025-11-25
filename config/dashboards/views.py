"""
Dashboard Views for Mahad Group Accounting Suite
File: dashboards/views.py

Role-specific dashboard views with KPIs and analytics
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

# Ensure we reference the project's user model (supports custom user models)
from django.contrib.auth import get_user_model
User = get_user_model()

from core.models import (
    Company, Branch, Employer, Vendor,
    JobOrder, Candidate, CandidateCost,
    Invoice, Bill, Receipt, Payment
)


# ============================================================
# MAIN DASHBOARD ROUTER
# ============================================================

# @extend_schema(responses=OpenApiTypes.OBJECT)
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def dashboard(request):
#     """
#     Main dashboard endpoint - routes to role-specific dashboard
#     GET /api/dashboard/
#     """
#     user = request.user
    
#     # Route based on role
#     if user.role == 'HQ_ADMIN':
#         return hq_admin_dashboard(request)
#     elif user.role == 'COUNTRY_MANAGER':
#         return country_manager_dashboard(request)
#     elif user.role == 'FINANCE_MANAGER':
#         return finance_manager_dashboard(request)
#     elif user.role == 'ACCOUNTANT':
#         return accountant_dashboard(request)
#     elif user.role == 'BRANCH_USER':
#         return branch_user_dashboard(request)
#     elif user.role == 'AUDITOR':
#         return auditor_dashboard(request)
#     else:
#         return Response({
#             'error': 'Invalid user role'
#         }, status=status.HTTP_403_FORBIDDEN)

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """
    Main dashboard endpoint - routes to role-specific dashboard
    GET /api/dashboard/
    """
    user = request.user
    django_request = request._request   # ⬅️ FIX HERE

    if user.role == 'HQ_ADMIN':
        return hq_admin_dashboard(django_request)

    elif user.role == 'COUNTRY_MANAGER':
        return country_manager_dashboard(django_request)

    elif user.role == 'FINANCE_MANAGER':
        return finance_manager_dashboard(django_request)

    elif user.role == 'ACCOUNTANT':
        return accountant_dashboard(django_request)

    elif user.role == 'BRANCH_USER':
        return branch_user_dashboard(django_request)

    elif user.role == 'AUDITOR':
        return auditor_dashboard(django_request)

    return Response({
        'error': 'Invalid user role'
    }, status=status.HTTP_403_FORBIDDEN)

# ============================================================
# HQ ADMIN DASHBOARD
# ============================================================

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hq_admin_dashboard(request):
    """
    HQ Admin Dashboard - Consolidated view across all companies
    GET /api/dashboard/hq-admin/
    """
    # Date filters
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    this_year_start = today.replace(month=1, day=1)
    
    # Company Statistics
    companies = Company.objects.filter(is_active=True)
    total_companies = companies.count()
    
    companies_data = []
    for company in companies:
        companies_data.append({
            'id': str(company.id),
            'name': company.name,
            'code': company.code,
            'country': company.get_country_display(),
            'active_job_orders': JobOrder.objects.filter(company=company, is_active=True).count(),
            'candidates_deployed': Candidate.objects.filter(
                job_order__company=company,
                current_stage='DEPLOYED'
            ).count(),
            'revenue_ytd': Invoice.objects.filter(
                company=company,
                invoice_date__gte=this_year_start,
                status__in=['POSTED', 'SENT', 'PAID']
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
        })
    
    # Global Statistics
    total_job_orders = JobOrder.objects.filter(is_active=True).count()
    total_candidates = Candidate.objects.count()
    deployed_candidates = Candidate.objects.filter(current_stage='DEPLOYED').count()
    
    # Financial Overview (All Companies)
    total_revenue_ytd = Invoice.objects.filter(
        invoice_date__gte=this_year_start,
        status__in=['POSTED', 'SENT', 'PAID']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_ar = Invoice.objects.filter(
        status__in=['POSTED', 'SENT']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_ap = Bill.objects.filter(
        status__in=['POSTED']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Revenue by Country
    revenue_by_country = []
    for company in companies:
        revenue = Invoice.objects.filter(
            company=company,
            invoice_date__gte=this_month_start,
            status__in=['POSTED', 'SENT', 'PAID']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_by_country.append({
            'country': company.get_country_display(),
            'code': company.code,
            'revenue': float(revenue),
            'currency': company.base_currency
        })
    
    # Recent Activities
    recent_invoices = Invoice.objects.select_related('company', 'employer').order_by('-created_at')[:10]
    recent_activities = [{
        'type': 'invoice',
        'id': str(inv.id),
        'description': f"Invoice {inv.invoice_number} created for {inv.employer.name}",
        'company': inv.company.code,
        'amount': float(inv.total_amount),
        'currency': inv.currency,
        'date': inv.created_at.isoformat()
    } for inv in recent_invoices]
    
    return Response({
        'role': 'HQ_ADMIN',
        'summary': {
            'total_companies': total_companies,
            'total_job_orders': total_job_orders,
            'total_candidates': total_candidates,
            'deployed_candidates': deployed_candidates,
            'deployment_rate': f"{(deployed_candidates / total_candidates * 100) if total_candidates > 0 else 0:.1f}%"
        },
        'financial': {
            'revenue_ytd': float(total_revenue_ytd),
            'total_ar': float(total_ar),
            'total_ap': float(total_ap),
            'revenue_by_country': revenue_by_country
        },
        'companies': companies_data,
        'recent_activities': recent_activities
    }, status=status.HTTP_200_OK)


# ============================================================
# COUNTRY MANAGER DASHBOARD
# ============================================================

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def country_manager_dashboard(request):
    """
    Country Manager Dashboard - Company-specific operations
    GET /api/dashboard/country-manager/
    """
    user = request.user
    company = user.company
    
    if not company:
        return Response({
            'error': 'No company assigned to user'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    this_year_start = today.replace(month=1, day=1)
    
    # Company Overview
    branches = Branch.objects.filter(company=company, is_active=True)
    active_job_orders = JobOrder.objects.filter(company=company, is_active=True)
    
    # Candidate Pipeline
    candidates_by_stage = {}
    for stage_code, stage_name in Candidate.STAGE_CHOICES:
        count = Candidate.objects.filter(
            job_order__company=company,
            current_stage=stage_code
        ).count()
        candidates_by_stage[stage_code] = {
            'name': stage_name,
            'count': count
        }
    
    # Financial Performance
    revenue_mtd = Invoice.objects.filter(
        company=company,
        invoice_date__gte=this_month_start,
        status__in=['POSTED', 'SENT', 'PAID']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    revenue_ytd = Invoice.objects.filter(
        company=company,
        invoice_date__gte=this_year_start,
        status__in=['POSTED', 'SENT', 'PAID']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Outstanding AR
    ar_outstanding = Invoice.objects.filter(
        company=company,
        status__in=['POSTED', 'SENT']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Outstanding AP
    ap_outstanding = Bill.objects.filter(
        company=company,
        status='POSTED'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Top Employers
    top_employers = JobOrder.objects.filter(
        company=company,
        is_active=True
    ).values('employer__name', 'employer__id').annotate(
        job_count=Count('id'),
        candidate_count=Count('candidates')
    ).order_by('-candidate_count')[:5]
    
    # Pending Approvals
    pending_invoices = Invoice.objects.filter(
        company=company,
        status='DRAFT'
    ).count()
    
    pending_bills = Bill.objects.filter(
        company=company,
        status='DRAFT'
    ).count()
    
    # Branch Performance
    branch_stats = []
    for branch in branches:
        candidates = Candidate.objects.filter(
            job_order__company=company
        ).count()  # Would filter by branch if we track that
        
        branch_stats.append({
            'id': str(branch.id),
            'name': branch.name,
            'code': branch.code,
            'city': branch.city,
            'is_headquarters': branch.is_headquarters,
            'candidates': candidates
        })
    
    return Response({
        'role': 'COUNTRY_MANAGER',
        'company': {
            'id': str(company.id),
            'name': company.name,
            'code': company.code,
            'country': company.get_country_display()
        },
        'summary': {
            'total_branches': branches.count(),
            'active_job_orders': active_job_orders.count(),
            'total_candidates': sum(stage['count'] for stage in candidates_by_stage.values()),
            'deployed_candidates': candidates_by_stage.get('DEPLOYED', {}).get('count', 0)
        },
        'financial': {
            'revenue_mtd': float(revenue_mtd),
            'revenue_ytd': float(revenue_ytd),
            'ar_outstanding': float(ar_outstanding),
            'ap_outstanding': float(ap_outstanding),
            'currency': company.base_currency
        },
        'candidate_pipeline': candidates_by_stage,
        'top_employers': list(top_employers),
        'pending_approvals': {
            'invoices': pending_invoices,
            'bills': pending_bills
        },
        'branches': branch_stats
    }, status=status.HTTP_200_OK)


# ============================================================
# FINANCE MANAGER DASHBOARD
# ============================================================

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def finance_manager_dashboard(request):
    """
    Finance Manager Dashboard - Financial operations focus
    GET /api/dashboard/finance-manager/
    """
    user = request.user
    company = user.company
    
    if not company:
        return Response({
            'error': 'No company assigned to user'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # AR/AP Summary
    total_ar = Invoice.objects.filter(
        company=company,
        status__in=['POSTED', 'SENT']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    overdue_ar = Invoice.objects.filter(
        company=company,
        status__in=['POSTED', 'SENT'],
        due_date__lt=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_ap = Bill.objects.filter(
        company=company,
        status='POSTED'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    overdue_ap = Bill.objects.filter(
        company=company,
        status='POSTED',
        due_date__lt=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # AR Aging
    ar_aging = {
        'current': 0,
        '1_30_days': 0,
        '31_60_days': 0,
        '61_90_days': 0,
        'over_90_days': 0
    }
    
    outstanding_invoices = Invoice.objects.filter(
        company=company,
        status__in=['POSTED', 'SENT']
    )
    
    for invoice in outstanding_invoices:
        days_overdue = (today - invoice.due_date).days
        amount = float(invoice.total_amount)
        
        if days_overdue <= 0:
            ar_aging['current'] += amount
        elif days_overdue <= 30:
            ar_aging['1_30_days'] += amount
        elif days_overdue <= 60:
            ar_aging['31_60_days'] += amount
        elif days_overdue <= 90:
            ar_aging['61_90_days'] += amount
        else:
            ar_aging['over_90_days'] += amount
    
    # Cash Flow (MTD)
    receipts_mtd = Receipt.objects.filter(
        company=company,
        receipt_date__gte=this_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    payments_mtd = Payment.objects.filter(
        company=company,
        payment_date__gte=this_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Pending Approvals
    invoices_pending_post = Invoice.objects.filter(
        company=company,
        status='DRAFT'
    ).count()
    
    bills_pending_post = Bill.objects.filter(
        company=company,
        status='DRAFT'
    ).count()
    
    payments_pending = Bill.objects.filter(
        company=company,
        status='POSTED',
        due_date__lte=today + timedelta(days=7)
    ).count()
    
    # Recent Transactions
    recent_receipts = Receipt.objects.filter(
        company=company
    ).select_related('employer').order_by('-receipt_date')[:5]
    
    recent_payments = Payment.objects.filter(
        company=company
    ).select_related('vendor').order_by('-payment_date')[:5]
    
    return Response({
        'role': 'FINANCE_MANAGER',
        'company': {
            'name': company.name,
            'currency': company.base_currency
        },
        'ar_summary': {
            'total': float(total_ar),
            'overdue': float(overdue_ar),
            'current': float(total_ar - overdue_ar),
            'aging': ar_aging
        },
        'ap_summary': {
            'total': float(total_ap),
            'overdue': float(overdue_ap),
            'current': float(total_ap - overdue_ap)
        },
        'cash_flow': {
            'receipts_mtd': float(receipts_mtd),
            'payments_mtd': float(payments_mtd),
            'net_cash_flow': float(receipts_mtd - payments_mtd)
        },
        'pending_actions': {
            'invoices_to_post': invoices_pending_post,
            'bills_to_post': bills_pending_post,
            'payments_due_soon': payments_pending
        },
        'recent_receipts': [{
            'id': str(r.id),
            'receipt_number': r.receipt_number,
            'employer': r.employer.name,
            'amount': float(r.amount),
            'date': r.receipt_date.isoformat()
        } for r in recent_receipts],
        'recent_payments': [{
            'id': str(p.id),
            'payment_number': p.payment_number,
            'vendor': p.vendor.name,
            'amount': float(p.amount),
            'date': p.payment_date.isoformat()
        } for p in recent_payments]
    }, status=status.HTTP_200_OK)


# ============================================================
# ACCOUNTANT DASHBOARD
# ============================================================

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def accountant_dashboard(request):
    """
    Accountant Dashboard - Day-to-day operations
    GET /api/dashboard/accountant/
    """
    user = request.user
    company = user.company
    
    if not company:
        return Response({
            'error': 'No company assigned to user'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    today = timezone.now().date()
    
    # Today's Tasks
    invoices_to_send = Invoice.objects.filter(
        company=company,
        status='POSTED',
        invoice_date=today
    ).count()
    
    bills_to_process = Bill.objects.filter(
        company=company,
        status='DRAFT'
    ).count()
    
    payments_due_today = Bill.objects.filter(
        company=company,
        status='POSTED',
        due_date=today
    ).count()
    
    # Recent Work
    my_recent_invoices = Invoice.objects.filter(
        company=company
    ).select_related('employer').order_by('-created_at')[:10]
    
    my_recent_bills = Bill.objects.filter(
        company=company
    ).select_related('vendor').order_by('-created_at')[:10]
    
    # Candidate Costs to Process
    unprocessed_costs = CandidateCost.objects.filter(
        candidate__job_order__company=company,
        bill__isnull=True
    ).count()
    
    # Quick Stats
    draft_invoices = Invoice.objects.filter(company=company, status='DRAFT').count()
    draft_bills = Bill.objects.filter(company=company, status='DRAFT').count()
    
    return Response({
        'role': 'ACCOUNTANT',
        'company': {
            'name': company.name,
            'currency': company.base_currency
        },
        'today_tasks': {
            'invoices_to_send': invoices_to_send,
            'bills_to_process': bills_to_process,
            'payments_due': payments_due_today,
            'unprocessed_costs': unprocessed_costs
        },
        'quick_stats': {
            'draft_invoices': draft_invoices,
            'draft_bills': draft_bills
        },
        'recent_invoices': [{
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'employer': inv.employer.name,
            'amount': float(inv.total_amount),
            'status': inv.status,
            'date': inv.invoice_date.isoformat()
        } for inv in my_recent_invoices],
        'recent_bills': [{
            'id': str(bill.id),
            'bill_number': bill.bill_number,
            'vendor': bill.vendor.name,
            'amount': float(bill.total_amount),
            'status': bill.status,
            'date': bill.bill_date.isoformat()
        } for bill in my_recent_bills]
    }, status=status.HTTP_200_OK)


# ============================================================
# BRANCH USER DASHBOARD
# ============================================================

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def branch_user_dashboard(request):
    """
    Branch User Dashboard - Candidate operations focus
    GET /api/dashboard/branch-user/
    """
    user = request.user
    company = user.company
    branch = user.branch
    
    if not company:
        return Response({
            'error': 'No company assigned to user'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Candidate Pipeline for company
    candidates_by_stage = {}
    total_candidates = 0
    
    for stage_code, stage_name in Candidate.STAGE_CHOICES:
        count = Candidate.objects.filter(
            job_order__company=company,
            current_stage=stage_code
        ).count()
        candidates_by_stage[stage_code] = {
            'name': stage_name,
            'count': count
        }
        total_candidates += count
    
    # Active Job Orders
    active_jobs = JobOrder.objects.filter(
        company=company,
        is_active=True
    ).select_related('employer').order_by('-created_at')
    
    # Recent Candidates
    recent_candidates = Candidate.objects.filter(
        job_order__company=company
    ).select_related('job_order', 'job_order__employer').order_by('-created_at')[:10]
    
    # Candidates needing action
    needs_documentation = Candidate.objects.filter(
        job_order__company=company,
        current_stage='DOCUMENTATION'
    ).count()
    
    needs_visa = Candidate.objects.filter(
        job_order__company=company,
        current_stage='VISA'
    ).count()
    
    needs_medical = Candidate.objects.filter(
        job_order__company=company,
        current_stage='MEDICAL'
    ).count()
    
    return Response({
        'role': 'BRANCH_USER',
        'company': {
            'name': company.name,
            'code': company.code
        },
        'branch': {
            'name': branch.name if branch else 'No branch assigned',
            'code': branch.code if branch else None
        } if branch else None,
        'summary': {
            'total_candidates': total_candidates,
            'active_job_orders': active_jobs.count(),
            'deployed_this_month': Candidate.objects.filter(
                job_order__company=company,
                current_stage='DEPLOYED',
                deployed_date__month=timezone.now().month
            ).count()
        },
        'candidate_pipeline': candidates_by_stage,
        'action_required': {
            'needs_documentation': needs_documentation,
            'needs_visa': needs_visa,
            'needs_medical': needs_medical
        },
        'active_job_orders': [{
            'id': str(job.id),
            'position': job.position_title,
            'employer': job.employer.name,
            'positions': job.num_positions,
            'filled': job.candidates.filter(current_stage='DEPLOYED').count()
        } for job in active_jobs[:10]],
        'recent_candidates': [{
            'id': str(cand.id),
            'name': cand.full_name,
            'passport': cand.passport_number,
            'stage': cand.get_current_stage_display(),
            'job_order': cand.job_order.position_title,
            'employer': cand.job_order.employer.name
        } for cand in recent_candidates]
    }, status=status.HTTP_200_OK)


# ============================================================
# AUDITOR DASHBOARD
# ============================================================

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auditor_dashboard(request):
    """
    Auditor Dashboard - Read-only audit and compliance view
    GET /api/dashboard/auditor/
    """
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # System-wide Statistics
    total_companies = Company.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_active=True).count()
    
    # Transaction Volume
    invoices_mtd = Invoice.objects.filter(
        created_at__gte=this_month_start
    ).count()
    
    bills_mtd = Bill.objects.filter(
        created_at__gte=this_month_start
    ).count()
    
    # Compliance Checks
    unposted_invoices = Invoice.objects.filter(status='DRAFT').count()
    unposted_bills = Bill.objects.filter(status='DRAFT').count()
    
    # Recent Activity Across All Companies
    from authentications.models import LoginHistory
    recent_logins = LoginHistory.objects.filter(
        status='SUCCESS'
    ).order_by('-timestamp')[:20]
    
    # Company-wise Summary
    company_summary = []
    for company in Company.objects.filter(is_active=True):
        company_summary.append({
            'company': company.name,
            'code': company.code,
            'invoices_mtd': Invoice.objects.filter(
                company=company,
                created_at__gte=this_month_start
            ).count(),
            'bills_mtd': Bill.objects.filter(
                company=company,
                created_at__gte=this_month_start
            ).count(),
            'candidates': Candidate.objects.filter(
                job_order__company=company
            ).count()
        })
    
    return Response({
        'role': 'AUDITOR',
        'system_overview': {
            'total_companies': total_companies,
            'total_users': total_users,
            'active_job_orders': JobOrder.objects.filter(is_active=True).count(),
            'total_candidates': Candidate.objects.count()
        },
        'transaction_volume': {
            'invoices_mtd': invoices_mtd,
            'bills_mtd': bills_mtd,
            'receipts_mtd': Receipt.objects.filter(
                receipt_date__gte=this_month_start
            ).count(),
            'payments_mtd': Payment.objects.filter(
                payment_date__gte=this_month_start
            ).count()
        },
        'compliance': {
            'unposted_invoices': unposted_invoices,
            'unposted_bills': unposted_bills
        },
        'company_summary': company_summary,
        'recent_logins': [{
            'email': login.email_attempted,
            'status': login.status,
            'ip_address': login.ip_address,
            'timestamp': login.timestamp.isoformat()
        } for login in recent_logins]
    }, status=status.HTTP_200_OK)
# End of dashboards/views.py