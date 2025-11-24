from django.db import models
from django.conf import settings
from django.utils import timezone


class Approval(models.Model):
    """
    Approval model for multi-level approval workflow.
    
    Each purchase request requires two levels of approval:
    - Level 1: Initial approval by APPROVER_L1
    - Level 2: Final approval by APPROVER_L2
    
    Approvals must be sequential - Level 2 can only approve after Level 1.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    purchase_request = models.ForeignKey(
        'PurchaseRequest',
        on_delete=models.CASCADE,
        related_name='approvals',
        help_text='The purchase request being approved'
    )
    
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='approvals_given',
        null=True,
        blank=True,
        help_text='User who processed this approval (assigned when approved/rejected)'
    )
    
    level = models.IntegerField(
        help_text='Approval level: 1 for L1 approver, 2 for L2 approver'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text='Current status of this approval level'
    )
    
    comments = models.TextField(
        blank=True,
        help_text='Comments or notes from the approver'
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date and time when the approval was reviewed'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Date and time when approval record was created'
    )
    
    class Meta:
        unique_together = ['purchase_request', 'level']
        ordering = ['level', 'created_at']
        verbose_name = 'Approval'
        verbose_name_plural = 'Approvals'
        indexes = [
            models.Index(fields=['purchase_request', 'level']),
            models.Index(fields=['approver', 'status']),
            models.Index(fields=['status', 'level']),
        ]
    
    def __str__(self):
        approver_name = self.approver.get_full_name() if self.approver else 'Unassigned'
        return f"Level {self.level} - {self.get_status_display()} by {approver_name}"
    
    def can_approve(self, user):
        """
        Check if a user can approve at this level.
        
        Args:
            user: User instance
            
        Returns:
            bool: True if user can approve, False otherwise
        """
        # Must be pending
        if self.status != self.Status.PENDING:
            return False
        
        # User must have the correct approval level
        if user.get_approval_level() != self.level:
            return False
        
        # For Level 2, Level 1 must be approved first
        if self.level == 2:
            level_1_approval = self.purchase_request.approvals.filter(level=1).first()
            if not level_1_approval or level_1_approval.status != self.Status.APPROVED:
                return False
        
        return True
    
    def approve(self, user, comments=''):
        """
        Approve this level.
        
        Args:
            user: User performing the approval
            comments: Optional comments
            
        Raises:
            ValueError: If approval conditions are not met
        """
        if not self.can_approve(user):
            raise ValueError("User cannot approve this request at this level")
        
        self.approver = user
        self.status = self.Status.APPROVED
        self.comments = comments
        self.reviewed_at = timezone.now()
        self.save()
    
    def reject(self, user, comments=''):
        """
        Reject this level.
        
        Args:
            user: User performing the rejection
            comments: Optional comments (recommended for rejection)
            
        Raises:
            ValueError: If rejection conditions are not met
        """
        if self.status != self.Status.PENDING:
            raise ValueError("Only pending approvals can be rejected")
        
        if user.get_approval_level() != self.level:
            raise ValueError("User does not have permission to reject at this level")
        
        self.approver = user
        self.status = self.Status.REJECTED
        self.comments = comments
        self.reviewed_at = timezone.now()
        self.save()
    
    def is_overdue(self, days=7):
        """
        Check if this approval is overdue.
        
        Args:
            days: Number of days before considering overdue
            
        Returns:
            bool: True if approval is pending and overdue
        """
        if self.status != self.Status.PENDING:
            return False
        
        age = timezone.now() - self.created_at
        return age.days > days



