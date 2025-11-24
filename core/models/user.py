from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based authentication for the procure-to-pay system.
    
    Roles:
    - STAFF: Can create purchase requests and submit receipts
    - APPROVER_L1: Level 1 approver (first approval level)
    - APPROVER_L2: Level 2 approver (second approval level)
    - FINANCE: Can view approved requests and financial reports
    """
    
    class Role(models.TextChoices):
        STAFF = 'staff', 'Staff'
        APPROVER_L1 = 'approver_l1', 'Approver Level 1'
        APPROVER_L2 = 'approver_l2', 'Approver Level 2'
        FINANCE = 'finance', 'Finance'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF,
        help_text='User role determines access permissions'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text='Department or division of the user'
    )
    
    class Meta:
        ordering = ['username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def is_approver(self):
        """Check if user has approval privileges"""
        return self.role in [self.Role.APPROVER_L1, self.Role.APPROVER_L2]
    
    def get_approval_level(self):
        """
        Get the approval level of the user.
        
        Returns:
            int: 1 for Level 1 approver, 2 for Level 2 approver, None otherwise
        """
        if self.role == self.Role.APPROVER_L1:
            return 1
        elif self.role == self.Role.APPROVER_L2:
            return 2
        return None
    
    def can_approve_request(self, purchase_request):
        """
        Check if user can approve a specific purchase request.
        
        Args:
            purchase_request: PurchaseRequest instance
            
        Returns:
            bool: True if user can approve, False otherwise
        """
        if not self.is_approver():
            return False
        
        if purchase_request.status != 'pending':
            return False
        
        level = self.get_approval_level()
        # Check if there's a pending approval for this user's level
        return purchase_request.approvals.filter(
            level=level,
            status='pending'
        ).exists()


