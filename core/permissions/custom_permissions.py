from rest_framework import permissions


class IsStaff(permissions.BasePermission):
    """
    Permission class to check if user has Staff role.
    
    Staff users can:
    - Create purchase requests
    - View their own purchase requests
    - Submit receipts for approved requests
    """
    
    message = "You must have Staff role to perform this action"
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'staff'
        )


class IsApprover(permissions.BasePermission):
    """
    Permission class to check if user has Approver role (L1 or L2).
    
    Approvers can:
    - View purchase requests pending approval at their level
    - Approve or reject requests at their level
    """
    
    message = "You must have Approver role to perform this action"
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_approver()
        )


class IsFinance(permissions.BasePermission):
    """
    Permission class to check if user has Finance role.
    
    Finance users can:
    - View all approved purchase requests
    - View financial reports and analytics
    - Access receipt validation data
    """
    
    message = "You must have Finance role to perform this action"
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'finance'
        )


class CanModifyRequest(permissions.BasePermission):
    """
    Permission class to check if user can modify a specific purchase request.
    
    A purchase request can be modified only if:
    - User is the creator of the request
    - Request is still in pending status
    - No approvals have been processed yet
    """
    
    message = "You can only modify your own pending requests that haven't been processed"
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the creator
        if obj.created_by != request.user:
            return False
        
        # Can only modify if request can be edited
        return obj.can_edit()


class CanViewRequest(permissions.BasePermission):
    """
    Permission class to control who can view a purchase request.
    
    Viewing rules:
    - Staff: Can view only their own requests
    - Approvers: Can view requests pending at their approval level
    - Finance: Can view all approved requests
    """
    
    message = "You don't have permission to view this request"
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Staff can view their own requests
        if user.role == 'staff':
            return obj.created_by == user
        
        # Approvers can view requests pending at their level
        if user.is_approver():
            level = user.get_approval_level()
            
            # Can view if there's a pending approval at their level
            pending_at_level = obj.approvals.filter(
                level=level,
                status='pending'
            ).exists()
            
            if pending_at_level:
                # For L2 approvers, L1 must be approved
                if level == 2:
                    l1_approved = obj.approvals.filter(
                        level=1,
                        status='approved'
                    ).exists()
                    return l1_approved
                return True
            
            # Approvers can also view requests they've already reviewed
            reviewed = obj.approvals.filter(
                level=level,
                approver=user
            ).exists()
            if reviewed:
                return True
        
        # Finance can view all approved requests
        if user.role == 'finance':
            return obj.status == 'approved'
        
        return False


class CanApproveRequest(permissions.BasePermission):
    """
    Permission class to check if user can approve a specific purchase request.
    
    Approval rules:
    - User must be an approver
    - Request must be pending
    - User's approval level must match the current pending level
    - For L2, L1 must be approved first
    """
    
    message = "You cannot approve this request at this time"
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Must be an approver
        if not user.is_approver():
            return False
        
        # Request must be pending
        if obj.status != 'pending':
            return False
        
        level = user.get_approval_level()
        
        # Check if there's a pending approval at user's level
        try:
            approval = obj.approvals.get(level=level)
            
            if approval.status != 'pending':
                return False
            
            # For Level 2, check if Level 1 is approved
            if level == 2:
                l1_approval = obj.approvals.get(level=1)
                if l1_approval.status != 'approved':
                    return False
            
            return True
            
        except:
            return False


class CanSubmitReceipt(permissions.BasePermission):
    """
    Permission class to check if user can submit a receipt for a purchase request.
    
    Receipt submission rules:
    - User must be staff
    - User must be the creator of the request
    - Request must be approved
    - Purchase order must exist
    - Receipt must not already be submitted
    """
    
    message = "You cannot submit a receipt for this request"
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Must be staff
        if user.role != 'staff':
            return False
        
        # Must be the creator
        if obj.created_by != user:
            return False
        
        # Can submit receipt only if conditions are met
        return obj.can_submit_receipt()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class allowing owners to edit and others to read only.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the owner
        return obj.created_by == request.user


class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    Permission class allowing superusers to edit and others to read only.
    """
    
    def has_permission(self, request, view):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions only for superusers
        return request.user and request.user.is_superuser



