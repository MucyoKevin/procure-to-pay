from django.db import models
from django.conf import settings
import uuid


class PurchaseRequest(models.Model):
    """
    Purchase Request model representing a request for purchasing goods/services.
    
    Workflow:
    1. Staff creates request with proforma invoice
    2. L1 Approver reviews and approves/rejects
    3. L2 Approver reviews and approves/rejects (if L1 approved)
    4. If fully approved, PO is generated
    5. Staff uploads receipt for validation
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the purchase request'
    )
    
    title = models.CharField(
        max_length=255,
        help_text='Brief title describing the purchase'
    )
    
    description = models.TextField(
        help_text='Detailed description of items/services to be purchased'
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Total amount of the purchase request'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text='Current status of the purchase request'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_requests',
        help_text='User who created this request'
    )
    
    # Document fields
    proforma = models.FileField(
        upload_to='proformas/%Y/%m/',
        null=True,
        blank=True,
        help_text='Proforma invoice document (PDF/Image)'
    )
    
    proforma_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Extracted metadata from proforma invoice'
    )
    
    purchase_order = models.FileField(
        upload_to='purchase_orders/%Y/%m/',
        null=True,
        blank=True,
        help_text='Generated purchase order document'
    )
    
    po_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Purchase order metadata'
    )
    
    receipt = models.FileField(
        upload_to='receipts/%Y/%m/',
        null=True,
        blank=True,
        help_text='Receipt/invoice document uploaded after purchase'
    )
    
    receipt_validation = models.JSONField(
        default=dict,
        blank=True,
        help_text='Validation results comparing receipt with PO'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Date and time when request was created'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Date and time of last update'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_by', 'status']),
        ]
        verbose_name = 'Purchase Request'
        verbose_name_plural = 'Purchase Requests'
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()} (${self.amount})"
    
    def is_fully_approved(self):
        """Check if all approval levels have approved"""
        return all(
            approval.status == 'approved'
            for approval in self.approvals.all()
        )
    
    def is_rejected(self):
        """Check if any approval level has rejected"""
        return any(
            approval.status == 'rejected'
            for approval in self.approvals.all()
        )
    
    def get_current_approval_level(self):
        """
        Get the current approval level that needs action.
        
        Returns:
            int or None: Approval level number or None if complete
        """
        for approval in self.approvals.order_by('level'):
            if approval.status == 'pending':
                return approval.level
        return None
    
    def can_edit(self):
        """Check if request can be edited"""
        return self.status == self.Status.PENDING and not self.approvals.filter(
            status__in=['approved', 'rejected']
        ).exists()
    
    def can_submit_receipt(self):
        """Check if receipt can be submitted"""
        return self.status == self.Status.APPROVED and self.purchase_order and not self.receipt



