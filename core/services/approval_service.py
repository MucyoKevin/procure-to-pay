from django.db import transaction
from django.utils import timezone
from core.models import PurchaseRequest, Approval
from typing import Dict, Any


class ApprovalService:
    """
    Service for managing the approval workflow with transaction safety.
    
    Ensures ACID properties for approval operations and handles concurrency.
    """
    
    @staticmethod
    @transaction.atomic()
    def create_request_with_approvals(request_data: Dict[str, Any], user) -> PurchaseRequest:
        """
        Create a purchase request and initialize the approval workflow.
        
        This creates a purchase request along with two approval records
        (one for each approval level) in a single atomic transaction.
        
        Args:
            request_data: Dictionary containing request fields (title, description, amount)
            user: User creating the request
            
        Returns:
            PurchaseRequest: The created purchase request with approval records
        """
        # Create the purchase request
        purchase_request = PurchaseRequest.objects.create(
            created_by=user,
            **request_data
        )
        
        # Create approval records for both levels
        Approval.objects.create(
            purchase_request=purchase_request,
            level=1,
            approver=None,  # Will be assigned when someone approves
            status=Approval.Status.PENDING
        )
        Approval.objects.create(
            purchase_request=purchase_request,
            level=2,
            approver=None,
            status=Approval.Status.PENDING
        )
        
        return purchase_request
    
    @staticmethod
    @transaction.atomic()
    def approve_request(purchase_request: PurchaseRequest, approver, comments: str = '') -> PurchaseRequest:
        """
        Approve a purchase request at the user's approval level.
        
        Uses select_for_update() to prevent race conditions and ensure
        that approval state is consistent even under concurrent access.
        
        Args:
            purchase_request: The purchase request to approve
            approver: User performing the approval
            comments: Optional approval comments
            
        Returns:
            PurchaseRequest: Updated purchase request
            
        Raises:
            ValueError: If approval conditions are not met
        """
        # Lock the purchase request row to prevent concurrent modifications
        pr = PurchaseRequest.objects.select_for_update().get(
            id=purchase_request.id
        )
        
        # Check if request is already finalized
        if pr.status in [PurchaseRequest.Status.APPROVED, PurchaseRequest.Status.REJECTED]:
            raise ValueError("Request has already been finalized and cannot be modified")
        
        # Get approver's level
        level = approver.get_approval_level()
        if not level:
            raise ValueError("User does not have approval privileges")
        
        # Get and lock the approval record
        try:
            approval = Approval.objects.select_for_update().get(
                purchase_request=pr,
                level=level
            )
        except Approval.DoesNotExist:
            raise ValueError(f"No approval record found for level {level}")
        
        # Check if this approval is still pending
        if approval.status != Approval.Status.PENDING:
            raise ValueError(f"Approval at level {level} has already been processed")
        
        # For Level 2, ensure Level 1 is approved first
        if level == 2:
            level_1_approval = Approval.objects.get(
                purchase_request=pr,
                level=1
            )
            if level_1_approval.status != Approval.Status.APPROVED:
                raise ValueError("Level 1 approval must be completed before Level 2")
        
        # Approve at this level
        approval.approver = approver
        approval.status = Approval.Status.APPROVED
        approval.comments = comments
        approval.reviewed_at = timezone.now()
        approval.save()
        
        # Check if all approvals are complete
        all_approvals = pr.approvals.all()
        if all(a.status == Approval.Status.APPROVED for a in all_approvals):
            pr.status = PurchaseRequest.Status.APPROVED
            pr.save()
            
            # Generate PO if this is the final (Level 2) approval
            if level == 2:
                # Import here to avoid circular dependency
                from .document_service import DocumentService
                try:
                    DocumentService.generate_purchase_order(pr)
                except Exception as e:
                    # Log the error but don't fail the approval
                    print(f"Warning: Failed to generate PO: {str(e)}")
        
        return pr
    
    @staticmethod
    @transaction.atomic()
    def reject_request(purchase_request: PurchaseRequest, approver, comments: str = '') -> PurchaseRequest:
        """
        Reject a purchase request at the user's approval level.
        
        A rejection at any level immediately finalizes the request as rejected.
        
        Args:
            purchase_request: The purchase request to reject
            approver: User performing the rejection
            comments: Rejection reason (strongly recommended)
            
        Returns:
            PurchaseRequest: Updated purchase request
            
        Raises:
            ValueError: If rejection conditions are not met
        """
        # Lock the purchase request row
        pr = PurchaseRequest.objects.select_for_update().get(
            id=purchase_request.id
        )
        
        # Check if request is already finalized
        if pr.status in [PurchaseRequest.Status.APPROVED, PurchaseRequest.Status.REJECTED]:
            raise ValueError("Request has already been finalized and cannot be modified")
        
        # Get approver's level
        level = approver.get_approval_level()
        if not level:
            raise ValueError("User does not have approval privileges")
        
        # Get and lock the approval record
        try:
            approval = Approval.objects.select_for_update().get(
                purchase_request=pr,
                level=level
            )
        except Approval.DoesNotExist:
            raise ValueError(f"No approval record found for level {level}")
        
        # Check if this approval is still pending
        if approval.status != Approval.Status.PENDING:
            raise ValueError(f"Approval at level {level} has already been processed")
        
        # Reject at this level
        approval.approver = approver
        approval.status = Approval.Status.REJECTED
        approval.comments = comments
        approval.reviewed_at = timezone.now()
        approval.save()
        
        # Mark the entire request as rejected
        pr.status = PurchaseRequest.Status.REJECTED
        pr.save()
        
        return pr
    
    @staticmethod
    def get_pending_approvals_for_user(user):
        """
        Get all pending approvals for a specific approver.
        
        Args:
            user: User to get pending approvals for
            
        Returns:
            QuerySet: Purchase requests pending approval at the user's level
        """
        level = user.get_approval_level()
        if not level:
            return PurchaseRequest.objects.none()
        
        # For Level 2 approvers, only show requests where Level 1 is approved
        if level == 2:
            return PurchaseRequest.objects.filter(
                status=PurchaseRequest.Status.PENDING,
                approvals__level=1,
                approvals__status=Approval.Status.APPROVED
            ).filter(
                approvals__level=2,
                approvals__status=Approval.Status.PENDING
            ).distinct()
        else:
            # Level 1 approvers see all pending requests at their level
            return PurchaseRequest.objects.filter(
                status=PurchaseRequest.Status.PENDING,
                approvals__level=level,
                approvals__status=Approval.Status.PENDING
            ).distinct()
    
    @staticmethod
    def can_user_approve(purchase_request: PurchaseRequest, user) -> bool:
        """
        Check if a user can approve a specific purchase request.
        
        Args:
            purchase_request: Purchase request to check
            user: User to check permissions for
            
        Returns:
            bool: True if user can approve, False otherwise
        """
        if not user.is_approver():
            return False
        
        if purchase_request.status != PurchaseRequest.Status.PENDING:
            return False
        
        level = user.get_approval_level()
        
        try:
            approval = Approval.objects.get(
                purchase_request=purchase_request,
                level=level
            )
            
            # For Level 2, check if Level 1 is approved
            if level == 2:
                level_1 = Approval.objects.get(
                    purchase_request=purchase_request,
                    level=1
                )
                if level_1.status != Approval.Status.APPROVED:
                    return False
            
            return approval.status == Approval.Status.PENDING
        except Approval.DoesNotExist:
            return False



