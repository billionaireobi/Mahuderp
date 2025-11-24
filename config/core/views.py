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

from .models import (
    Company, Branch, Employer, Vendor,
    JobOrder, Candidate, CandidateCost,
    Invoice, Bill
)
from .serializers import (
    CompanySerializer, BranchSerializer,
    EmployerSerializer, VendorSerializer,
    JobOrderSerializer, CandidateSerializer, CandidateCostSerializer,
    InvoiceSerializer, BillSerializer
)

# def handler404(request, exception):
#     return render(request, '404.html', status=404)

# def handler500(request):
#     return render(request, '500.html', status=500)
# ============================================================
# COMPANIES
# ============================================================

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


# ============================================================
# CANDIDATES
# ============================================================

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


# ============================================================
# INVOICES
# ============================================================

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


# ============================================================
# DASHBOARD STATS
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics
    GET /api/dashboard/stats/
    """
    user = request.user
    
    if user.role == 'HQ_ADMIN':
        companies = Company.objects.filter(is_active=True).count()
        job_orders = JobOrder.objects.filter(is_active=True).count()
        candidates = Candidate.objects.all().count()
        invoices = Invoice.objects.all().count()
    elif user.company:
        companies = 1
        job_orders = JobOrder.objects.filter(company=user.company, is_active=True).count()
        candidates = Candidate.objects.filter(job_order__company=user.company).count()
        invoices = Invoice.objects.filter(company=user.company).count()
    else:
        companies = job_orders = candidates = invoices = 0
    
    return Response({
        'companies': companies,
        'job_orders': job_orders,
        'candidates': candidates,
        'invoices': invoices
    }, status=status.HTTP_200_OK)
