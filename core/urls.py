from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import PurchaseRequestViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'purchase-requests', PurchaseRequestViewSet, basename='purchaserequest')

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
]



