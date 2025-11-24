from django.core.management.base import BaseCommand
from core.models import User


class Command(BaseCommand):
    help = 'Create test users with different roles for development and testing'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Creating test users...'))
        
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@procure.test',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role='staff'
            )
            self.stdout.write(self.style.SUCCESS('✓ Created superuser: admin / admin123'))
        else:
            self.stdout.write(self.style.WARNING('✗ Superuser "admin" already exists'))
        
        # Create staff users
        staff_users = [
            {
                'username': 'staff1',
                'email': 'staff1@procure.test',
                'password': 'staff123',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'staff',
                'department': 'IT'
            },
            {
                'username': 'staff2',
                'email': 'staff2@procure.test',
                'password': 'staff123',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'role': 'staff',
                'department': 'Marketing'
            },
        ]
        
        for user_data in staff_users:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created staff user: {user_data["username"]} / {user_data["password"]}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ User "{user_data["username"]}" already exists')
                )
        
        # Create Level 1 approvers
        l1_approvers = [
            {
                'username': 'approver_l1',
                'email': 'approver.l1@procure.test',
                'password': 'approver123',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'role': 'approver_l1',
                'department': 'Management'
            },
        ]
        
        for user_data in l1_approvers:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created L1 approver: {user_data["username"]} / {user_data["password"]}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ User "{user_data["username"]}" already exists')
                )
        
        # Create Level 2 approvers
        l2_approvers = [
            {
                'username': 'approver_l2',
                'email': 'approver.l2@procure.test',
                'password': 'approver123',
                'first_name': 'Bob',
                'last_name': 'Williams',
                'role': 'approver_l2',
                'department': 'Executive'
            },
        ]
        
        for user_data in l2_approvers:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created L2 approver: {user_data["username"]} / {user_data["password"]}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ User "{user_data["username"]}" already exists')
                )
        
        # Create finance users
        finance_users = [
            {
                'username': 'finance',
                'email': 'finance@procure.test',
                'password': 'finance123',
                'first_name': 'Carol',
                'last_name': 'Davis',
                'role': 'finance',
                'department': 'Finance'
            },
        ]
        
        for user_data in finance_users:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created finance user: {user_data["username"]} / {user_data["password"]}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ User "{user_data["username"]}" already exists')
                )
        
        self.stdout.write(self.style.SUCCESS('\n=== Test Users Summary ==='))
        self.stdout.write('Role: Username / Password')
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Staff: staff1 / staff123')
        self.stdout.write('Staff: staff2 / staff123')
        self.stdout.write('L1 Approver: approver_l1 / approver123')
        self.stdout.write('L2 Approver: approver_l2 / approver123')
        self.stdout.write('Finance: finance / finance123')
        self.stdout.write(self.style.SUCCESS('=========================\n'))




