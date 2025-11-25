# reports/views.py
# MAHAD GROUP ACCOUNTING SUITE — COMPLETE FINANCIAL & RECRUITMENT REPORTS
# Multi-Company | Multi-Currency | Double-Entry | Candidate Profitability | 5 Countries
# © 2025 Mahad Group — Built for Global Recruitment Domination

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Q, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from core.models import (
    Company, JobOrder, Candidate, CandidateCost,
    Invoice, InvoiceLine, Bill, Employer, FxRate
)


# =============================================
# FX CONVERSION ENGINE — THE HEART OF MULTI-CURRENCY
# =============================================
def convert_currency(amount: Decimal, from_currency: str, to_currency: str, date=None) -> Decimal:
    if not amount or amount == 0:
        return Decimal('0.00')
    if from_currency == to_currency:
        return round(amount, 2)

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

        # Reverse rate fallback
        reverse = FxRate.objects.filter(
            from_currency=to_currency,
            to_currency=from_currency,
            rate_date__lte=date
        ).order_by('-rate_date').first()
        if reverse:
            return round(amount / reverse.rate, 2)
    except Exception:
        pass

    return round(amount, 2)  # Fallback


# =============================================
# 1. PROFIT & LOSS STATEMENT (FULLY MULTI-CURRENCY)
# =============================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profit_loss_report(request):
    company_id = request.query_params.get('company_id')
    from_date = request.query_params.get('from_date')
    to_date = request.query_params.get('to_date', timezone.now().date())
    job_order_id = request.query_params.get('job_order_id')
    candidate_id = request.query_params.get('candidate_id')

    if not company_id:
        return Response({"error": "company_id required"}, status=400)

    company = Company.objects.get(id=company_id)
    base = company.base_currency

    inv_filter = Q(invoice__company_id=company_id, invoice__status__in=['POSTED', 'PAID'])
    cost_filter = Q(candidate__job_order__company_id=company_id, candidate__current_stage='DEPLOYED')

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

    revenue_total = Decimal('0.00')
    cogs_total = Decimal('0.00')
    revenue_lines = []
    cogs_lines = []

    for line in InvoiceLine.objects.filter(inv_filter):
        conv = convert_currency(line.amount, line.invoice.currency, base, line.invoice.invoice_date)
        revenue_total += conv
        revenue_lines.append({
            "candidate": line.candidate.full_name if line.candidate else "N/A",
            "description": line.description,
            "original": f"{line.amount} {line.invoice.currency}",
            "converted": f"{conv:.2f} {base}",
            "date": str(line.invoice.invoice_date)
        })

    for cost in CandidateCost.objects.filter(cost_filter):
        conv = convert_currency(cost.amount, cost.currency, base, cost.date)
        cogs_total += conv
        cogs_lines.append({
            "candidate": cost.candidate.full_name,
            "type": cost.get_cost_type_display(),
            "original": f"{cost.amount} {cost.currency}",
            "converted": f"{conv:.2f} {base}",
            "date": str(cost.date)
        })

    gross_profit = revenue_total - cogs_total
    gross_margin = (gross_profit / revenue_total * 100) if revenue_total > 0 else Decimal('0')

    return Response({
        "company": company.name,
        "base_currency": base,
        "period": f"{from_date or 'Beginning'} to {to_date}",
        "revenue": {"total": float(revenue_total), "lines": revenue_lines[:100]},
        "cogs": {"total": float(cogs_total), "lines": cogs_lines[:100]},
        "gross_profit": float(gross_profit),
        "gross_margin_percent": round(float(gross_margin), 2),
        "generated_at": timezone.now().isoformat()
    })


# =============================================
# 2. BALANCE SHEET (MULTI-CURRENCY)
# =============================================
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
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_profitability_view(request):
    candidate_id = request.query_params.get('candidate_id')
    if not candidate_id:
        return Response({"error": "candidate_id required"}, status=400)

    candidate = Candidate.objects.get(id=candidate_id)
    job = candidate.job_order
    base = job.company.base_currency

    revenue = sum(convert_currency(l.amount, l.invoice.currency, base, l.invoice.invoice_date)
                  for l in InvoiceLine.objects.filter(candidate=candidate, invoice__status__in=['POSTED','PAID']))

    costs = sum(convert_currency(c.amount, c.currency, base, c.date) for c in candidate.costs.all())

    profit = revenue - costs
    margin = (profit / revenue * 100) if revenue > 0 else Decimal('0')

    return Response({
        "candidate": candidate.full_name,
        "passport": candidate.passport_number,
        "job_order": str(job),
        "currency": base,
        "revenue": float(revenue),
        "total_costs": float(costs),
        "profit": float(profit),
        "margin_percent": round(float(margin), 2),
        "current_stage": candidate.current_stage
    })