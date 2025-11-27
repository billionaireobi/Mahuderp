# reports/views.py
# MAHAD GROUP ACCOUNTING SUITE — COMPLETE FINANCIAL & RECRUITMENT REPORTS
# Multi-Company | Multi-Currency | Double-Entry | Candidate Profitability | 5 Countries
# © 2025 Mahad Group — Built for Global Recruitment Domination

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.db.models import Sum, Q, F, DecimalField
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from core.models import (
    Company, JobOrder, Candidate, CandidateCost,
    Invoice, InvoiceLine, Bill, Employer, FxRate
)
from .models import CandidateReport, JobOrderReport


# =============================================
# FX CONVERSION ENGINE — THE HEART OF MULTI-CURRENCY
# =============================================
def convert_currency(amount: Decimal, from_currency: str, to_currency: str, date=None) -> Decimal:
    if not amount or amount == 0 or from_currency == to_currency:
        return round(amount or Decimal('0'), 2)

    if not date:
        date = timezone.now().date()

    try:
        rate = FxRate.objects.filter(
            from_currency=from_currency,
            to_currency=to_currency,
            rate_date__lte=date
        ).order_by('-rate_date').first()

        if rate:
            return round(amount * rate.rate, 2)

        reverse = FxRate.objects.filter(
            from_currency=to_currency,
            to_currency=from_currency,
            rate_date__lte=date
        ).order_by('-rate_date').first()
        if reverse:
            return round(amount / reverse.rate, 2)
    except:
        pass
    return round(amount, 2)



# =============================================
# 1. PROFIT & LOSS STATEMENT (FULLY MULTI-CURRENCY)
# =============================================
@extend_schema(
    parameters=[
        OpenApiParameter('company_id', OpenApiTypes.UUID, description='Company ID', required=True),
        OpenApiParameter('from_date', OpenApiTypes.DATE, description='Start date (YYYY-MM-DD)', required=False),
        OpenApiParameter('to_date', OpenApiTypes.DATE, description='End date (YYYY-MM-DD)', required=False),
        OpenApiParameter('job_order_id', OpenApiTypes.STR, description='Job order id (optional)', required=False),
        OpenApiParameter('candidate_id', OpenApiTypes.STR, description='Candidate id (optional)', required=False),
        OpenApiParameter('detail', OpenApiTypes.STR, description='Detail level: summary|job|candidate', required=False),
    ],
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profit_loss_report(request):
    company_id = request.query_params.get('company_id')
    from_date = request.query_params.get('from_date')
    to_date = request.query_params.get('to_date', timezone.now().date())
    job_order_id = request.query_params.get('job_order_id')
    candidate_id = request.query_params.get('candidate_id')
    detail = request.query_params.get('detail', 'summary')  # summary, job, candidate

    if not company_id:
        return Response({"error": "company_id required"}, status=400)

    company = Company.objects.get(id=company_id)
    base = company.base_currency

    inv_filter = Q(invoice__company_id=company_id, invoice__status__in=['POSTED', 'PAID'])
    cost_filter = Q(candidate__job_order__company_id=company_id)

    if from_date:
        inv_filter &= Q(invoice__invoice_date__gte=from_date)
        cost_filter &= Q(date__gte=from_date)
    if to_date:
        inv_filter &= Q(invoice__invoice_date__lte=to_date)
        cost_filter &= Q(date__lte=to_date)
    if job_order_id:
        inv_filter &= Q(candidate__job_order_id=job_order_id)
        cost_filter &= Q(candidate__job_order_id=job_order_id)
    if candidate_id:
        inv_filter &= Q(candidate_id=candidate_id)
        cost_filter &= Q(candidate_id=candidate_id)

    revenue_lines = []
    cogs_lines = []
    revenue_total = cost_total = Decimal('0')

    # REVENUE
    for line in InvoiceLine.objects.filter(inv_filter).select_related('candidate', 'invoice'):
        conv = convert_currency(line.amount, line.invoice.currency, base, line.invoice.invoice_date)
        revenue_total += conv
        if detail in ['job', 'candidate']:
            revenue_lines.append({
                "candidate": line.candidate.full_name if line.candidate else "Direct Fee",
                "passport": line.candidate.passport_number if line.candidate else None,
                "job_order": str(line.candidate.job_order) if line.candidate else "N/A",
                "invoice": line.invoice.invoice_number,
                "description": line.description,
                "original": f"{line.amount:.2f} {line.invoice.currency}",
                "converted": f"{conv:.2f} {base}",
                "date": line.invoice.invoice_date.isoformat(),
                "employer": line.invoice.employer.name
            })

    # COSTS
    for cost in CandidateCost.objects.filter(cost_filter).select_related('candidate'):
        conv = convert_currency(cost.amount, cost.currency, base, cost.date)
        cost_total += conv
        if detail in ['job', 'candidate']:
            cogs_lines.append({
                "candidate": cost.candidate.full_name,
                "passport": cost.candidate.passport_number,
                "type": cost.get_cost_type_display(),
                "reimbursable": cost.reimbursable,
                "vendor": cost.vendor.name if cost.vendor else "Internal",
                "original": f"{cost.amount:.2f} {cost.currency}",
                "converted": f"{conv:.2f} {base}",
                "date": cost.date.isoformat(),
                "stage_when_incurred": cost.candidate.current_stage
            })

    gross_profit = revenue_total - cost_total
    gross_margin = (gross_profit / revenue_total * 100) if revenue_total else Decimal('0')

    response = {
        "report": "Profit & Loss Statement",
        "company": company.name,
        "base_currency": base,
        "period": f"{from_date or 'All Time'} → {to_date}",
        "filters": {"job_order": job_order_id, "candidate": candidate_id, "detail_level": detail},
        "summary": {
            "total_revenue": float(revenue_total),
            "total_cogs": float(cost_total),
            "gross_profit": float(gross_profit),
            "gross_margin_percent": round(float(gross_margin), 2),
        },
        "breakdown": {
            "revenue_lines": revenue_lines[:500],
            "cost_lines": cogs_lines[:500],
        },
        "generated_at": timezone.now().isoformat(),
        "total_candidates": Candidate.objects.filter(cost_filter).distinct().count()
    }

    if detail == 'candidate':
        response["top_performers"] = list(Candidate.objects.filter(cost_filter)
            .annotate(
                    revenue=Coalesce(Sum('invoiceline__amount', filter=Q(invoiceline__invoice__status__in=['POSTED','PAID'])), Value(Decimal('0')), output_field=DecimalField()),
                    cost=Coalesce(Sum('costs__amount'), Value(Decimal('0')), output_field=DecimalField()),
                profit=ExpressionWrapper(F('revenue') - F('cost'), output_field=DecimalField())
            )
            .filter(revenue__gt=0)
            .order_by('-profit')[:10]
            .values('full_name', 'passport_number', 'revenue', 'cost', 'profit')
        )

    return Response(response)



# =============================================
# 2. BALANCE SHEET (MULTI-CURRENCY)
# =============================================
@extend_schema(
    parameters=[
        OpenApiParameter('company_id', OpenApiTypes.UUID, description='Company ID', required=True),
        OpenApiParameter('as_of_date', OpenApiTypes.DATE, description='As of date (YYYY-MM-DD)', required=False),
    ],
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def balance_sheet_report(request):
    company_id = request.query_params.get('company_id')
    as_of_date = request.query_params.get('as_of_date', timezone.now().date())
    if not company_id:
        return Response({"error": "company_id required"}, status=400)

    company = Company.objects.get(id=company_id)
    base = company.base_currency

    ar = Decimal('0.00')
    for inv in Invoice.objects.filter(company_id=company_id, status__in=['POSTED','SENT'], invoice_date__lte=as_of_date):
        due = inv.total_amount - inv.amount_paid
        if due > 0:
            ar += convert_currency(due, inv.currency, base, inv.invoice_date)

    wip = Decimal('0.00')
    for cost in CandidateCost.objects.filter(
        candidate__job_order__company_id=company_id,
        candidate__current_stage__in=['SOURCING','SCREENING','DOCUMENTATION','VISA','MEDICAL','TICKET'],
        date__lte=as_of_date
    ):
        wip += convert_currency(cost.amount, cost.currency, base, cost.date)

    ap = Decimal('0.00')
    for bill in Bill.objects.filter(company_id=company_id, status='POSTED', bill_date__lte=as_of_date):
        due = bill.total_amount - bill.amount_paid
        if due > 0:
            ap += convert_currency(due, bill.currency, base, bill.bill_date)

    total_assets = ar + wip
    equity = total_assets - ap

    return Response({
        "company": company.name,
        "as_of_date": str(as_of_date),
        "currency": base,
        "assets": {
            "accounts_receivable": float(ar),
            "work_in_progress": float(wip),
            "total_assets": float(total_assets)
        },
        "liabilities": {"accounts_payable": float(ap)},
        "equity": float(equity),
        "generated_at": timezone.now().isoformat()
    })


# =============================================
# 3. AR AGING REPORT (MULTI-CURRENCY)
# =============================================
@extend_schema(
    parameters=[
        OpenApiParameter('company_id', OpenApiTypes.UUID, description='Company ID', required=True),
    ]
    ,
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ar_aging_report(request):
    company_id = request.query_params.get('company_id')
    if not company_id:
        return Response({"error": "company_id required"}, status=400)

    company = Company.objects.get(id=company_id)
    base = company.base_currency
    today = timezone.now().date()

    buckets = {"current": 0, "1-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
    details = []

    for inv in Invoice.objects.filter(
        company_id=company_id,
        status__in=['POSTED', 'SENT'],
        total_amount__gt=F('amount_paid')
    ):
        outstanding = inv.total_amount - inv.amount_paid
        conv = convert_currency(outstanding, inv.currency, base, inv.invoice_date)
        days = max(0, (today - inv.due_date).days if inv.due_date else 0)

        bucket = "90+" if days > 90 else ("current" if days <= 0 else f"{((days-1)//30)*30 + 1}-{(days//30)*30 + 30}")
        bucket_key = bucket if bucket in buckets else "90+"
        buckets[bucket_key] += float(conv)

        details.append({
            "invoice": inv.invoice_number,
            "employer": inv.employer.name,
            "due_date": str(inv.due_date),
            "original": f"{outstanding} {inv.currency}",
            "converted": f"{conv:.2f} {base}",
            "days_overdue": days,
            "bucket": bucket
        })

    return Response({
        "company": company.name,
        "as_of": str(today),
        "currency": base,
        "summary": buckets,
        "total_outstanding": sum(buckets.values()),
        "invoices": details
    })


# =============================================
# 4. JOB ORDER PROFITABILITY
# =============================================
@extend_schema(
    parameters=[
        OpenApiParameter('job_order_id', OpenApiTypes.STR, description='Job order id', required=True),
    ],
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_order_profitability_view(request):
    job_order_id = request.query_params.get('job_order_id')
    if not job_order_id:
        return Response({"error": "job_order_id required"}, status=400)

    job = JobOrder.objects.get(id=job_order_id)
    base = job.company.base_currency

    revenue = sum(convert_currency(l.amount, l.invoice.currency, base, l.invoice.invoice_date)
                  for l in InvoiceLine.objects.filter(candidate__job_order=job, invoice__status__in=['POSTED','PAID']))

    costs = sum(convert_currency(c.amount, c.currency, base, c.date)
                for c in CandidateCost.objects.filter(candidate__job_order=job, candidate__current_stage='DEPLOYED'))

    profit = revenue - costs
    margin = (profit / revenue * 100) if revenue > 0 else 0

    return Response({
        "job_order": str(job),
        "employer": job.employer.name,
        "currency": base,
        "revenue": float(revenue),
        "costs": float(costs),
        "profit": float(profit),
        "margin_percent": round(float(margin), 2)
    })


# =============================================
# 5. EMPLOYER PROFITABILITY
# =============================================
@extend_schema(
    parameters=[
        OpenApiParameter('employer_id', OpenApiTypes.STR, description='Employer id', required=True),
    ],
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employer_profitability_view(request):
    employer_id = request.query_params.get('employer_id')
    if not employer_id:
        return Response({"error": "employer_id required"}, status=400)

    employer = Employer.objects.get(id=employer_id)
    total_revenue = total_cost = total_profit = Decimal('0')

    for job in employer.job_orders.all():
        base = job.company.base_currency
        rev = sum(convert_currency(l.amount, l.invoice.currency, base, l.invoice.invoice_date)
                  for l in InvoiceLine.objects.filter(candidate__job_order=job, invoice__status__in=['POSTED','PAID']))
        cost = sum(convert_currency(c.amount, c.currency, base, c.date)
                   for c in CandidateCost.objects.filter(candidate__job_order=job, candidate__current_stage='DEPLOYED'))
        total_revenue += rev
        total_cost += cost
        total_profit += (rev - cost)

    return Response({
        "employer": employer.name,
        "total_revenue": float(total_revenue),
        "total_costs": float(total_cost),
        "gross_profit": float(total_profit),
        "overall_margin": round(float(total_profit/total_revenue*100) if total_revenue else 0, 2)
    })


# =============================================
# 6. RECRUITMENT KPI DASHBOARD
# =============================================
@extend_schema(
    parameters=[
        OpenApiParameter('company_id', OpenApiTypes.UUID, description='Company ID', required=True),
    ],
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recruitment_kpi_dashboard(request):
    company_id = request.query_params.get('company_id')
    if not company_id:
        return Response({"error": "company_id required"}, status=400)

    candidates = Candidate.objects.filter(job_order__company_id=company_id)
    total = candidates.count()
    deployed = candidates.filter(current_stage='DEPLOYED').count()

    return Response({
        "total_candidates": total,
        "deployed": deployed,
        "deployment_rate_percent": round(deployed/total*100, 1) if total else 0,
        "pending": total - deployed
    })


# =============================================
# 7. COST CENTER REPORT
# =============================================
@extend_schema(
    parameters=[
        OpenApiParameter('company_id', OpenApiTypes.UUID, description='Company ID', required=True),
    ],
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cost_center_report_view(request):
    company_id = request.query_params.get('company_id')
    if not company_id:
        return Response({"error": "company_id required"}, status=400)

    breakdown = CandidateCost.objects.filter(
        candidate__job_order__company_id=company_id
    ).values('cost_type').annotate(total=Sum('amount'))

    return Response({
        "breakdown": [
            {"type": dict(CandidateCost.COST_TYPE_CHOICES).get(b['cost_type']), "amount": float(b['total'] or 0)}
            for b in breakdown
        ]
    })


# =============================================
# 8. CASHFLOW FORECAST (90 DAYS)
# =============================================
@extend_schema(
    parameters=[
        OpenApiParameter('company_id', OpenApiTypes.UUID, description='Company ID', required=True),
    ],
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cashflow_forecast_view(request):
    company_id = request.query_params.get('company_id')
    if not company_id:
        return Response({"error": "company_id required"}, status=400)

    company = Company.objects.get(id=company_id)
    base = company.base_currency
    future = timezone.now().date() + timedelta(days=90)

    inflow = Decimal('0')
    outflow = Decimal('0')

    for inv in Invoice.objects.filter(company_id=company_id, status__in=['POSTED','SENT'], due_date__lte=future):
        due = inv.total_amount - inv.amount_paid
        if due > 0:
            inflow += convert_currency(due, inv.currency, base, inv.due_date)

    for bill in Bill.objects.filter(company_id=company_id, status='POSTED', due_date__lte=future):
        due = bill.total_amount - bill.amount_paid
        if due > 0:
            outflow += convert_currency(due, bill.currency, base, bill.due_date)

    return Response({
        "expected_inflow": float(inflow),
        "expected_outflow": float(outflow),
        "net_forecast": float(inflow - outflow)
    })


# =============================================
# 9. CANDIDATE PROFITABILITY
# =============================================
@extend_schema(
    parameters=[
        OpenApiParameter('candidate_id', OpenApiTypes.STR, description='Candidate id', required=True),
    ],
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_profitability_view(request):
    candidate_id = request.query_params.get('candidate_id')
    if not candidate_id:
        return Response({"error": "candidate_id required"}, status=400)
    # Try to serve from snapshot table if available (faster for frontend)
    snapshot = CandidateReport.objects.filter(candidate_id=candidate_id).order_by('-generated_at').first()
    if snapshot:
        # build a minimal response from snapshot
        try:
            candidate = Candidate.objects.get(id=candidate_id)
            job = candidate.job_order
            employer = job.employer
        except Candidate.DoesNotExist:
            return Response({"error": "candidate not found"}, status=404)

        return Response({
            "candidate": candidate.full_name,
            "passport": candidate.passport_number,
            "nationality": candidate.nationality,
            "job_order": str(job),
            "employer": employer.name,
            "current_stage": candidate.current_stage,
            "deployment_date": candidate.deployed_date.isoformat() if candidate.deployed_date else None,
            "base_currency": snapshot.currency,
            "revenue": {"total": float(snapshot.revenue), "lines": []},
            "costs": {"total": float(snapshot.cost), "reimbursable": None, "non_reimbursable": None, "breakdown": []},
            "profitability": {"gross_profit": float(snapshot.profit), "gross_margin_percent": float(snapshot.margin_percent), "profit_per_day": None},
            "generated_at": snapshot.generated_at.isoformat()
        })

    candidate = Candidate.objects.get(id=candidate_id)
    job = candidate.job_order
    base = job.company.base_currency

    # Revenue
    revenue_lines = InvoiceLine.objects.filter(
        candidate=candidate, invoice__status__in=['POSTED', 'PAID']
    ).select_related('invoice')

    revenue_total = Decimal('0')
    revenue_detail = []
    for line in revenue_lines:
        conv = convert_currency(line.amount, line.invoice.currency, base, line.invoice.invoice_date)
        revenue_total += conv
        revenue_detail.append({
            "invoice": line.invoice.invoice_number,
            "description": line.description,
            "amount_original": f"{line.amount:.2f} {line.invoice.currency}",
            "amount_converted": f"{conv:.2f} {base}",
            "date": line.invoice.invoice_date.isoformat()
        })

    # Costs
    costs = candidate.costs.all().select_related('vendor')
    cost_total = Decimal('0')
    cost_detail = []
    reimbursable = non_reimbursable = Decimal('0')

    for cost in costs:
        conv = convert_currency(cost.amount, cost.currency, base, cost.date)
        cost_total += conv
        if cost.reimbursable:
            reimbursable += conv
        else:
            non_reimbursable += conv

        cost_detail.append({
            "type": cost.get_cost_type_display(),
            "reimbursable": cost.reimbursable,
            "amount_original": f"{cost.amount:.2f} {cost.currency}",
            "amount_converted": f"{conv:.2f} {base}",
            "date": cost.date.isoformat(),
            "vendor": cost.vendor.name if cost.vendor else "Internal",
            "stage": cost.candidate.current_stage
        })

    profit = revenue_total - cost_total
    margin = (profit / revenue_total * 100) if revenue_total else Decimal('0')

    return Response({
        "candidate": candidate.full_name,
        "passport": candidate.passport_number,
        "nationality": candidate.nationality,
        "job_order": str(job),
        "employer": job.employer.name,
        "current_stage": candidate.current_stage,
        "deployment_date": candidate.deployed_date.isoformat() if candidate.deployed_date else None,
        "base_currency": base,

        "revenue": {
            "total": float(revenue_total),
            "lines": revenue_detail
        },
        "costs": {
            "total": float(cost_total),
            "reimbursable": float(reimbursable),
            "non_reimbursable": float(non_reimbursable),
            "breakdown": cost_detail
        },
        "profitability": {
            "gross_profit": float(profit),
            "gross_margin_percent": round(float(margin), 2),
            "profit_per_day": float(profit / max((timezone.now().date() - candidate.created_at.date()).days, 1))
        },
        "generated_at": timezone.now().isoformat()
    })

# =============================================
# 3. MARGIN LEADERBOARD — WHO ARE YOUR GODS?
# =============================================
from django.db.models import Sum, Q, F, Count, Avg, DecimalField, ExpressionWrapper, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone
@extend_schema(
    parameters=[
        OpenApiParameter('company_id', OpenApiTypes.UUID, description='Company ID', required=True),
        OpenApiParameter('limit', OpenApiTypes.INT, description='Max results to return', required=False),
    ]
    ,
    responses=OpenApiTypes.OBJECT
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def margin_leaderboard_view(request):
    company_id = request.query_params.get('company_id')
    limit = int(request.query_params.get('limit', 20))
    # If snapshots exist, use them for faster response
    if CandidateReport.objects.filter(company_id=company_id).exists():
        snaps = CandidateReport.objects.filter(company_id=company_id).order_by('-margin_percent', '-profit')[:limit]
        top = []
        for i, s in enumerate(snaps):
            # try to fetch candidate record for names
            try:
                cand = Candidate.objects.get(id=s.candidate_id)
                job_order_str = str(cand.job_order)
                passport = cand.passport_number
                full_name = cand.full_name
            except Candidate.DoesNotExist:
                full_name = str(s.candidate_id)
                passport = None
                job_order_str = None
            top.append({
                "rank": i+1,
                "candidate": full_name,
                "passport": passport,
                "revenue": float(s.revenue),
                "cost": float(s.cost),
                "profit": float(s.profit),
                "margin_percent": float(s.margin_percent),
                "job_order": job_order_str
            })
        return Response({"title": "Margin Kings Leaderboard", "company_id": company_id, "top_performers": top})

    candidates = Candidate.objects.filter(
        job_order__company_id=company_id,
        current_stage='DEPLOYED'
    ).annotate(
            revenue=Coalesce(Sum('invoiceline__amount', filter=Q(invoiceline__invoice__status__in=['POSTED','PAID'])), Value(Decimal('0')), output_field=DecimalField()),
            cost=Coalesce(Sum('costs__amount'), Value(Decimal('0')), output_field=DecimalField()),
        profit=ExpressionWrapper(F('revenue') - F('cost'), output_field=DecimalField()),
        margin=ExpressionWrapper(
            F('profit') * 100 / F('revenue'),
            output_field=FloatField()
        )
    ).filter(revenue__gt=0).order_by('-margin', '-profit')[:limit]

    return Response({
        "title": "Margin Kings Leaderboard",
        "company_id": company_id,
        "top_performers": [
            {
                "rank": i+1,
                "candidate": c.full_name,
                "passport": c.passport_number,
                "revenue": float(c.revenue),
                "cost": float(c.cost),
                "profit": float(c.profit),
                "margin_percent": round(c.margin, 2) if c.margin else 0,
                "job_order": str(c.job_order)
            } for i, c in enumerate(candidates)
        ]
    })


