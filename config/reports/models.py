from django.db import models
from decimal import Decimal
import uuid

from django.utils import timezone


class CandidateReport(models.Model):
	"""Snapshot metrics per candidate for quick reporting and frontend consumption."""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	company_id = models.UUIDField(db_index=True)
	candidate_id = models.UUIDField(db_index=True)
	job_order_id = models.UUIDField(db_index=True, null=True)
	employer_id = models.UUIDField(db_index=True, null=True)

	period_start = models.DateField(blank=True, null=True)
	period_end = models.DateField(blank=True, null=True)

	revenue = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
	cost = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
	profit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
	margin_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))

	currency = models.CharField(max_length=3, default='USD')

	generated_at = models.DateTimeField(default=timezone.now)

	class Meta:
		db_table = 'reports_candidate_report'
		indexes = [
			models.Index(fields=['company_id', 'candidate_id']),
		]

	def __str__(self):
		return f"CandidateReport {self.candidate_id} ({self.company_id}) @ {self.generated_at.isoformat()}"


class JobOrderReport(models.Model):
	"""Snapshot metrics per job order for reporting and leaderboards."""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	company_id = models.UUIDField(db_index=True)
	job_order_id = models.UUIDField(db_index=True)
	employer_id = models.UUIDField(db_index=True, null=True)

	period_start = models.DateField(blank=True, null=True)
	period_end = models.DateField(blank=True, null=True)

	revenue = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
	cost = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
	profit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0.00'))
	avg_margin_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))

	currency = models.CharField(max_length=3, default='USD')
	generated_at = models.DateTimeField(default=timezone.now)

	class Meta:
		db_table = 'reports_joborder_report'
		indexes = [models.Index(fields=['company_id', 'job_order_id']), ]

	def __str__(self):
		return f"JobOrderReport {self.job_order_id} ({self.company_id}) @ {self.generated_at.isoformat()}"
