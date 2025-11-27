from django.core.management.base import BaseCommand
from django.db.models import Sum, Q, F
from decimal import Decimal
from django.utils import timezone
from reports.models import CandidateReport, JobOrderReport
from core.models import Candidate, InvoiceLine, CandidateCost, JobOrder


class Command(BaseCommand):
    help = 'Generate report snapshots for candidates and job orders'

    def add_arguments(self, parser):
        parser.add_argument('--company-id', dest='company_id', help='Company UUID to restrict', required=False)
        parser.add_argument('--period-start', dest='period_start', help='YYYY-MM-DD', required=False)
        parser.add_argument('--period-end', dest='period_end', help='YYYY-MM-DD', required=False)

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        period_start = options.get('period_start')
        period_end = options.get('period_end')

        candidates = Candidate.objects.all()
        if company_id:
            candidates = candidates.filter(job_order__company_id=company_id)

        if period_start:
            # filter invoice lines and candidate costs later by invoice.invoice_date or cost.date
            pass

        count = 0
        for c in candidates:
            # revenue
            invoicelines = InvoiceLine.objects.filter(candidate=c, invoice__status__in=['POSTED','PAID'])
            if period_start:
                invoicelines = invoicelines.filter(invoice__invoice_date__gte=period_start)
            if period_end:
                invoicelines = invoicelines.filter(invoice__invoice_date__lte=period_end)
            revenue = invoicelines.aggregate(total=Sum('amount'))['total'] or Decimal('0')

            costs_qs = CandidateCost.objects.filter(candidate=c)
            if period_start:
                costs_qs = costs_qs.filter(date__gte=period_start)
            if period_end:
                costs_qs = costs_qs.filter(date__lte=period_end)
            cost = costs_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

            profit = (revenue - cost)
            margin = (profit / revenue * 100) if revenue and revenue != 0 else Decimal('0')

            CandidateReport.objects.create(
                company_id=c.job_order.company_id,
                candidate_id=c.id,
                job_order_id=c.job_order_id,
                employer_id=c.job_order.employer_id,
                period_start=period_start,
                period_end=period_end,
                revenue=revenue,
                cost=cost,
                profit=profit,
                margin_percent=round(margin, 2),
                currency=c.job_order.currency
            )
            count += 1

        # Job orders
        joborders = JobOrder.objects.all()
        if company_id:
            joborders = joborders.filter(company_id=company_id)

        for j in joborders:
            invoicelines = InvoiceLine.objects.filter(candidate__job_order=j, invoice__status__in=['POSTED','PAID'])
            if period_start:
                invoicelines = invoicelines.filter(invoice__invoice_date__gte=period_start)
            if period_end:
                invoicelines = invoicelines.filter(invoice__invoice_date__lte=period_end)
            revenue = invoicelines.aggregate(total=Sum('amount'))['total'] or Decimal('0')

            costs_qs = CandidateCost.objects.filter(candidate__job_order=j)
            if period_start:
                costs_qs = costs_qs.filter(date__gte=period_start)
            if period_end:
                costs_qs = costs_qs.filter(date__lte=period_end)
            cost = costs_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

            profit = (revenue - cost)
            avg_margin = (profit / revenue * 100) if revenue and revenue != 0 else Decimal('0')

            JobOrderReport.objects.create(
                company_id=j.company_id,
                job_order_id=j.id,
                employer_id=j.employer_id,
                period_start=period_start,
                period_end=period_end,
                revenue=revenue,
                cost=cost,
                profit=profit,
                avg_margin_percent=round(avg_margin, 2),
                currency=j.currency
            )

        self.stdout.write(self.style.SUCCESS(f"Generated {count} candidate snapshots and job order snapshots."))
