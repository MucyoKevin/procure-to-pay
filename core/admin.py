from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PurchaseRequest, Approval


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""
    list_display = ['username', 'email', 'role', 'department', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {
            'fields': ('role', 'department')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {
            'fields': ('role', 'department')
        }),
    )


class ApprovalInline(admin.TabularInline):
    """Inline admin for Approval model"""
    model = Approval
    extra = 0
    readonly_fields = ['reviewed_at']
    fields = ['level', 'approver', 'status', 'comments', 'reviewed_at']


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    """Admin interface for PurchaseRequest model"""
    list_display = ['title', 'created_by', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [ApprovalInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'amount', 'status', 'created_by')
        }),
        ('Documents', {
            'fields': ('proforma', 'proforma_metadata', 'purchase_order', 'po_metadata', 'receipt', 'receipt_validation'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    """Admin interface for Approval model"""
    list_display = ['purchase_request', 'level', 'approver', 'status', 'reviewed_at']
    list_filter = ['status', 'level', 'reviewed_at']
    search_fields = ['purchase_request__title', 'approver__username', 'comments']
    readonly_fields = ['created_at', 'reviewed_at']
    
    fieldsets = (
        ('Approval Information', {
            'fields': ('purchase_request', 'level', 'approver', 'status')
        }),
        ('Review Details', {
            'fields': ('comments', 'reviewed_at', 'created_at')
        }),
    )
