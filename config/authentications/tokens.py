"""
Custom JWT Token Claims for Mahad Group Accounting Suite
File: apps/auth/tokens.py

This module customizes JWT tokens to include additional user information
and role-based permissions in the token payload.
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Token serializer to include additional user information
    and permissions in the token payload
    """
    
    @classmethod
    def get_token(cls, user):
        """
        Override to add custom claims to the JWT token
        
        Args:
            user: User object
            
        Returns:
            Token with custom claims
        """
        token = super().get_token(user)
        
        # Add basic user information
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['full_name'] = user.get_full_name()
        token['role'] = user.role
        token['is_verified'] = user.is_verified
        token['is_active'] = user.is_active
        
        # Add company information
        if user.company:
            token['company_id'] = str(user.company.id)
            token['company_name'] = user.company.name
            token['company_code'] = user.company.code
            token['country'] = user.company.country
        else:
            token['company_id'] = None
            token['company_name'] = None
            token['company_code'] = None
            token['country'] = None
        
        # Add branch information
        if user.branch:
            token['branch_id'] = str(user.branch.id)
            token['branch_name'] = user.branch.name
            token['branch_code'] = user.branch.code
        else:
            token['branch_id'] = None
            token['branch_name'] = None
            token['branch_code'] = None
        
        # Add role-based permissions
        permissions = cls.get_role_permissions(user.role)
        token['permissions'] = permissions
        
        return token
    
    @staticmethod
    def get_role_permissions(role):
        """
        Get permissions for a given role
        
        Args:
            role (str): User role
            
        Returns:
            list: List of permission strings
        """
        permissions_map = {
            'HQ_ADMIN': [
                # Company Management
                'view_all_companies',
                'create_companies',
                'edit_companies',
                'delete_companies',
                
                # User Management
                'manage_users',
                'create_users',
                'edit_users',
                'delete_users',
                'assign_roles',
                
                # System
                'system_configuration',
                'view_system_logs',
                'manage_settings',
                
                # Reports
                'view_consolidated_reports',
                'export_reports',
                
                # Full Access
                'manage_all_data',
                'access_all_modules'
            ],
            
            'COUNTRY_MANAGER': [
                # Company Operations
                'view_company_data',
                'manage_company_operations',
                'edit_company_settings',
                
                # Branch Management
                'manage_branches',
                'create_branches',
                'edit_branches',
                
                # Financial
                'approve_transactions',
                'view_financial_reports',
                'manage_budgets',
                
                # HR & Recruitment
                'manage_employers',
                'manage_job_orders',
                'manage_candidates',
                
                # Reports
                'view_company_reports',
                'export_company_reports',
                
                # Users
                'view_company_users',
                'create_branch_users'
            ],
            
            'FINANCE_MANAGER': [
                # Invoicing
                'manage_invoices',
                'create_invoices',
                'edit_invoices',
                'delete_invoices',
                'approve_invoices',
                
                # Bills & Payments
                'manage_bills',
                'create_bills',
                'edit_bills',
                'delete_bills',
                'approve_bills',
                
                # Payments
                'manage_payments',
                'create_payments',
                'approve_payments',
                'manage_receipts',
                'record_receipts',
                
                # Banking
                'bank_reconciliation',
                'manage_bank_accounts',
                'import_bank_statements',
                
                # Accounting
                'period_close',
                'manage_journals',
                'view_gl_accounts',
                
                # Reports
                'view_financial_reports',
                'view_ar_aging',
                'view_ap_aging',
                'view_cash_flow',
                'export_financial_reports'
            ],
            
            'ACCOUNTANT': [
                # Invoicing
                'create_invoices',
                'edit_invoices',
                'view_invoices',
                
                # Bills
                'create_bills',
                'edit_bills',
                'view_bills',
                
                # Receipts & Payments
                'record_receipts',
                'record_payments',
                'view_receipts',
                'view_payments',
                
                # Candidates
                'manage_candidates',
                'add_candidate_costs',
                'view_candidate_costs',
                
                # Job Orders
                'view_job_orders',
                'view_job_order_costs',
                
                # Reports
                'view_reports',
                'view_basic_financial_reports',
                'export_basic_reports',
                
                # General
                'view_employers',
                'view_vendors'
            ],
            
            'BRANCH_USER': [
                # Candidates
                'manage_candidates',
                'create_candidates',
                'edit_candidates',
                'view_candidates',
                'add_candidate_costs',
                'update_candidate_stage',
                
                # Job Orders
                'view_job_orders',
                'view_job_order_details',
                'assign_candidates_to_jobs',
                
                # Limited Financial Access
                'limited_financial_access',
                'view_candidate_invoices',
                'view_candidate_costs',
                
                # General
                'view_employers',
                'view_branch_data'
            ],
            
            'AUDITOR': [
                # View Only Access
                'view_all_data',
                'view_all_companies',
                'view_all_transactions',
                'view_all_invoices',
                'view_all_bills',
                'view_all_payments',
                'view_all_receipts',
                'view_all_candidates',
                'view_all_job_orders',
                
                # Reports
                'view_financial_reports',
                'view_consolidated_reports',
                'download_reports',
                'export_all_reports',
                
                # Audit
                'view_audit_logs',
                'view_user_activity',
                'view_system_logs',
                'generate_audit_reports'
            ]
        }
        
        return permissions_map.get(role, [])
    
    def validate(self, attrs):
        """
        Override validate to add additional user data to response
        
        Args:
            attrs: Validated attributes
            
        Returns:
            dict: Token response with user data
        """
        data = super().validate(attrs)
        
        # Add comprehensive user data to response
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'full_name': self.user.get_full_name(),
            'phone': self.user.phone,
            'role': self.user.role,
            'role_display': self.user.get_role_display(),
            'is_verified': self.user.is_verified,
            'is_active': self.user.is_active,
            'date_joined': self.user.date_joined.isoformat() if self.user.date_joined else None,
            'last_login': self.user.last_login.isoformat() if self.user.last_login else None,
        }
        
        # Add company information
        if self.user.company:
            data['user']['company'] = {
                'id': str(self.user.company.id),
                'name': self.user.company.name,
                'code': self.user.company.code,
                'country': self.user.company.country
            }
        else:
            data['user']['company'] = None
        
        # Add branch information
        if self.user.branch:
            data['user']['branch'] = {
                'id': str(self.user.branch.id),
                'name': self.user.branch.name,
                'code': self.user.branch.code
            }
        else:
            data['user']['branch'] = None
        
        # Add permissions
        data['user']['permissions'] = self.get_role_permissions(self.user.role)
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom Token View using our custom serializer
    
    This view can be used as an alternative to the standard login view
    if you prefer to use SimpleJWT's built-in token endpoint
    
    Usage in urls.py:
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    """
    serializer_class = CustomTokenObtainPairSerializer


# Helper function to check permissions
def has_permission(user, permission):
    """
    Check if user has a specific permission based on their role
    
    Args:
        user: User object
        permission (str): Permission string to check
        
    Returns:
        bool: True if user has permission, False otherwise
    
    Example:
        if has_permission(request.user, 'create_invoices'):
            # Allow action
    """
    if not user or not user.is_authenticated:
        return False
    
    permissions = CustomTokenObtainPairSerializer.get_role_permissions(user.role)
    return permission in permissions


def has_any_permission(user, permissions):
    """
    Check if user has any of the specified permissions
    
    Args:
        user: User object
        permissions (list): List of permission strings
        
    Returns:
        bool: True if user has at least one permission
    """
    if not user or not user.is_authenticated:
        return False
    
    user_permissions = CustomTokenObtainPairSerializer.get_role_permissions(user.role)
    return any(perm in user_permissions for perm in permissions)


def has_all_permissions(user, permissions):
    """
    Check if user has all of the specified permissions
    
    Args:
        user: User object
        permissions (list): List of permission strings
        
    Returns:
        bool: True if user has all permissions
    """
    if not user or not user.is_authenticated:
        return False
    
    user_permissions = CustomTokenObtainPairSerializer.get_role_permissions(user.role)
    return all(perm in user_permissions for perm in permissions)