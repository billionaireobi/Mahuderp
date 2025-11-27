from django.core.management.base import BaseCommand
from decimal import Decimal
from django.utils import timezone
from django.db import models

from authentications.models import User

from core.models import (
    Company, Branch, Employer, Vendor, JobOrder, Candidate,
    CandidateCost, Invoice, InvoiceLine, Bill, BillLine
)

from reports.models import CandidateReport, JobOrderReport


class Command(BaseCommand):
    help = 'Seed a lightweight dataset for reports and create snapshot entries (for testing)'

    def add_arguments(self, parser):
        parser.add_argument('--company-code', type=str, default='TESTCO', help='Company code to create/use')
        parser.add_argument('--candidates', type=int, default=3, help='Number of candidates to create')

    def handle(self, *args, **options):
        code = options['company_code']
        num_candidates = options['candidates']

        self.stdout.write(self.style.NOTICE(f'Seeding reporting test data for company code: {code}'))

        # Create or get company
        company, _ = Company.objects.get_or_create(
            code=code,
            defaults={
                'name': 'Test Company',
                'short_name': 'TEST',
                'country': 'IN',
                'base_currency': 'USD'
            }
        )

        # Branch
        branch, _ = Branch.objects.get_or_create(
            company=company,
            code=f'{code}-HQ',
            defaults={'name': 'Headquarters', 'phone': '+000'}
        )

        # Employer
        employer, _ = Employer.objects.get_or_create(
            code=f'{code}-EMP',
            defaults={'name': 'Test Employer', 'country': 'IN', 'email': 'employer@test.local', 'phone': '+000'}
        )

        # Vendor
        vendor, _ = Vendor.objects.get_or_create(
            name=f'{code} Vendor',
            defaults={'type': 'OTHER', 'country': 'IN', 'contact': 'Vendor Contact', 'email': 'vendor@test.local', 'phone': '+000'}
        )

        # Job Order
        job_order, _ = JobOrder.objects.get_or_create(
            company=company,
            employer=employer,
            position_title='Test Position',
            defaults={'num_positions': 1, 'agreed_fee': Decimal('1500.00'), 'currency': company.base_currency}
        )

        created_candidates = []
        for i in range(num_candidates):
            cand, _ = Candidate.objects.get_or_create(
                job_order=job_order,
                passport_number=f'TESTPASS-{i}',
                defaults={'full_name': f'Test Candidate {i}', 'nationality': 'IN'}
            )
            created_candidates.append(cand)

            # Candidate cost
            cost_amount = Decimal('200.00')
            CandidateCost.objects.get_or_create(
                candidate=cand,
                cost_type='OTHER',
                defaults={'amount': cost_amount, 'currency': company.base_currency, 'vendor': vendor}
            )

            # Invoice (one per candidate)
            invoice, created = Invoice.objects.get_or_create(
                company=company,
                employer=employer,
                candidate=cand,
                defaults={
                    'invoice_date': timezone.now().date(),
                    'due_date': timezone.now().date(),
                    'currency': company.base_currency,
                }
            )

            # InvoiceLine
            InvoiceLine.objects.get_or_create(
                invoice=invoice,
                description=f'Placement fee for {cand.full_name}',
                defaults={'quantity': 1, 'unit_price': job_order.agreed_fee, 'amount': job_order.agreed_fee, 'candidate': cand}
            )

            # Ensure invoice totals updated
            invoice.total_amount = sum(line.amount for line in invoice.lines.all())
            invoice.net_amount = invoice.total_amount
            invoice.status = 'POSTED'
            invoice.save()

            # Bill for candidate costs
            bill, _ = Bill.objects.get_or_create(
                company=company,
                vendor=vendor,
                defaults={'bill_date': timezone.now().date(), 'due_date': timezone.now().date(), 'currency': company.base_currency}
            )

            BillLine.objects.get_or_create(
                bill=bill,
                description=f'Cost for {cand.full_name}',
                defaults={'quantity': 1, 'unit_price': cost_amount, 'amount': cost_amount}
            )

            bill.total_amount = sum(line.amount for line in bill.lines.all())
            bill.status = 'POSTED'
            bill.save()

        # Create a basic HQ user for testing
        user_email = f'test+{code.lower()}@test.local'
        user, created = User.objects.get_or_create(email=user_email, defaults={
            'first_name': 'Test', 'last_name': 'User', 'role': 'HQ_ADMIN', 'is_staff': True, 'is_verified': True
        })
        if created:
            user.set_password('password')
            user.save()

        # Create CandidateReport and JobOrderReport snapshots
        candidate_reports = 0
        for cand in created_candidates:
            revenue = InvoiceLine.objects.filter(candidate=cand).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
            cost = CandidateCost.objects.filter(candidate=cand).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
            profit = (revenue or Decimal('0')) - (cost or Decimal('0'))
            margin = (profit / revenue * Decimal('100')) if revenue and revenue != Decimal('0') else Decimal('0')

            CandidateReport.objects.create(
                company_id=company.id,
                candidate_id=cand.id,
                job_order_id=job_order.id,
                employer_id=employer.id,
                period_start=timezone.now().date(),
                period_end=timezone.now().date(),
                revenue=revenue or Decimal('0'),
                cost=cost or Decimal('0'),
                profit=profit,
                margin_percent=margin,
                currency=company.base_currency,
                generated_at=timezone.now()
            )
            candidate_reports += 1

        # JobOrder snapshot
        total_revenue = Invoice.objects.filter(job_order=job_order).aggregate(total=models.Sum('total_amount'))['total'] or Decimal('0')
        total_cost = CandidateCost.objects.filter(candidate__job_order=job_order).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        total_profit = (total_revenue or Decimal('0')) - (total_cost or Decimal('0'))
        avg_margin = (total_profit / total_revenue * Decimal('100')) if total_revenue and total_revenue != Decimal('0') else Decimal('0')

        JobOrderReport.objects.create(
            company_id=company.id,
            job_order_id=job_order.id,
            employer_id=employer.id,
            period_start=timezone.now().date(),
            period_end=timezone.now().date(),
            revenue=total_revenue or Decimal('0'),
            cost=total_cost or Decimal('0'),
            profit=total_profit,
            avg_margin_percent=avg_margin,
            currency=company.base_currency,
            generated_at=timezone.now()
        )

        self.stdout.write(self.style.SUCCESS(f'Created {len(created_candidates)} candidates, {candidate_reports} candidate snapshots, and 1 job order snapshot.'))