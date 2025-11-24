from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.serializers import UserSerializer


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

