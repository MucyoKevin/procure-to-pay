from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import User, PurchaseRequest
from core.services import ApprovalService
from decimal import Decimal
import io


class Command(BaseCommand):
    help = 'Create test purchase requests for development and testing'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Creating test purchase requests...'))
        
        # Get or create test users
        try:
            staff1 = User.objects.get(username='staff1')
            staff2 = User.objects.get(username='staff2')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Test users not found. Please run: python manage.py create_test_users')
            )
            return
        
        # Test purchase requests data
        test_requests = [
            {
                'user': staff1,
                'title': 'Office Supplies - Q1 2024',
                'description': 'Purchase of office supplies including printer paper, pens, folders, and sticky notes for Q1 2024.',
                'amount': Decimal('1250.00')
            },
            {
                'user': staff1,
                'title': 'Software Licenses - Adobe Creative Suite',
                'description': 'Annual renewal of Adobe Creative Suite licenses for the marketing team (5 licenses).',
                'amount': Decimal('2999.95')
            },
            {
                'user': staff2,
                'title': 'Marketing Materials - Trade Show',
                'description': 'Promotional materials for upcoming trade show: banners, brochures, business cards, and booth supplies.',
                'amount': Decimal('4500.00')
            },
            {
                'user': staff2,
                'title': 'Computer Equipment - IT Department',
                'description': 'Purchase of 3 Dell XPS laptops with accessories for new IT team members.',
                'amount': Decimal('8750.00')
            },
            {
                'user': staff1,
                'title': 'Training Workshop - Project Management',
                'description': 'Registration and materials for Project Management Professional (PMP) certification workshop for 4 team members.',
                'amount': Decimal('5200.00')
            },
        ]
        
        created_count = 0
        
        for req_data in test_requests:
            # Check if similar request already exists
            existing = PurchaseRequest.objects.filter(
                title=req_data['title'],
                created_by=req_data['user']
            ).exists()
            
            if not existing:
                # Create the request with approval workflow
                pr = ApprovalService.create_request_with_approvals(
                    {
                        'title': req_data['title'],
                        'description': req_data['description'],
                        'amount': req_data['amount']
                    },
                    req_data['user']
                )
                
                # Create a dummy proforma file
                dummy_proforma = self._create_dummy_proforma(req_data)
                pr.proforma.save(
                    f'proforma_{pr.id}.txt',
                    ContentFile(dummy_proforma.encode('utf-8'))
                )
                
                # Add basic metadata
                pr.proforma_metadata = {
                    'vendor_name': 'Test Vendor Inc.',
                    'vendor_email': 'vendor@test.com',
                    'items': [
                        {
                            'name': req_data['title'],
                            'quantity': 1,
                            'unit_price': float(req_data['amount']),
                            'total': float(req_data['amount'])
                        }
                    ],
                    'total_amount': float(req_data['amount']),
                    'currency': 'USD'
                }
                pr.save()
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created purchase request: {req_data["title"]} (${req_data["amount"]})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ Request "{req_data["title"]}" already exists')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Created {created_count} test purchase request(s)')
        )
        
        # Display summary
        total_requests = PurchaseRequest.objects.count()
        pending = PurchaseRequest.objects.filter(status='pending').count()
        approved = PurchaseRequest.objects.filter(status='approved').count()
        rejected = PurchaseRequest.objects.filter(status='rejected').count()
        
        self.stdout.write(self.style.SUCCESS('\n=== Purchase Requests Summary ==='))
        self.stdout.write(f'Total: {total_requests}')
        self.stdout.write(f'Pending: {pending}')
        self.stdout.write(f'Approved: {approved}')
        self.stdout.write(f'Rejected: {rejected}')
        self.stdout.write(self.style.SUCCESS('=================================\n'))
    
    def _create_dummy_proforma(self, req_data):
        """Create a simple text-based dummy proforma"""
        return f"""
PROFORMA INVOICE
================

Vendor: Test Vendor Inc.
Email: vendor@test.com
Phone: +1-555-0123

Bill To: {req_data['user'].get_full_name()}
Department: {req_data['user'].department}

Date: 2024-01-15
Invoice #: INV-2024-001

ITEM DESCRIPTION                          QTY    UNIT PRICE    TOTAL
------------------------------------------------------------------------
{req_data['title']:40} 1      ${req_data['amount']}     ${req_data['amount']}

                                          SUBTOTAL:  ${req_data['amount']}
                                          TAX (0%):  $0.00
                                          TOTAL:     ${req_data['amount']}

Payment Terms: Net 30
Delivery: 7-10 business days

Thank you for your business!
"""




