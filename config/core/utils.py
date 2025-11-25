# accounting/utils.py
"""
Accounting Utilities for Mahad Group Accounting Suite
Handles all automatic journal postings, FX conversions, and bulk operations
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from core.models import (
    Journal, JournalLine, Candidate, CandidateCost, Invoice, Receipt,
    Payment, Bill, Company, FxRate
)
from django.core.exceptions import ValidationError


def get_fx_rate(from_currency: str, to_currency: str, date=None) -> Decimal:
    """Get FX rate with fallback to latest"""
    if from_currency == to_currency:
        return Decimal('1.0000')
    
    date = date or timezone.now().date()
    try:
        return FxRate.objects.get(
            from_currency=from_currency,
            to_currency=to_currency,
            rate_date=date
        ).rate
    except FxRate.DoesNotExist:
        # Get latest available rate
        latest = FxRate.objects.filter(
            from_currency=from_currency,
            to_currency=to_currency
        ).order_by('-rate_date').first()
        if latest:
            return latest.rate
        raise ValidationError(f"No FX rate found: {from_currency} → {to_currency}")


def convert_currency(amount: Decimal, from_curr: str, to_curr: str, date=None) -> Decimal:
    """Convert amount using current or historical FX rate"""
    rate = get_fx_rate(from_curr, to_curr, date)
    return (amount * rate).quantize(Decimal('0.0001'))


def post_journal(company: Company, description: str, lines: list, posted_by=None):
    """Create journal with balanced lines"""
    total_debit = sum(line['debit'] for line in lines)
    total_credit = sum(line['credit'] for line in lines)
    
    if abs(total_debit - total_credit) > Decimal('0.01'):
        raise ValidationError(f"Journal unbalanced: Debit {total_debit}, Credit {total_credit}")
    
    journal = Journal.objects.create(
        company=company,
        description=description,
        posted_by=posted_by or company.default_posting_user(),
        created_by=posted_by or company.default_posting_user(),
        posted_at=timezone.now()
    )
    
    for line in lines:
        JournalLine.objects.create(
            journal=journal,
            account=line['account'],
            debit=line['debit'],
            credit=line['credit'],
            description=line.get('description', '')
        )
    
    return journal


# ============================================================
# CANDIDATE COST → WIP JOURNAL
# ============================================================

@transaction.atomic
def post_wip_cost_journal(cost: CandidateCost):
    """DR WIP - Visa/Medical/Ticket, CR Accounts Payable"""
    candidate = cost.candidate
    company = candidate.job_order.company
    base_amount = cost.amount
    base_curr = cost.currency
    
    # Convert to company base currency
    company_curr = company.base_currency
    local_amount = convert_currency(base_amount, base_curr, company_curr, cost.date_incurred)
    
    lines = [
        # DR: Work in Progress (Asset)
        {
            "account": company.chart_of_accounts.wip_account,
            "debit": local_amount,
            "credit": Decimal('0'),
            "description": f"WIP - {cost.get_cost_type_display()} - {candidate.full_name}"
        },
        # CR: Accounts Payable
        {
            "account": company.chart_of_accounts.accounts_payable,
            "debit": Decimal('0'),
            "credit": local_amount,
            "description": f"AP - {cost.vendor.name if cost.vendor else 'Vendor'}"
        }
    ]
    
    return post_journal(
        company=company,
        description=f"Candidate Cost: {candidate.passport_number} - {cost.get_cost_type_display()}",
        lines=lines
    )


# ============================================================
# CANDIDATE DEPLOYED → REVENUE RECOGNITION
# ============================================================

@transaction.atomic
def post_deployment_journal(candidate: Candidate):
    """DR COGS (total WIP costs), CR WIP + Revenue to Income"""
    if candidate.current_stage != 'DEPLOYED':
        return None
    
    job_order = candidate.job_order
    company = job_order.company
    
    # Total costs in company currency
    total_wip = Decimal('0')
    for cost in candidate.costs.all():
        local = convert_currency(cost.amount, cost.currency, company.base_currency, cost.date_incurred)
        total_wip += local
    
    revenue_local = convert_currency(job_order.agreed_fee, job_order.currency, company.base_currency)
    
    lines = [
        # DR: Cost of Goods Sold
        {
            "account": company.chart_of_accounts.cogs_account,
            "debit": total_wip,
            "credit": Decimal('0'),
            "description": f"COGS - Deployment {candidate.full_name}"
        },
        # CR: Clear WIP
        {
            "account": company.chart_of_accounts.wip_account,
            "debit": Decimal('0'),
            "credit": total_wip,
            "description": f"WIP Cleared - {candidate.passport_number}"
        },
        # CR: Revenue
        {
            "account": company.chart_of_accounts.revenue_account,
            "debit": Decimal('0'),
            "credit": revenue_local,
            "description": f"Revenue - Placement {candidate.full_name}"
        },
        # DR: Accounts Receivable (if not yet invoiced)
        {
            "account": company.chart_of_accounts.accounts_receivable,
            "debit": revenue_local,
            "credit": Decimal('0'),
            "description": f"AR - Placement Fee {candidate.passport_number}"
        }
    ]
    
    return post_journal(
        company=company,
        description=f"Deployment Revenue Recognition - {candidate.full_name}",
        lines=lines
    )


# ============================================================
# INVOICE POSTING
# ============================================================

@transaction.atomic
def post_invoice_journal(invoice: Invoice):
    """DR AR, CR Revenue + Tax Liability (if applicable)"""
    company = invoice.company
    total_local = convert_currency(invoice.total_amount, invoice.currency, company.base_currency)
    tax_local = convert_currency(invoice.tax_amount or 0, invoice.currency, company.base_currency)
    net_local = total_local - tax_local
    
    lines = [
        # DR: Accounts Receivable
        {
            "account": company.chart_of_accounts.accounts_receivable,
            "debit": total_local,
            "credit": Decimal('0'),
            "description": f"Invoice {invoice.invoice_number}"
        },
        # CR: Revenue
        {
            "account": company.chart_of_accounts.revenue_account,
            "debit": Decimal('0'),
            "credit": net_local,
            "description": f"Invoice {invoice.invoice_number} - Service"
        },
    ]
    
    if tax_local > 0:
        lines.append({
            "account": company.chart_of_accounts.tax_payable,
            "debit": Decimal('0'),
            "credit": tax_local,
            "description": f"VAT/GST Output Tax - {invoice.invoice_number}"
        })
    
    return post_journal(
        company=company,
        description=f"Invoice Posted: {invoice.invoice_number}",
        lines=lines
    )


# ============================================================
# RECEIPT & PAYMENT JOURNALS
# ============================================================

def post_receipt_journal(receipt: Receipt):
    """DR Bank, CR AR + FX Gain/Loss"""
    company = receipt.company
    amount_local = convert_currency(receipt.amount, receipt.currency, company.base_currency)
    
    # Find original AR amount
    original_ar = receipt.invoice.total_amount if receipt.invoice else receipt.amount
    original_local = convert_currency(original_ar, receipt.invoice.currency, company.base_currency)
    
    fx_gain_loss = amount_local - original_local
    
    lines = [
        {
            "account": receipt.bank_account,
            "debit": amount_local,
            "credit": Decimal('0'),
            "description": f"Payment received - {receipt.reference}"
        },
        {
            "account": company.chart_of_accounts.accounts_receivable,
            "debit": Decimal('0'),
            "credit": original_local,
            "description": f"AR Cleared - {receipt.invoice.invoice_number if receipt.invoice else ''}"
        }
    ]
    
    if abs(fx_gain_loss) > Decimal('0.01'):
        account = company.chart_of_accounts.fx_gain if fx_gain_loss > 0 else company.chart_of_accounts.fx_loss
        lines.append({
            "account": account,
            "debit": fx_gain_loss if fx_gain_loss > 0 else Decimal('0'),
            "credit": abs(fx_gain_loss) if fx_gain_loss < 0 else Decimal('0'),
            "description": f"FX Gain/Loss on receipt"
        })
    
    return post_journal(company, f"Receipt: {receipt.reference}", lines)


def post_payment_journal(payment: Payment):
    """DR AP, CR Bank"""
    company = payment.company
    amount_local = convert_currency(payment.amount, payment.currency, company.base_currency)
    
    lines = [
        {
            "account": company.chart_of_accounts.accounts_payable,
            "debit": amount_local,
            "credit": Decimal('0'),
            "description": f"Payment to {payment.vendor.name}"
        },
        {
            "account": payment.bank_account,
            "debit": Decimal('0'),
            "credit": amount_local,
            "description": f"Bank payment - {payment.reference}"
        }
    ]
    
    return post_journal(company, f"Payment: {payment.reference}", lines)


# ============================================================
# BULK CANDIDATE OPERATIONS
# ============================================================

@transaction.atomic
def bulk_move_stage(candidate_ids: list, new_stage: str, user=None):
    """Move multiple candidates to new stage (e.g., DEPLOYED)"""
    candidates = Candidate.objects.filter(id__in=candidate_ids)
    updated = 0
    
    for candidate in candidates:
        old_stage = candidate.current_stage
        candidate.current_stage = new_stage
        if new_stage == 'DEPLOYED' and not candidate.deployed_date:
            candidate.deployed_date = timezone.now().date()
        candidate.save()
        
        if new_stage == 'DEPLOYED' and old_stage != 'DEPLOYED':
            post_deployment_journal(candidate)
            updated += 1
    
    return {"updated": updated, "total": len(candidate_ids)}


@transaction.atomic
def bulk_add_cost(candidate_ids: list, cost_data: dict, user=None):
    """Add same cost (e.g., medical) to multiple candidates"""
    created = []
    for candidate_id in candidate_ids:
        candidate = Candidate.objects.get(id=candidate_id)
        cost_data['candidate'] = candidate.id
        cost = CandidateCost.objects.create(**cost_data)
        post_wip_cost_journal(cost)
        created.append(cost)
    
    return {"created": len(created)}


@transaction.atomic
def bulk_generate_invoices(job_order_id: int, candidate_ids: list, invoice_date=None):
    """Generate one invoice for multiple deployed candidates"""
    from core.views import invoice_generate  # Avoid circular import
    # This reuses your existing generate logic
    # Or implement lightweight version here
    pass