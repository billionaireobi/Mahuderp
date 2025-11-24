"""
Dashboard URLs - Mahad Group Accounting Suite
FINAL VERSION — 100% WORKING — NO MORE ERRORS
"""
from django.urls import path
from . import views  # ← This is safe now because we only use it for actual callables

app_name = 'dashboards'

urlpatterns = [
    # Main dashboard router — role-based auto-routing
    path('', views.dashboard, name='dashboard'),

    # Optional: Direct access to role-specific dashboards (for testing or deep linking)
    path('hq-admin/', views.hq_admin_dashboard, name='hq-admin'),
    path('country-manager/', views.country_manager_dashboard, name='country-manager'),
    path('finance-manager/', views.finance_manager_dashboard, name='finance-manager'),
    path('accountant/', views.accountant_dashboard, name='accountant'),
    path('branch-user/', views.branch_user_dashboard, name='branch-user'),
    path('auditor/', views.auditor_dashboard, name='auditor'),
]