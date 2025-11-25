"""
Core URLs for Mahad Group Accounting Suite
File: core/urls.py
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ============================================================
    # DASHBOARD
    # ============================================================
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    
    # ============================================================
    # COMPANIES
    # ============================================================
    path('companies/', views.company_list, name='company-list'),
    path('companies/<uuid:company_id>/', views.company_detail, name='company-detail'),
    
    # ============================================================
    # BRANCHES
    # ============================================================
    path('branches/', views.branch_list, name='branch-list'),
    path('branches/<uuid:branch_id>/', views.branch_detail, name='branch-detail'),
    # ============================================================
    # EMPLOYERS (Clients)
    # ============================================================
    path('employers/', views.employer_list, name='employer-list'),
    path('employers/<uuid:employer_id>/', views.employer_detail, name='employer-detail'),
    
    # ============================================================
    # VENDORS
    # ============================================================
    path('vendors/', views.vendor_list, name='vendor-list'),
    path('vendors/<uuid:vendor_id>/', views.vendor_detail, name='vendor-detail'),
    # ============================================================
    # JOB ORDERS
    # ============================================================
    path('job-orders/', views.job_order_list, name='job-order-list'),
    path('job-orders/<uuid:job_order_id>/', views.job_order_detail, name='job-order-detail'),
    path('job-orders/<int:job_order_id>/summary/', views.job_order_summary, name='job-order-summary'),
    # ============================================================
    # CANDIDATES
    # ============================================================
    path('candidates/', views.candidate_list, name='candidate-list'),
    path('candidates/<uuid:candidate_id>/', views.candidate_detail, name='candidate-detail'),
    path('candidates/<uuid:candidate_id>/add-cost/', views.candidate_add_cost, name='candidate-add-cost'),
    path('candidates/<int:candidate_id>/move_stage/', views.candidate_move_stage, name='candidate-move-stage'),
    path('candidates/<int:candidate_id>/profitability/', views.candidate_profitability, name='candidate-profitability'),
    path('candidates/<int:candidate_id>/add_cost/', views.candidate_add_cost, name='candidate-add-cost'),
    path('candidates/bulk/move-stage/', views.candidate_bulk_move_stage),
path('candidates/bulk/add-cost/', views.candidate_bulk_add_cost),
    
    # ============================================================
    # INVOICES
    # ============================================================
    path('invoices/', views.invoice_list, name='invoice-list'),
    path('invoices/<uuid:invoice_id>/', views.invoice_detail, name='invoice-detail'),
    path('invoices/generate/', views.invoice_generate, name='invoice-generate'),
    path('invoices/<int:invoice_id>/post/', views.invoice_post, name='invoice-post'),
    path('invoices/<int:invoice_id>/send/', views.invoice_send, name='invoice-send'),
    
    # Bills & Payments
    path('bills/<int:bill_id>/post/', views.bill_post, name='bill-post'),
    path('receipts/', views.receipt_create, name='receipt-create'),
    path('payments/', views.payment_create, name='payment-create'),
]