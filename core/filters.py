import django_filters
from django.db import models
from core.models import PurchaseRequest


class PurchaseRequestFilter(django_filters.FilterSet):
    """Advanced filtering for purchase requests"""
    
    # Status filter
    status = django_filters.ChoiceFilter(choices=PurchaseRequest.Status.choices)
    
    # Search in title and description
    search = django_filters.CharFilter(method='filter_search')
    
    # Date range filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Amount range filters
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    # Created by filter
    created_by = django_filters.NumberFilter(field_name='created_by')
    
    class Meta:
        model = PurchaseRequest
        fields = ['status', 'created_by']
    
    def filter_search(self, queryset, name, value):
        """Search in title and description fields"""
        if value:
            return queryset.filter(
                models.Q(title__icontains=value) |
                models.Q(description__icontains=value)
            )
        return queryset

