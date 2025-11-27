"""
Core Views for Mahad Group Accounting Suite
File: core/views.py

API endpoints for core business operations
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
from decimal import Decimal
from .models import *
from .serializers import *
try:
    from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiResponse, OpenApiParameter
except Exception:
    # Fallback no-op definitions if drf-spectacular is not installed (prevents import errors).
    def extend_schema(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    class OpenApiTypes:
        OBJECT = dict
        # common simple fallbacks - adjust if additional types are referenced
        INT = int
        NUMBER = float
        STRING = str

    class OpenApiResponse:
        def __init__(self, *args, **kwargs):
            pass
    # Minimal placeholder so code referencing OpenApiParameter doesn't crash when spectacular missing
    class OpenApiParameter:
        PATH = 'path'
        QUERY = 'query'
        def __init__(self, *args, **kwargs):
            pass

from .utils import *
# def handler404(request, exception):
#     return render(request, '404.html', status=404)

# def handler500(request):
#     return render(request, '500.html', status=500)
# ============================================================
# COMPANIES
# ============================================================

@extend_schema(request=CompanySerializer, responses=CompanySerializer(many=True))
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def company_list(request):
    user = request.user

    # CREATE COMPANY
    if request.method == 'POST':
        if user.role != "HQ_ADMIN":
            return Response({"error": "Only HQ Admin can create companies"}, status=403)

        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Company created successfully",
                "company": serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)

    # LIST COMPANIES
    if user.role == 'HQ_ADMIN':
        companies = Company.objects.filter(is_active=True)
    else:
        companies = Company.objects.filter(id=user.company.id, is_active=True) if user.company else Company.objects.none()

    serializer = CompanySerializer(companies, many=True)
    return Response({"companies": serializer.data, "total": companies.count()}, status=200)




@extend_schema(responses=CompanySerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_detail(request, company_id):
    """
    Get company details
    GET /api/companies/{id}/
    """
    company = get_object_or_404(Company, id=company_id)
    
    # Check permission
    if not request.user.has_company_access(company):
        return Response({
            'error': 'You do not have permission to access this company'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = CompanySerializer(company)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# BRANCHES
# ============================================================

@extend_schema(request=BranchSerializer, responses=BranchSerializer(many=True))
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def branch_list(request):
    """
    List branches or create a branch
    GET/POST /api/core/branches/
    """
    user = request.user

    # CREATE BRANCH
    if request.method == 'POST':
        if user.role not in ['HQ_ADMIN', 'COMPANY_ADMIN']:
            return Response({"error": "You do not have permission to create branches"}, status=403)
        
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Branch created successfully",
                "branch": serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)

    # LIST BRANCHES
    company_id = request.query_params.get('company_id')
    if company_id:
        branches = Branch.objects.filter(company_id=company_id, is_active=True)
    elif user.role == 'HQ_ADMIN':
        branches = Branch.objects.filter(is_active=True)
    elif user.company:
        branches = Branch.objects.filter(company=user.company, is_active=True)
    else:
        branches = Branch.objects.none()

    serializer = BranchSerializer(branches, many=True)
    return Response({
        'branches': serializer.data,
        'total': branches.count()
    }, status=200)

@extend_schema(request=BranchSerializer, responses=BranchSerializer)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def branch_detail(request, branch_id):
    """
    Get, update, or soft delete a branch
    GET/PUT/PATCH/DELETE /api/core/branches/<branch_id>/
    """
    branch = get_object_or_404(Branch, id=branch_id)

    # Check permission
    if request.user.role not in ['HQ_ADMIN', 'COMPANY_ADMIN']:
        return Response({"error": "You do not have permission"}, status=403)

    # GET branch
    if request.method == 'GET':
        serializer = BranchSerializer(branch)
        return Response(serializer.data, status=200)

    # UPDATE branch
    if request.method in ['PUT', 'PATCH']:
        serializer = BranchSerializer(branch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Branch updated successfully",
                "branch": serializer.data
            }, status=200)
        return Response(serializer.errors, status=400)

    # SOFT DELETE branch
    if request.method == 'DELETE':
        branch.is_active = False
        branch.save()
        return Response({"message": "Branch soft deleted"}, status=200)

# ============================================================
# EMPLOYERS (Clients)
# ============================================================

@extend_schema(request=EmployerSerializer, responses=EmployerSerializer(many=True))
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def employer_list(request):
    """
    List or create employers
    GET/POST /api/employers/
    """
    if request.method == 'GET':
        employers = Employer.objects.all().order_by('name')
        search = request.query_params.get('search')
        
        if search:
            employers = employers.filter(name__icontains=search)
        
        serializer = EmployerSerializer(employers, many=True)
        return Response({
            'employers': serializer.data,
            'total': employers.count()
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = EmployerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Employer created successfully',
                'employer': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=EmployerSerializer, responses=EmployerSerializer)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def employer_detail(request, employer_id):
    """
    Get, update, or delete an employer
    GET/PUT/PATCH/DELETE /api/employers/{id}/
    """
    employer = get_object_or_404(Employer, id=employer_id)

    if request.method == 'GET':
        serializer = EmployerSerializer(employer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = EmployerSerializer(employer, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Employer updated successfully',
                'employer': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Soft delete
        employer.is_active = False
        employer.save()
        return Response({
            'message': 'Employer deleted successfully (soft delete)'
        }, status=status.HTTP_200_OK)



# ============================================================
# VENDORS
# ============================================================

@extend_schema(request=VendorSerializer, responses=VendorSerializer(many=True))
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def vendor_list(request):
    """
    List or create vendors
    GET/POST /api/vendors/
    """
    if request.method == 'GET':
        vendors = Vendor.objects.all().order_by('name')
        vendor_type = request.query_params.get('type')
        
        if vendor_type:
            vendors = vendors.filter(type=vendor_type)
        
        serializer = VendorSerializer(vendors, many=True)
        return Response({
            'vendors': serializer.data,
            'total': vendors.count()
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Vendor created successfully',
                'vendor': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(request=VendorSerializer, responses=VendorSerializer)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def vendor_detail(request, vendor_id):
    """
    Get, update, or delete a vendor
    GET/PUT/PATCH/DELETE /api/vendors/{id}/
    """
    vendor = get_object_or_404(Vendor, id=vendor_id)

    if request.method == 'GET':
        serializer = VendorSerializer(vendor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = VendorSerializer(vendor, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Vendor updated successfully',
                'vendor': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Soft delete
        vendor.is_active = False
        vendor.save()
        return Response({
            'message': 'Vendor deleted successfully (soft delete)'
        }, status=status.HTTP_200_OK)

# ============================================================
# JOB ORDERS
# ============================================================

@extend_schema(request=JobOrderSerializer, responses=JobOrderSerializer(many=True))
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def job_order_list(request):
    """
    List or create job orders
    GET/POST /api/job-orders/
    """
    if request.method == 'GET':
        user = request.user
        
        if user.role == 'HQ_ADMIN':
            job_orders = JobOrder.objects.all()
        elif user.company:
            job_orders = JobOrder.objects.filter(company=user.company)
        else:
            job_orders = JobOrder.objects.none()
        
        job_orders = job_orders.select_related('company', 'employer').order_by('-created_at')
        
        serializer = JobOrderSerializer(job_orders, many=True)
        return Response({
            'job_orders': serializer.data,
            'total': job_orders.count()
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = JobOrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Job order created successfully',
                'job_order': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses=JobOrderSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_order_detail(request, job_order_id):
    """
    Get job order details with candidates
    GET /api/job-orders/{id}/
    """
    job_order = get_object_or_404(JobOrder, id=job_order_id)
    
    # Check permission
    if not request.user.has_company_access(job_order.company):
        return Response({
            'error': 'You do not have permission to access this job order'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = JobOrderSerializer(job_order)
    candidates = Candidate.objects.filter(job_order=job_order)
    candidate_serializer = CandidateSerializer(candidates, many=True)
    
    return Response({
        'job_order': serializer.data,
        'candidates': candidate_serializer.data,
        'total_candidates': candidates.count()
    }, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='job_order_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='Job order id (UUID)',
            required=True
        )
    ],
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_order_summary(request, job_order_id):
    """
    Financial summary for a job order
    GET /api/job-orders/{id}/summary/
    """
    job_order = get_object_or_404(JobOrder, id=job_order_id)
    
    if not request.user.has_company_access(job_order.company):
        return Response({"error": "Access denied"}, status=403)

    candidates = job_order.candidates.all()
    deployed = candidates.filter(current_stage='DEPLOYED').count()
    total_costs = CandidateCost.objects.filter(candidate__job_order=job_order).aggregate(t=Sum('amount'))['t'] or 0
    revenue = deployed * job_order.agreed_fee
    profit = revenue - total_costs

    return Response({
        "job_order": job_order.position_title,
        "employer": job_order.employer.name,
        "total_candidates": candidates.count(),
        "deployed": deployed,
        "in_progress": candidates.count() - deployed,
        "agreed_fee_per_candidate": float(job_order.agreed_fee),
        "potential_revenue": float(revenue),
        "total_costs": float(total_costs),
        "estimated_profit": float(profit),
        "profit_margin_%": round((profit / revenue * 100), 2) if revenue > 0 else 0
    })

# ============================================================
# CANDIDATES
# ============================================================

@extend_schema(request=CandidateSerializer, responses=CandidateSerializer(many=True))
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def candidate_list(request):
    """
    List or create candidates
    GET/POST /api/candidates/
    """
    if request.method == 'GET':
        user = request.user
        job_order_id = request.query_params.get('job_order')
        
        if user.role == 'HQ_ADMIN':
            candidates = Candidate.objects.all()
        elif user.company:
            candidates = Candidate.objects.filter(job_order__company=user.company)
        else:
            candidates = Candidate.objects.none()
        
        if job_order_id:
            candidates = candidates.filter(job_order_id=job_order_id)
        
        candidates = candidates.select_related('job_order', 'job_order__employer').order_by('-created_at')
        
        serializer = CandidateSerializer(candidates, many=True)
        return Response({
            'candidates': serializer.data,
            'total': candidates.count()
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = CandidateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Candidate created successfully',
                'candidate': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=CandidateSerializer, responses=CandidateSerializer)
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def candidate_detail(request, candidate_id):
    """
    Get or update candidate details
    GET/PUT /api/candidates/{id}/
    """
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'GET':
        serializer = CandidateSerializer(candidate)
        costs = CandidateCost.objects.filter(candidate=candidate)
        cost_serializer = CandidateCostSerializer(costs, many=True)
        
        return Response({
            'candidate': serializer.data,
            'costs': cost_serializer.data,
            'total_costs': sum(cost.amount for cost in costs)
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = CandidateSerializer(candidate, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Candidate updated successfully',
                'candidate': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=CandidateCostSerializer, responses=CandidateCostSerializer, operation_id='core_candidate_add_cost_create')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def candidate_add_cost(request, candidate_id):
    """
    Add cost to candidate
    POST /api/candidates/{id}/add-cost/
    """
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    data = request.data.copy()
    data['candidate'] = str(candidate.id)
    
    serializer = CandidateCostSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Cost added successfully',
            'cost': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'error': 'Validation failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=None, responses=CandidateSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def candidate_move_stage(request, candidate_id):
    """
    Move candidate to next stage (especially DEPLOYED → triggers revenue)
    POST /api/candidates/{id}/move_stage/
    Body: { "stage": "DEPLOYED" }
    → Auto-posts journal: DR COGS / CR WIP
    """
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if not request.user.has_company_access(candidate.job_order.company):
        return Response({"error": "Access denied"}, status=403)

    new_stage = request.data.get('stage')
    if new_stage not in dict(Candidate.STAGE_CHOICES):
        return Response({"error": "Invalid stage"}, status=400)

    old_stage = candidate.current_stage
    candidate.current_stage = new_stage
    if new_stage == 'DEPLOYED' and not candidate.deployed_date:
        candidate.deployed_date = timezone.now().date()
    candidate.save()

    # AUTO JOURNAL ON DEPLOYMENT
    if new_stage == 'DEPLOYED' and old_stage != 'DEPLOYED':
        from .utils import post_deployment_journal
        post_deployment_journal(candidate)

    return Response({
        "message": "Stage updated successfully",
        "candidate": CandidateSerializer(candidate).data,
        "auto_journal_posted": new_stage == 'DEPLOYED'
    }, status=200)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_profitability(request, candidate_id):
    """
    Get per-candidate profitability
    GET /api/candidates/{id}/profitability/
    """
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if not request.user.has_company_access(candidate.job_order.company):
        return Response({"error": "Access denied"}, status=403)

    total_costs = candidate.costs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    revenue = candidate.job_order.agreed_fee if candidate.current_stage == 'DEPLOYED' else Decimal('0.00')
    profit = revenue - total_costs
    margin = (profit / revenue * 100) if revenue > 0 else 0

    return Response({
        "candidate": candidate.full_name,
        "passport": candidate.passport_number,
        "job_order": candidate.job_order.position_title,
        "revenue": float(revenue),
        "total_costs": float(total_costs),
        "gross_profit": float(profit),
        "margin_percent": round(float(margin), 2),
        "status": candidate.get_current_stage_display()
    })

# ============================================================
# INVOICES
# ============================================================

@extend_schema(responses=InvoiceSerializer(many=True))
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_list(request):
    """
    List invoices
    GET /api/invoices/
    """
    user = request.user
    
    if user.role == 'HQ_ADMIN':
        invoices = Invoice.objects.all()
    elif user.company:
        invoices = Invoice.objects.filter(company=user.company)
    else:
        invoices = Invoice.objects.none()
    
    # Filters
    status_filter = request.query_params.get('status')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    invoices = invoices.select_related('company', 'employer').order_by('-invoice_date')
    
    serializer = InvoiceSerializer(invoices, many=True)
    return Response({
        'invoices': serializer.data,
        'total': invoices.count()
    }, status=status.HTTP_200_OK)


@extend_schema(responses=InvoiceSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_detail(request, invoice_id):
    """
    Get invoice details
    GET /api/invoices/{id}/
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Check permission
    if not request.user.has_company_access(invoice.company):
        return Response({
            'error': 'You do not have permission to access this invoice'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = InvoiceSerializer(invoice)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(request=InvoiceGenerateSerializer, responses=InvoiceSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def invoice_generate(request):
    """
    Generate invoice from deployed candidates
    POST /api/invoices/generate/
    Body: {
        "job_order_id": 1,
        "candidate_ids": [1, 2, 3],
        "invoice_date": "2025-01-18"
    }
    """
    job_order_id = request.data.get('job_order_id')
    candidate_ids = request.data.get('candidate_ids', [])
    invoice_date = request.data.get('invoice_date')

    if not all([job_order_id, candidate_ids, invoice_date]):
        return Response({"error": "job_order_id, candidate_ids, invoice_date required"}, status=400)

    job_order = get_object_or_404(JobOrder, id=job_order_id)
    candidates = Candidate.objects.filter(id__in=candidate_ids, job_order=job_order, current_stage='DEPLOYED')

    if not candidates.exists():
        return Response({"error": "No deployed candidates found"}, status=400)

    if not request.user.has_company_access(job_order.company):
        return Response({"error": "Access denied"}, status=403)

    invoice = Invoice.objects.create(
        company=job_order.company,
        employer=job_order.employer,
        job_order=job_order,
        invoice_date=invoice_date,
        due_date=invoice_date + timedelta(days=30),
        currency=job_order.currency,
        status='DRAFT'
    )

    # Service Fee
    InvoiceLine.objects.create(
        invoice=invoice,
        description=f"Placement Fee - {candidates.count()} candidate(s)",
        quantity=candidates.count(),
        unit_price=job_order.agreed_fee,
        amount=candidates.count() * job_order.agreed_fee
    )

    # Reimbursable Costs
    total_reimb = 0
    for candidate in candidates:
        for cost in candidate.costs.filter(reimbursable=True):
            InvoiceLine.objects.create(
                invoice=invoice,
                description=f"{cost.get_cost_type_display()} - {candidate.full_name}",
                quantity=1,
                unit_price=cost.amount,
                amount=cost.amount,
                candidate=candidate
            )
            total_reimb += cost.amount

    invoice.total_amount = invoice.lines.aggregate(t=Sum('amount'))['t'] or 0
    invoice.net_amount = invoice.total_amount
    invoice.save()

    # AUTO JOURNAL
    from .utils import post_invoice_journal
    post_invoice_journal(invoice)

    return Response({
        "message": "Invoice generated successfully",
        "invoice": InvoiceSerializer(invoice).data,
        "service_fee": float(candidates.count() * job_order.agreed_fee),
        "reimbursable_costs": float(total_reimb),
        "total": float(invoice.total_amount)
    }, status=201)


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invoice_post(request, invoice_id):
    """
    Post invoice to General Ledger
    POST /api/invoices/{id}/post/
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if not request.user.has_company_access(invoice.company):
        return Response({"error": "Access denied"}, status=403)

    if invoice.status != 'DRAFT':
        return Response({"error": "Only draft invoices can be posted"}, status=400)

    invoice.status = 'POSTED'
    invoice.posted_at = timezone.now()
    invoice.save()

    return Response({"message": "Invoice posted to GL", "invoice": InvoiceSerializer(invoice).data})


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invoice_send(request, invoice_id):
    """
    Send invoice via email (PDF + Stripe/PayPal links)
    POST /api/invoices/{id}/send/
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if not request.user.has_company_access(invoice.company):
        return Response({"error": "Access denied"}, status=403)

    invoice.status = 'SENT'
    invoice.save()

    from .tasks import generate_and_send_invoice_pdf
    generate_and_send_invoice_pdf.delay(invoice.id)

    return Response({
        "message": "Invoice email queued",
        "invoice_number": invoice.invoice_number,
        "sent_to": invoice.employer.email
    })
# ============================================================
# DASHBOARD STATS
# ============================================================

# @extend_schema(responses=OpenApiTypes.OBJECT)
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def dashboard_stats(request):
#     """
#     Get dashboard statistics
#     GET /api/dashboard/stats/
#     """
#     user = request.user
    
#     if user.role == 'HQ_ADMIN':
#         companies = Company.objects.filter(is_active=True).count()
#         job_orders = JobOrder.objects.filter(is_active=True).count()
#         candidates = Candidate.objects.all().count()
#         invoices = Invoice.objects.all().count()
#     elif user.company:
#         companies = 1
#         job_orders = JobOrder.objects.filter(company=user.company, is_active=True).count()
#         candidates = Candidate.objects.filter(job_order__company=user.company).count()
#         invoices = Invoice.objects.filter(company=user.company).count()
#     else:
#         companies = job_orders = candidates = invoices = 0
    
#     return Response({
#         'companies': companies,
#         'job_orders': job_orders,
#         'candidates': candidates,
#         'invoices': invoices
#     }, status=status.HTTP_200_OK)
# reports/views.py → REPLACE your old dashboard_stats with THIS NUCLEAR VERSION
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db.models import Sum, Count, Avg, Q, F, FloatField, ExpressionWrapper
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from django.db.models.functions import Coalesce
from django.db.models import DecimalField, Value

@extend_schema(
    description="MAHAD GROUP GLOBAL DASHBOARD — Real-time financial & operational intelligence across 5 countries",
    responses=OpenApiResponse(response=dict, description="Complete empire overview")
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    today = timezone.now().date()
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)

    # Base filters
    if user.role == 'HQ_ADMIN':
        company_filter = Q()
        job_filter = Q(is_active=True)
        candidate_filter = Q()
    elif user.company:
        company_filter = Q(company=user.company)
        job_filter = Q(company=user.company, is_active=True)
        candidate_filter = Q(job_order__company=user.company)
    else:
        return Response({"error": "No company access"}, status=403)

    # =============================================================================
    # 1. CORE BUSINESS METRICS
    # =============================================================================
    total_candidates = Candidate.objects.filter(candidate_filter).count()
    deployed_this_month = Candidate.objects.filter(
        candidate_filter,
        current_stage='DEPLOYED',
        deployed_date__gte=this_month
    ).count()

    active_job_orders = JobOrder.objects.filter(job_filter).count()
    # Employer model is not directly linked to Company via a `company` FK in this schema.
    # Count differently depending on user role: HQ admins see all employers;
    # company users see employers that have job orders for their company.
    if user.role == 'HQ_ADMIN':
        total_employers = Employer.objects.count()
    else:
        total_employers = Employer.objects.filter(job_orders__company=user.company).distinct().count()

    # =============================================================================
    # 2. FINANCIAL POWER METRICS
    # =============================================================================
    revenue_this_month = Decimal('0')
    costs_this_month = Decimal('0')
    profit_this_month = Decimal('0')
    ar_outstanding = Decimal('0')
    wip_total = Decimal('0')

    companies = Company.objects.filter(is_active=True) if user.role == 'HQ_ADMIN' else [user.company]

    for company in companies:
        base = company.base_currency

        # ---------- Revenue ----------
        rev = InvoiceLine.objects.filter(
            invoice__company=company,
            invoice__status__in=['POSTED', 'PAID'],
            invoice__invoice_date__gte=this_month
        ).aggregate(
            total=Coalesce(
                Sum('amount'),
                Value(0),
                output_field=DecimalField()
            )
        )['total'] or Decimal('0')

        revenue_this_month += convert_currency(rev, company.base_currency, 'USD', today) or rev

        # ---------- Costs ----------
        cost = CandidateCost.objects.filter(
            candidate__job_order__company=company,
            candidate__current_stage='DEPLOYED',
            date__gte=this_month
        ).aggregate(
            total=Coalesce(
                Sum('amount'),
                Value(0),
                output_field=DecimalField()
            )
        )['total'] or Decimal('0')

        costs_this_month += convert_currency(cost, company.base_currency, 'USD', today) or cost

        # ---------- Accounts Receivable ----------
        for inv in Invoice.objects.filter(company=company, status__in=['POSTED', 'SENT']):
            due = inv.total_amount - inv.amount_paid
            if due > 0:
                ar_outstanding += convert_currency(
                    due, inv.currency, base, inv.due_date or today
                )

        # ---------- WIP ----------
        wip = CandidateCost.objects.filter(
            candidate__job_order__company=company,
            candidate__current_stage__in=[
                'SOURCING', 'SCREENING', 'DOCUMENTATION',
                'VISA', 'MEDICAL', 'TICKET'
            ]
        ).aggregate(
            total=Coalesce(
                Sum('amount'),
                Value(0),
                output_field=DecimalField()
            )
        )['total'] or Decimal('0')

        wip_total += convert_currency(wip, company.base_currency, base, today)

    profit_this_month = revenue_this_month - costs_this_month
    gross_margin = (
        profit_this_month / revenue_this_month * 100
        if revenue_this_month else Decimal('0')
    )

    # =============================================================================
    # 3. MARGIN LEADERS
    # =============================================================================
    top_margin_candidates = list(
        Candidate.objects.filter(candidate_filter, current_stage='DEPLOYED')
        .annotate(
            revenue=Coalesce(
                Sum(
                    'invoiceline__amount',
                    filter=Q(invoiceline__invoice__status__in=['POSTED', 'PAID'])
                ),
                Value(0),
                output_field=DecimalField()
            ),
            cost=Coalesce(
                Sum('costs__amount'),
                Value(0),
                output_field=DecimalField()
            ),
            margin=ExpressionWrapper(
                (F('revenue') - F('cost')) * 100.0 / F('revenue'),
                output_field=FloatField()
            )
        )
        .filter(revenue__gt=0)
        .order_by('-margin')[:5]
        .values('full_name', 'passport_number', 'margin', 'revenue', 'cost')
    )

    # Stage distribution
    stage_breakdown = dict(
        Candidate.objects.filter(candidate_filter)
        .values('current_stage')
        .annotate(count=Count('id'))
        .values_list('current_stage', 'count')
    )

    # =============================================================================
    # 4. CASHFLOW & RISK
    # =============================================================================
    overdue_invoices = Invoice.objects.filter(
        company_filter,
        status__in=['POSTED', 'SENT'],
        due_date__lt=today,
        total_amount__gt=F('amount_paid')
    ).count()

    expected_inflow_30days = Decimal('0')

    for inv in Invoice.objects.filter(
        company_filter,
        status__in=['POSTED', 'SENT'],
        due_date__lte=today + timedelta(days=30)
    ):
        due = inv.total_amount - inv.amount_paid
        if due > 0:
            expected_inflow_30days += convert_currency(
                due, inv.currency, inv.company.base_currency, inv.due_date
            )

    # =============================================================================
    # FINAL RESPONSE
    # =============================================================================
    return Response({
        "generated_at": timezone.now().isoformat(),
        "user_role": user.role,
        "dashboard": "Mahad Group Global Intelligence Center",

        "core_metrics": {
            "total_candidates_all_time": total_candidates,
            "deployed_this_month": deployed_this_month,
            "deployment_rate_this_month": round(deployed_this_month / max(total_candidates, 1) * 100, 1),
            "active_job_orders": active_job_orders,
            "total_clients": total_employers,
        },

        "financial_overview_usd": {
            "revenue_this_month": round(float(revenue_this_month), 2),
            "cogs_this_month": round(float(costs_this_month), 2),
            "gross_profit_this_month": round(float(profit_this_month), 2),
            "gross_margin_percent": round(float(gross_margin), 2),
            "ar_outstanding": round(float(ar_outstanding), 2),
            "wip_invested": round(float(wip_total), 2),
            "net_cash_position": round(float(ar_outstanding - wip_total), 2),
        },

        "top_performers": [
            {
                "rank": i+1,
                "candidate": c['full_name'],
                "passport": c['passport_number'],
                "margin_percent": round(c['margin'], 2),
                "profit_usd": round(float(c['revenue'] - c['cost']), 2)
            }
            for i, c in enumerate(top_margin_candidates)
        ],

        "pipeline_stages": {
            stage: stage_breakdown.get(stage, 0) for stage in [
                "SOURCING", "SCREENING", "DOCUMENTATION",
                "VISA", "MEDICAL", "TICKET", "DEPLOYED"
            ]
        },

        "risk_alerts": {
            "overdue_invoices": overdue_invoices,
            "expected_inflow_next_30_days": round(float(expected_inflow_30days), 2),
            "high_risk_over_90_days": Invoice.objects.filter(
                company_filter,
                status__in=['POSTED', 'SENT'],
                due_date__lt=today - timedelta(days=90),
                total_amount__gt=F('amount_paid')
            ).count()
        },

        "quick_actions": {
            "view_margin_leaderboard": "/api/reports/margin-leaderboard/",
            "view_profit_loss": "/api/reports/profit-loss/",
            "view_ar_aging": "/api/reports/ar-aging/",
            "generate_invoice": "/api/invoices/generate/",
        }
    }, status=200)

# ============================================================
# BILLS, RECEIPTS, PAYMENTS
# ============================================================

@extend_schema(request=BillSerializer, responses=BillSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bill_post(request, bill_id):
    """Post vendor bill to GL"""
    bill = get_object_or_404(Bill, id=bill_id)
    if bill.status != 'DRAFT':
        return Response({"error": "Only draft bills can be posted"}, status=400)

    bill.status = 'POSTED'
    bill.posted_at = timezone.now()
    bill.save()

    return Response({"message": "Bill posted to GL"})


@extend_schema(request=ReceiptSerializer, responses=ReceiptSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def receipt_create(request):
    """Record customer payment"""
    serializer = ReceiptSerializer(data=request.data)
    if serializer.is_valid():
        receipt = serializer.save()
        # Auto-post journal
        from .utils import post_receipt_journal
        post_receipt_journal(receipt)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@extend_schema(request=PaymentSerializer, responses=PaymentSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_create(request):
    """Record vendor payment"""
    serializer = PaymentSerializer(data=request.data)
    if serializer.is_valid():
        payment = serializer.save()
        # Auto-post journal
        from .utils import post_payment_journal
        post_payment_journal(payment)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


# BULK CANDIDATE OPERATIONS

@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def candidate_bulk_move_stage(request):
    """Move multiple candidates to DEPLOYED (triggers revenue)"""
    candidate_ids = request.data.get('candidate_ids', [])
    stage = request.data.get('stage', 'DEPLOYED')
    
    result = bulk_move_stage(candidate_ids, stage, request.user)
    return Response({
        "message": f"{result['updated']} candidates moved to {stage}",
        "details": result
    })


@extend_schema(request=CandidateCostSerializer, responses=OpenApiTypes.OBJECT, operation_id='core_candidate_bulk_add_cost_create')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def candidate_bulk_add_cost(request):
    """Add same cost (e.g., visa fee) to multiple candidates"""
    candidate_ids = request.data.get('candidate_ids', [])
    cost_data = {
        "cost_type": request.data.get('cost_type'),
        "amount": request.data.get('amount'),
        "currency": request.data.get('currency'),
        "vendor_id": request.data.get('vendor'),
        "description": request.data.get('description'),
        "date_incurred": request.data.get('date_incurred'),
        "reimbursable": request.data.get('reimbursable', False)
    }
    
    result = bulk_add_cost(candidate_ids, cost_data, request.user)
    return Response({
        "message": f"Cost added to {result['created']} candidates",
        "details": result
    })
