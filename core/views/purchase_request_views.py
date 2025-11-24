from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from core.models import PurchaseRequest
from core.filters import PurchaseRequestFilter
from core.serializers import (
    PurchaseRequestSerializer,
    PurchaseRequestListSerializer,
    PurchaseRequestCreateSerializer,
    PurchaseRequestUpdateSerializer,
    ApprovalActionSerializer,
    ReceiptUploadSerializer
)
from core.services import ApprovalService, DocumentService
from core.permissions import (
    IsStaff,
    IsApprover,
    IsFinance,
    CanModifyRequest,
    CanViewRequest,
    CanApproveRequest,
    CanSubmitReceipt
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class PurchaseRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase requests with role-based access control.
    
    Endpoints:
    - list: Get list of purchase requests (filtered by role)
    - create: Create new purchase request (staff only)
    - retrieve: Get single purchase request details
    - update/partial_update: Update purchase request (owner only, if pending)
    - destroy: Delete purchase request (not implemented for audit purposes)
    - approve: Approve a purchase request (approvers only)
    - reject: Reject a purchase request (approvers only)
    - submit_receipt: Submit receipt for approved request (staff only)
    - my_requests: Get current user's purchase requests
    - pending_approvals: Get requests pending approval at user's level
    """
    
    queryset = PurchaseRequest.objects.all()
    serializer_class = PurchaseRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PurchaseRequestFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'amount', 'status', 'updated_at']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """
        Filter queryset based on user role.
        
        - Staff: See only their own requests
        - Approvers: See requests pending at their level (for list), all pending requests (for detail actions)
        - Finance: See all approved requests
        - Superuser: See everything
        """
        user = self.request.user
        
        # Superusers see everything
        if user.is_superuser:
            return PurchaseRequest.objects.all()
        
        # Staff users see only their own requests
        if user.role == 'staff':
            return PurchaseRequest.objects.filter(created_by=user)
        
        # Approvers see requests pending at their level
        elif user.is_approver():
            # For approve/reject actions, show all pending requests (permissions will handle access control)
            if self.action in ['approve', 'reject', 'retrieve']:
                return PurchaseRequest.objects.filter(
                    status=PurchaseRequest.Status.PENDING
                )
            
            # For list actions, filter by approval level
            level = user.get_approval_level()
            
            if level == 1:
                # L1 approvers see all pending requests at level 1
                return PurchaseRequest.objects.filter(
                    status=PurchaseRequest.Status.PENDING,
                    approvals__level=1,
                    approvals__status='pending'
                ).distinct()
            
            elif level == 2:
                # L2 approvers see pending requests where L1 is approved
                return PurchaseRequest.objects.filter(
                    status=PurchaseRequest.Status.PENDING,
                    approvals__level=1,
                    approvals__status='approved'
                ).filter(
                    approvals__level=2,
                    approvals__status='pending'
                ).distinct()
        
        # Finance users see all approved requests
        elif user.role == 'finance':
            return PurchaseRequest.objects.filter(
                status=PurchaseRequest.Status.APPROVED
            )
        
        # Default: no access
        return PurchaseRequest.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PurchaseRequestListSerializer
        elif self.action == 'create':
            return PurchaseRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PurchaseRequestUpdateSerializer
        return PurchaseRequestSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action"""
        if self.action == 'create':
            return [IsAuthenticated(), IsStaff()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanModifyRequest()]
        elif self.action in ['approve', 'reject']:
            return [IsAuthenticated(), IsApprover()]
        elif self.action == 'submit_receipt':
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """
        Override create to return full serializer response after creation.
        """
        # Validate input with create serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        request_data = serializer.validated_data
        proforma = request_data.pop('proforma', None)
        
        # Create request with approval records
        pr = ApprovalService.create_request_with_approvals(
            request_data,
            request.user
        )
        
        # Process proforma if provided
        if proforma:
            pr.proforma = proforma
            pr.save()
            
            # Extract metadata from proforma in background (or synchronously for now)
            try:
                metadata = DocumentService.extract_proforma_data(proforma)
                pr.proforma_metadata = metadata
                pr.save()
            except Exception as e:
                # Log error but don't fail the request creation
                print(f"Warning: Failed to extract proforma metadata: {str(e)}")
        
        # Return full serializer response
        response_serializer = PurchaseRequestSerializer(
            pr,
            context={'request': request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        method='patch',
        request_body=ApprovalActionSerializer,
        responses={
            200: PurchaseRequestSerializer,
            400: 'Bad Request',
            403: 'Forbidden'
        }
    )
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsApprover])
    def approve(self, request, pk=None):
        """
        Approve a purchase request at the current user's approval level.
        
        Requires:
        - User must be an approver
        - Request must be pending
        - Approval must be at user's level
        - For L2: L1 must be approved first
        """
        pr = self.get_object()
        
        # Check if user can approve
        if not ApprovalService.can_user_approve(pr, request.user):
            return Response(
                {
                    'detail': 'You do not have permission to approve this request at this time',
                    'required_role': 'approver-level-1' if request.user.get_approval_level() == 1 else 'approver-level-2'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate comments
        serializer = ApprovalActionSerializer(
            data=request.data,
            context={'action': 'approve'}
        )
        serializer.is_valid(raise_exception=True)
        comments = serializer.validated_data.get('comments', '')
        
        try:
            updated_pr = ApprovalService.approve_request(
                pr,
                request.user,
                comments
            )
            
            # Return updated request
            response_serializer = PurchaseRequestSerializer(
                updated_pr,
                context={'request': request}
            )
            return Response(response_serializer.data)
            
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        method='patch',
        request_body=ApprovalActionSerializer,
        responses={
            200: PurchaseRequestSerializer,
            400: 'Bad Request',
            403: 'Forbidden'
        }
    )
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsApprover])
    def reject(self, request, pk=None):
        """
        Reject a purchase request at the current user's approval level.
        
        Requires:
        - User must be an approver
        - Request must be pending
        - Comments are required for rejection
        """
        pr = self.get_object()
        
        # Check if user can reject
        if not ApprovalService.can_user_approve(pr, request.user):
            return Response(
                {
                    'detail': 'You do not have permission to reject this request at this time',
                    'required_role': 'approver-level-1' if request.user.get_approval_level() == 1 else 'approver-level-2'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate comments (required for rejection)
        serializer = ApprovalActionSerializer(
            data=request.data,
            context={'action': 'reject'}
        )
        serializer.is_valid(raise_exception=True)
        comments = serializer.validated_data.get('comments', '')
        
        try:
            updated_pr = ApprovalService.reject_request(
                pr,
                request.user,
                comments
            )
            
            # Return updated request
            response_serializer = PurchaseRequestSerializer(
                updated_pr,
                context={'request': request}
            )
            return Response(response_serializer.data)
            
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        method='post',
        request_body=ReceiptUploadSerializer,
        responses={
            200: PurchaseRequestSerializer,
            400: 'Bad Request',
            403: 'Forbidden'
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStaff])
    def submit_receipt(self, request, pk=None):
        """
        Submit a receipt for validation against the purchase order.
        
        Requires:
        - User must be staff
        - User must be the creator of the request
        - Request must be approved
        - Purchase order must exist
        - Receipt must not already be submitted
        """
        pr = self.get_object()
        
        # Check if receipt can be submitted
        if not pr.can_submit_receipt():
            return Response(
                {'detail': 'Receipt cannot be submitted for this request. Request must be approved and purchase order must exist.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is the creator
        if pr.created_by != request.user:
            return Response(
                {
                    'detail': 'You can only submit receipts for your own requests',
                    'required_role': 'staff'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate receipt file
        serializer = ReceiptUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt = serializer.validated_data['receipt']
        
        # Save receipt
        pr.receipt = receipt
        pr.save()
        
        # Validate receipt against PO
        try:
            validation = DocumentService.validate_receipt(pr, receipt)
            pr.receipt_validation = validation
            pr.save()
        except Exception as e:
            # Log error but keep the receipt
            print(f"Warning: Failed to validate receipt: {str(e)}")
            pr.receipt_validation = {
                'error': f'Validation failed: {str(e)}',
                'is_valid': None
            }
            pr.save()
        
        # Return updated request
        response_serializer = PurchaseRequestSerializer(
            pr,
            context={'request': request}
        )
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_requests(self, request):
        """
        Get all purchase requests created by the current user.
        """
        if request.user.role != 'staff':
            return Response(
                {
                    'detail': 'Only staff users can view their requests',
                    'required_role': 'staff'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = PurchaseRequest.objects.filter(created_by=request.user)
        
        # Apply filters using the filter class
        queryset = self.filter_queryset(queryset)
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PurchaseRequestListSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = PurchaseRequestListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsApprover])
    def pending_approvals(self, request):
        """
        Get all purchase requests pending approval at the user's level.
        """
        queryset = ApprovalService.get_pending_approvals_for_user(request.user)
        
        # Apply filters
        queryset = self.filter_queryset(queryset)
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PurchaseRequestListSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = PurchaseRequestListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsFinance])
    def approved_requests(self, request):
        """
        Get all approved purchase requests (Finance view).
        """
        queryset = PurchaseRequest.objects.filter(
            status=PurchaseRequest.Status.APPROVED
        )
        
        # Apply filters
        queryset = self.filter_queryset(queryset)
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PurchaseRequestListSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = PurchaseRequestListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        responses={
            200: 'File download',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def download_po(self, request, pk=None):
        """
        Download the purchase order PDF for an approved request.
        """
        pr = self.get_object()
        
        if not pr.purchase_order:
            return Response(
                {'detail': 'Purchase order not available for this request'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            return FileResponse(
                pr.purchase_order.open('rb'),
                content_type='application/pdf',
                filename=pr.purchase_order.name.split('/')[-1]
            )
        except Exception as e:
            return Response(
                {'detail': f'Error downloading file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='get',
        responses={
            200: 'File download',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def download_proforma(self, request, pk=None):
        """
        Download the proforma invoice for a request.
        """
        pr = self.get_object()
        
        if not pr.proforma:
            return Response(
                {'detail': 'Proforma invoice not available for this request'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            return FileResponse(
                pr.proforma.open('rb'),
                content_type='application/pdf',
                filename=pr.proforma.name.split('/')[-1]
            )
        except Exception as e:
            return Response(
                {'detail': f'Error downloading file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='get',
        responses={
            200: 'File download',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def download_receipt(self, request, pk=None):
        """
        Download the receipt for a request.
        """
        pr = self.get_object()
        
        if not pr.receipt:
            return Response(
                {'detail': 'Receipt not available for this request'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            return FileResponse(
                pr.receipt.open('rb'),
                content_type='application/pdf',
                filename=pr.receipt.name.split('/')[-1]
            )
        except Exception as e:
            return Response(
                {'detail': f'Error downloading file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='get',
        responses={
            200: 'Approval history',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def approval_history(self, request, pk=None):
        """
        Get approval history for a purchase request.
        Returns just the approvals array.
        """
        pr = self.get_object()
        
        from core.serializers import ApprovalSerializer
        
        approvals = pr.approvals.all().order_by('level')
        serializer = ApprovalSerializer(approvals, many=True)
        return Response(serializer.data)



