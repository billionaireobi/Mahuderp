# reports/urls.py
from django.urls import path
from .views import *

app_name = "reports"

urlpatterns = [
    path('profit_loss/', profit_loss_report, name='profit-loss'),
    path('balance_sheet/', balance_sheet_report, name='balance-sheet'),
    path('ar_aging/', ar_aging_report, name='ar-aging'),
    path('job_order_profitability/', job_order_profitability_view, name='job-order-profitability'),
    path('employer_profitability/', employer_profitability_view, name='employer-profitability'),
    path('recruitment_kpi/', recruitment_kpi_dashboard, name='recruitment-kpi'),
    path('cost_centers/', cost_center_report_view, name='cost-centers'),
    path('cashflow_forecast/', cashflow_forecast_view, name='cashflow-forecast'),
    path('candidate_profitability/', candidate_profitability_view, name='candidate-profitability'),

    path('reports/margin-leaderboard/', margin_leaderboard_view),
]