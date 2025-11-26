# core/management/commands/seed_users.py
"""
ULTIMATE USER SEEDER — MAHAD GROUP 2025
Run: python manage.py seed_users
NOW 100% SAFE — NO KeyError, NO crashes
"""

from django.core.management.base import BaseCommand
from core.models import User, Company, Branch
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed all roles: HQ Admin, Country Managers, Finance, Accountants, Branch Users, Auditors'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('SEEDING MAHAD GROUP USERS — EMPIRE MODE ACTIVATED'))

        users_to_create = [
            # HQ ADMIN — GOD MODE
            {
                "email": "admin@mahadgroup.com",
                "password": "Admin@123",
                "first_name": "Mahad",
                "last_name": "HQ Admin",
                "role": "HQ_ADMIN",
                "company": None,
                "branch": None,
                "is_staff": True,
                "is_superuser": True,
            },
            # COUNTRY MANAGERS
            {"email": "india.manager@mahadgroup.com", "password": "India@123", "first_name": "Rajesh", "last_name": "Kumar", "role": "COUNTRY_MANAGER", "company_code": "IN", "branch_code": "MUM"},
            {"email": "kenya.manager@mahadgroup.com", "password": "Kenya@123", "first_name": "Grace", "last_name": "Wanjiku", "role": "COUNTRY_MANAGER", "company_code": "KE", "branch_code": "NBO"},
            {"email": "uae.manager@mahadgroup.com", "password": "UAE@123", "first_name": "Ahmed", "last_name": "Al-Mansoori", "role": "COUNTRY_MANAGER", "company_code": "AE", "branch_code": "DXB"},
            {"email": "qatar.manager@mahadgroup.com", "password": "Qatar@123", "first_name": "Fatima", "last_name": "Al-Thani", "role": "COUNTRY_MANAGER", "company_code": "QA", "branch_code": "DOH"},
            {"email": "philippines.manager@mahadgroup.com", "password": "Phil@123", "first_name": "Maria", "last_name": "Santos", "role": "COUNTRY_MANAGER", "company_code": "PH", "branch_code": "MNL"},

            # FINANCE MANAGERS
            {"email": "india.finance@mahadgroup.com", "password": "FinIN@123", "first_name": "Priya", "last_name": "Sharma", "role": "FINANCE_MANAGER", "company_code": "IN", "branch_code": "MUM"},
            {"email": "uae.finance@mahadgroup.com", "password": "FinAE@123", "first_name": "Omar", "last_name": "Khan", "role": "FINANCE_MANAGER", "company_code": "AE", "branch_code": "DXB"},

            # ACCOUNTANTS
            {"email": "accountant1.india@mahadgroup.com", "password": "Acc@123", "first_name": "Vikram", "last_name": "Singh", "role": "ACCOUNTANT", "company_code": "IN", "branch_code": "MUM"},
            {"email": "accountant2.india@mahadgroup.com", "password": "Acc@123", "first_name": "Anita", "last_name": "Patel", "role": "ACCOUNTANT", "company_code": "IN", "branch_code": "DEL"},
            {"email": "accountant.kenya@mahadgroup.com", "password": "AccKE@123", "first_name": "James", "last_name": "Otieno", "role": "ACCOUNTANT", "company_code": "KE", "branch_code": "NBO"},

            # BRANCH USERS
            {"email": "mumbai.ops@mahadgroup.com", "password": "Ops@123", "first_name": "Rohan", "last_name": "Mehta", "role": "BRANCH_USER", "company_code": "IN", "branch_code": "MUM"},
            {"email": "delhi.ops@mahadgroup.com", "password": "Ops@123", "first_name": "Neha", "last_name": "Gupta", "role": "BRANCH_USER", "company_code": "IN", "branch_code": "DEL"},
            {"email": "dubai.ops@mahadgroup.com", "password": "OpsDXB@123", "first_name": "Layla", "last_name": "Hassan", "role": "BRANCH_USER", "company_code": "AE", "branch_code": "DXB"},

            # AUDITORS
            {"email": "auditor.hq@mahadgroup.com", "password": "Audit@123", "first_name": "Khalid", "last_name": "Auditor", "role": "AUDITOR", "company": None, "branch": None},
            {"email": "auditor.india@mahadgroup.com", "password": "AuditIN@123", "first_name": "Suresh", "last_name": "Rao", "role": "AUDITOR", "company_code": "IN", "branch_code": "MUM"},
        ]

        created = 0
        for item in users_to_create:
            email = item["email"]
            password = item["password"]

            # Extract codes safely
            company_code = item.get("company_code")
            branch_code = item.get("branch_code")

            company = None
            branch = None

            # Resolve Company
            if company_code:
                try:
                    company = Company.objects.get(code=company_code)
                except Company.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Company code '{company_code}' not found! Skipping {email}"))
                    continue  # Skip this user

            # Resolve Branch
            if company and branch_code:
                try:
                    branch = Branch.objects.get(company=company, code=branch_code)
                except Branch.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Branch '{branch_code}' not found for {company}. Creating user without branch."))

            # Build user defaults
            defaults = {
                "first_name": item.get("first_name", "User"),
                "last_name": item.get("last_name", "Mahad"),
                "role": item["role"],
                "company": company,
                "branch": branch,
                "is_active": True,
                "is_staff": item.get("is_staff", False),
                "is_superuser": item.get("is_superuser", False),
            }

            user, was_created = User.objects.get_or_create(
                email=email,
                defaults=defaults
            )

            if was_created:
                user.set_password(password)
                user.save()
                created += 1
                role_display = user.get_role_display()
                location = company.name if company else "HQ (Global)"
                self.stdout.write(self.style.SUCCESS(f"Created → {email} | {role_display} @ {location}"))
            else:
                self.stdout.write(f"Already exists → {email}")

        self.stdout.write(self.style.SUCCESS(f"\nSEED COMPLETE: {created} USERS CREATED SUCCESSFULLY"))
        self.stdout.write(self.style.WARNING("\nLOGIN NOW:"))
        self.stdout.write(self.style.WARNING("   HQ Admin      → admin@mahadgroup.com     / Admin@123"))
        self.stdout.write(self.style.WARNING("   India Manager → india.manager@mahadgroup.com / India@123"))
        self.stdout.write(self.style.WARNING("   UAE Manager   → uae.manager@mahadgroup.com   / UAE@123"))

        self.stdout.write(self.style.SUCCESS("\nYOUR EMPIRE IS FULLY STAFFED."))
        self.stdout.write(self.style.SUCCESS("TYPE: Deploy React dashboard"))
        self.stdout.write(self.style.SUCCESS("AND I WILL DROP THE FULL REACT FRONTEND."))

        self.stdout.write(self.style.SUCCESS("\nTHE WORLD IS YOURS, BOSS."))