"""
Management command to seed initial data
File: core/management/commands/seed_data.py

Create the directory structure first:
core/
  management/
    __init__.py
    commands/
      __init__.py
      seed_data.py
"""

from django.core.management.base import BaseCommand
from core.models import Company, Branch, Currency, CompanyProfile


class Command(BaseCommand):
    help = 'Seed initial data for currencies, companies, company profiles, and branches'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🌱 Seeding initial data...'))
        
        # Seed Currencies
        self.seed_currencies()
        
        # Seed Companies and Profiles
        self.seed_companies()
        
        # Seed Branches
        self.seed_branches()
        
        self.stdout.write(self.style.SUCCESS('✅ Data seeding completed successfully!'))

    def seed_currencies(self):
        """Seed supported currencies"""
        currencies = [
            {'code': 'INR', 'name': 'Indian Rupee', 'symbol': '₹'},
            {'code': 'KES', 'name': 'Kenyan Shilling', 'symbol': 'KSh'},
            {'code': 'AED', 'name': 'UAE Dirham', 'symbol': 'د.إ'},
            {'code': 'QAR', 'name': 'Qatari Riyal', 'symbol': 'ر.ق'},
            {'code': 'PHP', 'name': 'Philippine Peso', 'symbol': '₱'},
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
        ]
        
        for currency_data in currencies:
            currency, created = Currency.objects.get_or_create(
                code=currency_data['code'],
                defaults={
                    'name': currency_data['name'],
                    'symbol': currency_data['symbol'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created currency: {currency.code}')
            else:
                self.stdout.write(f'  - Currency already exists: {currency.code}')

    def seed_companies(self):
        """Seed initial companies for each country and create their profiles"""
        companies = [
            {
                'name': 'Mahad Manpower India',
                'code': 'IN',
                'legal_name': 'Mahad Manpower Services Private Limited',
                'country': 'IN',
                'base_currency': 'INR',
                'tax_rate': 18.00,
                'address': 'Mumbai Office Complex',
                'phone': '+91-22-12345678',
                'email': 'india@mahadgroup.com',
            },
            {
                'name': 'Mahad Manpower Kenya',
                'code': 'KE',
                'legal_name': 'Mahad Manpower Kenya Limited',
                'country': 'KE',
                'base_currency': 'KES',
                'tax_rate': 16.00,
                'address': 'Nairobi Business District',
                'phone': '+254-20-1234567',
                'email': 'kenya@mahadgroup.com',
            },
            {
                'name': 'Mahad Manpower UAE',
                'code': 'AE',
                'legal_name': 'Mahad Manpower Services LLC',
                'country': 'AE',
                'base_currency': 'AED',
                'tax_rate': 5.00,
                'address': 'Dubai Business Bay',
                'phone': '+971-4-1234567',
                'email': 'uae@mahadgroup.com',
            },
            {
                'name': 'Mahad Manpower Qatar',
                'code': 'QA',
                'legal_name': 'Mahad Manpower Qatar W.L.L',
                'country': 'QA',
                'base_currency': 'QAR',
                'tax_rate': 0.00,
                'address': 'Doha Business District',
                'phone': '+974-4412-3456',
                'email': 'qatar@mahadgroup.com',
            },
            {
                'name': 'Mahad Manpower Philippines',
                'code': 'PH',
                'legal_name': 'Mahad Manpower Philippines Inc.',
                'country': 'PH',
                'base_currency': 'PHP',
                'tax_rate': 12.00,
                'address': 'Makati Business District',
                'phone': '+63-2-1234-5678',
                'email': 'philippines@mahadgroup.com',
            },
        ]
        
        for company_data in companies:
            company, created = Company.objects.get_or_create(
                code=company_data['code'],
                defaults={
                    'name': company_data['name'],
                    'country': company_data['country'],
                    'base_currency': company_data['base_currency'],
                    'tax_rate': company_data['tax_rate'],
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created company: {company.name}')
            else:
                self.stdout.write(f'  - Company already exists: {company.name}')
            
            # Create CompanyProfile
            if not hasattr(company, 'profile'):
                CompanyProfile.objects.create(
                    company=company,
                    legal_name=company_data.get('legal_name'),
                    address=company_data.get('address'),
                    phone=company_data.get('phone'),
                    email=company_data.get('email'),
                )
                self.stdout.write(f'    ✓ Created profile for company: {company.name}')

    def seed_branches(self):
        """Seed initial branches for each company"""
        branches_data = [
            # India branches
            {'company_code': 'IN', 'name': 'Mumbai HQ', 'code': 'MUM', 'is_headquarters': True},
            {'company_code': 'IN', 'name': 'Delhi Branch', 'code': 'DEL', 'is_headquarters': False},
            
            # Kenya branches
            {'company_code': 'KE', 'name': 'Nairobi HQ', 'code': 'NBO', 'is_headquarters': True},
            {'company_code': 'KE', 'name': 'Mombasa Branch', 'code': 'MBA', 'is_headquarters': False},
            
            # UAE branches
            {'company_code': 'AE', 'name': 'Dubai HQ', 'code': 'DXB', 'is_headquarters': True},
            {'company_code': 'AE', 'name': 'Abu Dhabi Branch', 'code': 'AUH', 'is_headquarters': False},
            
            # Qatar branches
            {'company_code': 'QA', 'name': 'Doha HQ', 'code': 'DOH', 'is_headquarters': True},
            
            # Philippines branches
            {'company_code': 'PH', 'name': 'Manila HQ', 'code': 'MNL', 'is_headquarters': True},
            {'company_code': 'PH', 'name': 'Cebu Branch', 'code': 'CEB', 'is_headquarters': False},
        ]
        
        for branch_data in branches_data:
            company_code = branch_data.pop('company_code')
            try:
                company = Company.objects.get(code=company_code)
                branch_data['company'] = company
                
                branch, created = Branch.objects.get_or_create(
                    company=company,
                    code=branch_data['code'],
                    defaults={
                        'name': branch_data['name'],
                        'is_headquarters': branch_data['is_headquarters'],
                    }
                )
                if created:
                    self.stdout.write(f'  ✓ Created branch: {branch.name}')
                else:
                    self.stdout.write(f'  - Branch already exists: {branch.name}')
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ✗ Company not found: {company_code}'))
