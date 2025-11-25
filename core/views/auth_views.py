from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from core.serializers import UserSerializer, UserRegistrationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Get current authenticated user information.
    
    Returns:
        {
            "id": 1,
            "username": "staff1",
            "email": "staff1@example.com",
            "role": "staff",
            "role_display": "Staff",
            "full_name": "Staff User",
            "department": "IT",
            "first_name": "Staff",
            "last_name": "User"
        }
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user with role selection.
    
    Request body:
        {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
            "role": "staff",  # Options: staff, approver_l1, approver_l2, finance
            "first_name": "John",  # Optional
            "last_name": "Doe",  # Optional
            "department": "IT"  # Optional
        }
    
    Returns:
        201 Created:
        {
            "id": 5,
            "username": "newuser",
            "email": "newuser@example.com",
            "role": "staff",
            "first_name": "John",
            "last_name": "Doe",
            "department": "IT",
            "message": "User registered successfully"
        }
        
        400 Bad Request:
        {
            "username": ["A user with this username already exists."],
            "email": ["A user with this email already exists."],
            "password_confirm": ["Passwords do not match."]
        }
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Return user data without password
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'department': user.department,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

