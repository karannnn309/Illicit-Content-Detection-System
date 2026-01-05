"""
Initial Setup Script
Run this after migrations to set up initial data and configurations
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from nlp_classifier.models import UserProfile, APIKey


class Command(BaseCommand):
    help = 'Initial setup for the application'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting initial setup...'))
        
        # Check if admin user exists
        try:
            admin_user = User.objects.get(username='admin')
            self.stdout.write(self.style.WARNING('Admin user already exists'))
            
            # Ensure admin has profile
            profile, created = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={
                    'role': 'admin',
                    'organization': 'System Administration'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Created admin profile'))
            else:
                # Update role if needed
                if profile.role != 'admin':
                    profile.role = 'admin'
                    profile.save()
                    self.stdout.write(self.style.SUCCESS('Updated admin profile role'))
                else:
                    self.stdout.write(self.style.WARNING('Admin profile already exists'))
                    
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Admin user not found. Please run: python manage.py createsuperuser'
            ))
        
        # Create demo user (optional)
        demo_username = 'demouser'
        if not User.objects.filter(username=demo_username).exists():
            demo_user = User.objects.create_user(
                username=demo_username,
                email='demo@example.com',
                password='Demo123456!',
                first_name='Demo',
                last_name='User'
            )
            UserProfile.objects.create(
                user=demo_user,
                role='user',
                organization='Demo Organization'
            )
            self.stdout.write(self.style.SUCCESS(
                f'Created demo user: {demo_username} / Demo123456!'
            ))
        else:
            self.stdout.write(self.style.WARNING('Demo user already exists'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Initial setup complete!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Run server: python manage.py runserver')
        self.stdout.write('2. Visit: http://127.0.0.1:8000/')
        self.stdout.write('3. Login as admin or demouser')
        self.stdout.write('4. Create API keys in Django admin')
