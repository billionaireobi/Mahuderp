# 📊 Role-Based Dashboards - Mahad Group Accounting Suite

Complete dashboard system with role-specific views and KPIs.

## 🎯 Dashboard Overview

Each user role gets a customized dashboard with relevant metrics and actions.

### Roles & Their Dashboards:

1. **HQ Admin** - Global consolidated view
2. **Country Manager** - Company-level operations
3. **Finance Manager** - Financial operations & AR/AP
4. **Accountant** - Day-to-day transactions
5. **Branch User** - Candidate pipeline management
6. **Auditor** - Read-only compliance view

---

## 📁 File Structure

```
dashboards/
├── __init__.py
├── apps.py
├── views.py          # All dashboard views
└── urls.py           # Dashboard routes
```

---

## 🔌 API Endpoints

### Main Dashboard (Auto-Routes)
```
GET /api/dashboard/
```
Automatically routes to the appropriate dashboard based on user's role.

### Role-Specific Endpoints
```
GET /api/dashboard/hq-admin/
GET /api/dashboard/country-manager/
GET /api/dashboard/finance-manager/
GET /api/dashboard/accountant/
GET /api/dashboard/branch-user/
GET /api/dashboard/auditor/
```

---

## 📈 Dashboard Details

### 1. HQ Admin Dashboard

**Who**: Super administrators with access to all companies

**Key Metrics**:
- Total companies count
- Global job orders & candidates
- Deployment rates
- Revenue by country
- Consolidated financials (AR/AP)

**Features**:
- Company comparison view
- Revenue by country breakdown
- Recent activities across all companies
- YTD revenue tracking

**Response Example**:
```json
{
  "role": "HQ_ADMIN",
  "summary": {
    "total_companies": 5,
    "total_job_orders": 45,
    "total_candidates": 230,
    "deployed_candidates": 180,
    "deployment_rate": "78.3%"
  },
  "financial": {
    "revenue_ytd": 1250000.00,
    "total_ar": 350000.00,
    "total_ap": 125000.00,
    "revenue_by_country": [...]
  },
  "companies": [...],
  "recent_activities": [...]
}
```

---

### 2. Country Manager Dashboard

**Who**: Managers overseeing a specific country operation

**Key Metrics**:
- Branch statistics
- Active job orders
- Candidate pipeline by stage
- Monthly & YTD revenue
- Outstanding AR/AP

**Features**:
- Candidate pipeline visualization
- Top employers ranking
- Branch performance comparison
- Pending approvals count

**Response Example**:
```json
{
  "role": "COUNTRY_MANAGER",
  "company": {
    "name": "Mahad Manpower Qatar",
    "code": "QA",
    "country": "Qatar"
  },
  "summary": {
    "total_branches": 2,
    "active_job_orders": 12,
    "total_candidates": 85,
    "deployed_candidates": 45
  },
  "financial": {
    "revenue_mtd": 125000.00,
    "revenue_ytd": 850000.00,
    "ar_outstanding": 95000.00,
    "ap_outstanding": 35000.00,
    "currency": "QAR"
  },
  "candidate_pipeline": {...},
  "top_employers": [...]
}
```

---

### 3. Finance Manager Dashboard

**Who**: Finance leaders managing AR, AP, and cash flow

**Key Metrics**:
- Total AR & AP outstanding
- Overdue amounts
- AR aging analysis
- Monthly cash flow (receipts vs payments)
- Pending approvals

**Features**:
- AR aging breakdown (Current, 1-30, 31-60, 61-90, 90+ days)
- Cash flow analysis
- Recent receipts & payments
- Payments due soon alert

**Response Example**:
```json
{
  "role": "FINANCE_MANAGER",
  "ar_summary": {
    "total": 95000.00,
    "overdue": 25000.00,
    "current": 70000.00,
    "aging": {
      "current": 70000.00,
      "1_30_days": 15000.00,
      "31_60_days": 7000.00,
      "61_90_days": 2000.00,
      "over_90_days": 1000.00
    }
  },
  "ap_summary": {
    "total": 35000.00,
    "overdue": 5000.00,
    "current": 30000.00
  },
  "cash_flow": {
    "receipts_mtd": 125000.00,
    "payments_mtd": 85000.00,
    "net_cash_flow": 40000.00
  },
  "pending_actions": {...}
}
```

---

### 4. Accountant Dashboard

**Who**: Day-to-day accounting staff

**Key Metrics**:
- Today's tasks (invoices to send, bills to process)
- Draft invoices & bills
- Unprocessed candidate costs
- Payments due today

**Features**:
- Task-focused view
- Recent invoices & bills
- Quick action items
- Work queue management

**Response Example**:
```json
{
  "role": "ACCOUNTANT",
  "today_tasks": {
    "invoices_to_send": 3,
    "bills_to_process": 5,
    "payments_due": 2,
    "unprocessed_costs": 12
  },
  "quick_stats": {
    "draft_invoices": 8,
    "draft_bills": 6
  },
  "recent_invoices": [...],
  "recent_bills": [...]
}
```

---

### 5. Branch User Dashboard

**Who**: Staff managing candidate recruitment and deployment

**Key Metrics**:
- Candidate pipeline by stage
- Active job orders
- Candidates deployed this month
- Action items by stage

**Features**:
- Candidate stage tracking
- Job order fulfillment status
- Recent candidates list
- Stage-specific action counts

**Response Example**:
```json
{
  "role": "BRANCH_USER",
  "summary": {
    "total_candidates": 85,
    "active_job_orders": 12,
    "deployed_this_month": 8
  },
  "candidate_pipeline": {
    "SOURCING": {"name": "Sourcing", "count": 15},
    "SCREENING": {"name": "Screening", "count": 12},
    "DOCUMENTATION": {"name": "Documentation", "count": 18},
    "VISA": {"name": "Visa Processing", "count": 10},
    "MEDICAL": {"name": "Medical", "count": 8},
    "TICKET": {"name": "Ticket Issued", "count": 5},
    "DEPLOYED": {"name": "Deployed", "count": 15},
    "INVOICED": {"name": "Invoiced", "count": 2}
  },
  "action_required": {
    "needs_documentation": 18,
    "needs_visa": 10,
    "needs_medical": 8
  },
  "active_job_orders": [...]
}
```

---

### 6. Auditor Dashboard

**Who**: Auditors with read-only access for compliance

**Key Metrics**:
- System-wide statistics
- Transaction volume (all types)
- Compliance checks
- Company-wise summary

**Features**:
- All-company overview
- Recent login activity
- Unposted transaction alerts
- Transaction volume tracking

**Response Example**:
```json
{
  "role": "AUDITOR",
  "system_overview": {
    "total_companies": 5,
    "total_users": 48,
    "active_job_orders": 45,
    "total_candidates": 230
  },
  "transaction_volume": {
    "invoices_mtd": 85,
    "bills_mtd": 120,
    "receipts_mtd": 65,
    "payments_mtd": 95
  },
  "compliance": {
    "unposted_invoices": 15,
    "unposted_bills": 12
  },
  "company_summary": [...],
  "recent_logins": [...]
}
```

---

## 🚀 Setup Instructions

### 1. Create Dashboard App

```bash
mkdir dashboards
touch dashboards/__init__.py
touch dashboards/apps.py
touch dashboards/views.py
touch dashboards/urls.py
```

### 2. Update Settings

Add to `INSTALLED_APPS` in `config/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'dashboards',
]
```

### 3. Include URLs

Already done in main `config/urls.py`:

```python
path('api/dashboard/', include('dashboards.urls')),
```

### 4. Test Dashboards

```bash
# Start server
python manage.py runserver

# Test with authentication token
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/dashboard/
```

---

## 💡 Usage Examples

### Frontend Integration (React/Vue)

```javascript
// Fetch dashboard data
const fetchDashboard = async () => {
  const response = await fetch('/api/dashboard/', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  return data;
};

// Use in component
useEffect(() => {
  fetchDashboard().then(dashboardData => {
    setDashboard(dashboardData);
  });
}, []);
```

### Role-Based Rendering

```javascript
const Dashboard = ({ user, data }) => {
  switch(user.role) {
    case 'HQ_ADMIN':
      return <HQAdminDashboard data={data} />;
    case 'COUNTRY_MANAGER':
      return <CountryManagerDashboard data={data} />;
    case 'FINANCE_MANAGER':
      return <FinanceManagerDashboard data={data} />;
    // ... other roles
    default:
      return <DefaultDashboard />;
  }
};
```

---

## 🎨 Dashboard Features Summary

| Role | Key Focus | Primary Metrics | Actions |
|------|-----------|----------------|---------|
| **HQ Admin** | Global oversight | Revenue, deployment rates | Company management |
| **Country Manager** | Company operations | Job orders, candidates | Branch oversight |
| **Finance Manager** | Financial health | AR/AP, cash flow | Payment approvals |
| **Accountant** | Daily transactions | Tasks, drafts | Invoice/bill processing |
| **Branch User** | Candidate pipeline | Stage tracking | Candidate management |
| **Auditor** | Compliance | Transaction volume | Audit trails |

---

## 🔒 Security

- All endpoints require authentication
- Role-based access control enforced
- Users only see data for their assigned company (except HQ Admin)
- Auditors have read-only access

---

## 📝 Next Steps

1. **Test all dashboards** with different user roles
2. **Create frontend components** for each dashboard
3. **Add charts/graphs** for visual analytics
4. **Implement real-time updates** with WebSockets
5. **Add export functionality** for reports

---

## 🎉 Complete!

Your Mahad Group Accounting Suite now has:
- ✅ 6 Role-specific dashboards
- ✅ Real-time KPIs and metrics
- ✅ Financial analytics (AR aging, cash flow)
- ✅ Candidate pipeline tracking
- ✅ Audit and compliance views
- ✅ Task management for accountants

Ready for frontend integration! 🚀