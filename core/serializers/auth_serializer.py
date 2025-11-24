from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from core.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes user information in the token payload"""
    
    @classmethod
    def get_token(cls, user):
        """Add custom claims to the token"""
        token = super().get_token(user)
        
        # Add user information to token payload
        token['user_id'] = user.id
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        
        return token
    
    def validate(self, attrs):
        """Add user info to response"""
        data = super().validate(attrs)
        
        # Include user information in response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'full_name': self.user.get_full_name() or self.user.username,
        }
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'role',
            'role_display',
            'department',
            'first_name',
            'last_name',
        ]
        read_only_fields = ['id', 'username', 'email', 'role']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

