from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import secrets

# ========================================
# USER PROFILE MODEL
# ========================================
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('user', 'Regular User'),
        ('admin', 'Administrator'),
        ('super_admin', 'Super Administrator'),
        ('api_user', 'API User'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    organization = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


# ========================================
# CONTENT SUBMISSION MODEL
# ========================================
class ContentSubmission(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    ]
    
    STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved - Clean Content'),
        ('rejected', 'Rejected - Illicit Content'),
        ('auto_approved', 'Auto Approved'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='auto_approved')
    
    # Content data
    text_content = models.TextField(blank=True, null=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    content_url = models.URLField(blank=True, null=True)
    
    # Classification results
    classification_result = models.JSONField(blank=True, null=True)
    detected_categories = models.JSONField(default=list, blank=True)
    confidence_scores = models.JSONField(blank=True, null=True)
    
    # Metadata
    flagged = models.BooleanField(default=False)
    is_from_api = models.BooleanField(default=False)
    api_key = models.ForeignKey('APIKey', on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} - {self.content_type} - {self.status}"
    
    class Meta:
        verbose_name = 'Content Submission'
        verbose_name_plural = 'Content Submissions'
        ordering = ['-created_at']


# ========================================
# ADMIN REVIEW MODEL
# ========================================
class AdminReview(models.Model):
    DECISION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    submission = models.OneToOneField(ContentSubmission, on_delete=models.CASCADE, related_name='review')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    comments = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review by {self.admin.username} - {self.decision}"
    
    def save(self, *args, **kwargs):
        # Update the submission status when review is saved
        if self.decision == 'approved':
            self.submission.status = 'approved'
        else:
            self.submission.status = 'rejected'
        self.submission.save()
        
        # Create notification for the user
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.submission.user:
            Notification.objects.create(
                user=self.submission.user,
                title=f"Content Review: {self.decision.title()}",
                message=f"Your {self.submission.content_type} submission has been {self.decision}. {self.comments or ''}",
                notification_type='review_complete',
                related_submission=self.submission
            )
    
    class Meta:
        verbose_name = 'Admin Review'
        verbose_name_plural = 'Admin Reviews'
        ordering = ['-reviewed_at']


# ========================================
# API KEY MODEL
# ========================================
class APIKey(models.Model):
    TIER_CHOICES = [
        ('free', 'Free Tier - 50/day - $0'),
        ('basic', 'Basic Tier - 1000/day - $9.99/month'),
        ('premium', 'Premium Tier - 10000/day - $49.99/month'),
    ]
    
    TIER_PRICES = {
        'free': 0.00,
        'basic': 9.99,
        'premium': 49.99,
    }
    
    TIER_LIMITS = {
        'free': 50,
        'basic': 1000,
        'premium': 10000,
    }
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=64, unique=True, editable=False)
    name = models.CharField(max_length=100, help_text="Name to identify this API key")
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    
    # Rate limiting
    daily_limit = models.IntegerField(default=50)
    requests_today = models.IntegerField(default=0)
    last_reset = models.DateField(auto_now_add=True)
    
    # Payment & Subscription
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_status = models.CharField(max_length=20, default='inactive')  # active, inactive, cancelled
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Webhook configuration
    webhook_url = models.URLField(blank=True, null=True, help_text="URL to notify when content is flagged")
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_urlsafe(48)
        # Update daily limit based on tier
        if self.tier in self.TIER_LIMITS:
            self.daily_limit = self.TIER_LIMITS[self.tier]
        super().save(*args, **kwargs)
    
    def get_tier_price(self):
        """Get the monthly price for current tier"""
        return self.TIER_PRICES.get(self.tier, 0.00)
    
    def increment_usage(self):
        """Increment the usage counter and reset if it's a new day"""
        from datetime import date
        today = date.today()
        if self.last_reset != today:
            self.requests_today = 0
            self.last_reset = today
        self.requests_today += 1
        self.last_used = timezone.now()
        self.save()
    
    def can_make_request(self):
        """Check if the API key can make another request"""
        from datetime import date
        today = date.today()
        if self.last_reset != today:
            return True
        return self.requests_today < self.daily_limit
    
    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.tier})"
    
    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']


# ========================================
# NOTIFICATION MODEL
# ========================================
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('review_complete', 'Review Complete'),
        ('api_limit', 'API Limit Warning'),
        ('billing', 'Billing Notification'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    related_submission = models.ForeignKey(ContentSubmission, on_delete=models.CASCADE, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']


# ========================================
# BILLING RECORD MODEL
# ========================================
class BillingRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_records')
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Billing period
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    
    # Usage statistics
    free_requests_used = models.IntegerField(default=0)
    paid_requests = models.IntegerField(default=0)
    total_requests = models.IntegerField(default=0)
    
    # Financial
    amount_charged = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cost_per_request = models.DecimalField(max_digits=10, decimal_places=4, default=0.01)  # $0.01 per request
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_charges(self):
        """Calculate charges based on usage"""
        if self.paid_requests > 0:
            self.amount_charged = self.paid_requests * self.cost_per_request
        else:
            self.amount_charged = 0.00
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.year}/{self.month:02d} - ${self.amount_charged}"
    
    class Meta:
        verbose_name = 'Billing Record'
        verbose_name_plural = 'Billing Records'
        ordering = ['-year', '-month']
        unique_together = ['user', 'year', 'month']


# ========================================
# PAYMENT MODEL
# ========================================
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('upgrade', 'Upgrade'),
        ('overage', 'API Overage'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Stripe details
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Description
    description = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount} - {self.status}"
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']

