from rest_framework import serializers
from core.models import PurchaseRequest, Approval, User


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information serializer"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'role', 'department']
        read_only_fields = ['id', 'username', 'email', 'role']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ApprovalSerializer(serializers.ModelSerializer):
    """Serializer for approval records"""
    approver_name = serializers.SerializerMethodField()
    approver_info = UserBasicSerializer(source='approver', read_only=True)
    level_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Approval
        fields = [
            'id',
            'level',
            'level_display',
            'status',
            'status_display',
            'approver',
            'approver_name',
            'approver_info',
            'comments',
            'reviewed_at',
            'created_at',
            'is_overdue'
        ]
        read_only_fields = ['id', 'level', 'approver', 'reviewed_at', 'created_at']
    
    def get_approver_name(self, obj):
        if obj.approver:
            return obj.approver.get_full_name() or obj.approver.username
        return 'Pending Assignment'
    
    def get_level_display(self, obj):
        return f"Level {obj.level}"
    
    def get_is_overdue(self, obj):
        return obj.is_overdue(days=7)


class PurchaseRequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_approval_level = serializers.SerializerMethodField()
    approval_status_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseRequest
        fields = [
            'id',
            'title',
            'amount',
            'status',
            'status_display',
            'created_by',
            'created_by_name',
            'current_approval_level',
            'approval_status_summary',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_by', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username
    
    def get_current_approval_level(self, obj):
        return obj.get_current_approval_level()
    
    def get_approval_status_summary(self, obj):
        """Return a summary like 'Level 1: Approved, Level 2: Pending'"""
        approvals = obj.approvals.all().order_by('level')
        summary = []
        for approval in approvals:
            summary.append(f"L{approval.level}: {approval.get_status_display()}")
        return ", ".join(summary)


class PurchaseRequestSerializer(serializers.ModelSerializer):
    """Detailed serializer for purchase requests"""
    approvals = ApprovalSerializer(many=True, read_only=True)
    created_by_info = UserBasicSerializer(source='created_by', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_submit_receipt = serializers.SerializerMethodField()
    is_fully_approved = serializers.SerializerMethodField()
    current_approval_level = serializers.SerializerMethodField()
    
    # File URLs
    proforma_url = serializers.SerializerMethodField()
    purchase_order_url = serializers.SerializerMethodField()
    receipt_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseRequest
        fields = [
            'id',
            'title',
            'description',
            'amount',
            'status',
            'status_display',
            'created_by',
            'created_by_name',
            'created_by_info',
            'approvals',
            'proforma',
            'proforma_url',
            'proforma_metadata',
            'purchase_order',
            'purchase_order_url',
            'po_metadata',
            'receipt',
            'receipt_url',
            'receipt_validation',
            'created_at',
            'updated_at',
            'can_edit',
            'can_submit_receipt',
            'is_fully_approved',
            'current_approval_level'
        ]
        read_only_fields = [
            'id',
            'status',
            'created_by',
            'purchase_order',
            'po_metadata',
            'receipt_validation',
            'created_at',
            'updated_at'
        ]
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username
    
    def get_can_edit(self, obj):
        return obj.can_edit()
    
    def get_can_submit_receipt(self, obj):
        return obj.can_submit_receipt()
    
    def get_is_fully_approved(self, obj):
        return obj.is_fully_approved()
    
    def get_current_approval_level(self, obj):
        return obj.get_current_approval_level()
    
    def get_proforma_url(self, obj):
        # Check if proforma field has a file associated
        if obj.proforma and obj.proforma.name:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.proforma.url)
            return obj.proforma.url
        return None
    
    def get_purchase_order_url(self, obj):
        # Check if purchase_order field has a file associated
        if obj.purchase_order and obj.purchase_order.name:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.purchase_order.url)
            return obj.purchase_order.url
        return None
    
    def get_receipt_url(self, obj):
        # Check if receipt field has a file associated
        if obj.receipt and obj.receipt.name:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.receipt.url)
            return obj.receipt.url
        return None


class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new purchase requests"""
    
    class Meta:
        model = PurchaseRequest
        fields = ['title', 'description', 'amount', 'proforma']
    
    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate_proforma(self, value):
        """Validate proforma file"""
        if value:
            # Check file size (10MB max)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("File size must not exceed 10MB")
            
            # Check file extension
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
            ext = value.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
                )
        
        return value


class PurchaseRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating purchase requests (only for pending requests)"""
    
    class Meta:
        model = PurchaseRequest
        fields = ['title', 'description', 'amount', 'proforma']
    
    def validate(self, data):
        """Ensure request can be updated"""
        instance = self.instance
        if not instance.can_edit():
            raise serializers.ValidationError(
                "This request cannot be edited as it has been processed or approved"
            )
        return data
    
    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


class ApprovalActionSerializer(serializers.Serializer):
    """Serializer for approval/rejection actions"""
    comments = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text="Comments or notes about the approval/rejection"
    )
    
    def validate_comments(self, value):
        """Require comments for rejection"""
        action = self.context.get('action')
        if action == 'reject' and not value:
            raise serializers.ValidationError(
                "Comments are required when rejecting a request"
            )
        return value


class ReceiptUploadSerializer(serializers.Serializer):
    """Serializer for receipt upload"""
    receipt = serializers.FileField(
        help_text="Receipt file (PDF or image)"
    )
    
    def validate_receipt(self, value):
        """Validate receipt file"""
        # Check file size (10MB max)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 10MB")
        
        # Check file extension
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value



