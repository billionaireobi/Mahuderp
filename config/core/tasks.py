# accounting/tasks.py
"""
Celery Background Tasks for Mahad Group Accounting Suite
PDF Generation • Email • Contract Management • Alerts
"""
from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from weasyprint import HTML, CSS
from io import BytesIO
import os
from datetime import timedelta

from core.models import Invoice, Employer, EmployerContract, CompanyProfile
from .utils import convert_currency


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_and_send_invoice_pdf(self, invoice_id):
    """
    Generate branded PDF invoice + send via email with payment links
    Uses CompanyProfile for logo, bank details, signature
    """
    try:
        invoice = Invoice.objects.select_related(
            'company__profile', 'employer', 'job_order'
        ).get(id=invoice_id)
        
        company_profile = invoice.company.profile
        
        # Render HTML template
        html_string = render_to_string('invoices/invoice_pdf.html', {
            'invoice': invoice,
            'company': {
                'name': company_profile.legal_name,
                'logo': company_profile.logo.url if company_profile.logo else None,
                'address': company_profile.address,
                'phone': company_profile.phone,
                'email': company_profile.email,
                'tax_id': company_profile.tax_registration,
                'bank_name': company_profile.bank_name,
                'account_name': company_profile.bank_account_name,
                'account_number': company_profile.bank_account_number,
                'iban': company_profile.bank_iban,
                'swift': company_profile.bank_swift,
                'signature': company_profile.signature_image.url if company_profile.signature_image else None,
            },
            'lines': invoice.lines.all(),
            'qr_code': invoice.generate_qr_payment_link() if hasattr(invoice, 'generate_qr_payment_link') else None,
        })
        
        # Convert to PDF
        html = HTML(string=html_string, base_url=settings.BASE_DIR)
        css = CSS(string='''
            @page { size: A4; margin: 1cm; }
            body { font-family: DejaVu Sans, sans-serif; }
        ''')
        
        pdf_file = BytesIO()
        html.write_pdf(target=pdf_file, css=css)
        pdf_file.seek(0)
        
        # Save PDF to Invoice
        filename = f"Invoice_{invoice.invoice_number}.pdf"
        invoice.pdf_file.save(filename, pdf_file)
        invoice.save()
        
        # Send Email
        subject = f"Invoice {invoice.invoice_number} - {company_profile.legal_name}"
        body = render_to_string('invoices/email_template.txt', {
            'invoice': invoice,
            'company_name': company_profile.legal_name,
        })
        
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invoice.employer.email],
            cc=[invoice.company.profile.email],
        )
        email.attach(filename, pdf_file.getvalue(), 'application/pdf')
        email.send()
        
        return f"Invoice {invoice.invoice_number} sent successfully"
        
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def send_contract_expiry_reminders():
    """
    Daily task: Send reminder 30, 14, and 7 days before contract expiry
    """
    today = timezone.now().date()
    upcoming = EmployerContract.objects.filter(
        is_active=True,
        end_date__gte=today
    )
    
    for contract in upcoming:
        days_left = (contract.end_date - today).days
        
        if days_left in [30, 14, 7]:
            days_text = f"{days_left} days" if days_left > 1 else "tomorrow"
            
            subject = f"Contract Expiry Alert - {contract.employer.name}"
            context = {
                'employer': contract.employer,
                'contract': contract,
                'days_left': days_left,
                'days_text': days_text,
            }
            
            html_message = render_to_string('contracts/expiry_email.html', context)
            plain_message = render_to_string('contracts/expiry_email.txt', context)
            
            EmailMessage(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[contract.employer.email, contract.notify_email or 'operations@mahadgroup.com'],
                reply_to=['operations@mahadgroup.com'],
            ).send()


@shared_task
def generate_monthly_employer_reports():
    """
    Auto-generate monthly placement reports for active employers
    """
    from core.models import Employer
    from datetime import date
    from dateutil.relativedelta import relativedelta
    
    last_month = date.today() - relativedelta(months=1)
    
    active_employers = Employer.objects.filter(is_active=True)
    
    for employer in active_employers:
        # Generate report logic here
        pass


# ============================================================
# EMPLOYER CONTRACT MANAGEMENT TASKS
# ============================================================

@shared_task
def process_contract_upload(contract_id, file_path):
    """
    Background processing for uploaded contract PDFs
    - Extract text
    - Auto-fill start/end dates
    - OCR if scanned
    """
    try:
        # Prefer the modern package name 'pypdf', fall back to 'PyPDF2' for compatibility
        try:
            from pypdf import PdfReader  # newer package name
        except Exception:
            from PyPDF2 import PdfReader
    except Exception as e:
        raise ImportError(
            "Neither 'pypdf' nor 'PyPDF2' is installed; install one (e.g. pip install pypdf) to enable PDF text extraction."
        ) from e

    import pytesseract
    from PIL import Image
    
    contract = EmployerContract.objects.get(id=contract_id)
    
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        # Simple date extraction logic (improve with NLP later)
        import re
        dates = re.findall(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}', text)
        if len(dates) >= 2:
            contract.start_date = dates[0]
            contract.end_date = dates[-1]
            contract.save()
            
    except Exception as e:
        contract.notes += f"\nAuto-extract failed: {str(e)}"
        contract.save()


@shared_task
def auto_renew_contracts():
    """
    Auto-renew contracts with renewal_option = 'auto'
    """
    today = timezone.now().date()
    renewing = EmployerContract.objects.filter(
        renewal_option='AUTO',
        end_date=today + timedelta(days=30),  # 30 days before expiry
        is_active=True
    )
    
    for contract in renewing:
        new_end = contract.end_date + timedelta(days=365)
        contract.end_date = new_end
        contract.renewal_count += 1
        contract.save()
        
        # Notify
        EmailMessage(
            subject=f"Contract Auto-Renewed - {contract.employer.name}",
            body=f"Contract renewed until {new_end}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['management@mahadgroup.com'],
        ).send()