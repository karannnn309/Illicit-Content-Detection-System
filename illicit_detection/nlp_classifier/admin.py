from django.contrib import admin
from .models import UserProfile, ContentSubmission, AdminReview, APIKey, Notification, BillingRecord, Payment

# ========================================
# USER PROFILE ADMIN
# ========================================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'organization', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'organization']
    readonly_fields = ['created_at', 'updated_at']


# ========================================
# CONTENT SUBMISSION ADMIN
# ========================================
@admin.register(ContentSubmission)
class ContentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'content_type', 'status', 'flagged', 'is_from_api', 'created_at']
    list_filter = ['content_type', 'status', 'flagged', 'is_from_api', 'created_at']
    search_fields = ['user__username', 'text_content', 'content_url']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'content_type', 'status', 'flagged')
        }),
        ('Content', {
            'fields': ('text_content', 'file_path', 'content_url')
        }),
        ('Classification Results', {
            'fields': ('classification_result', 'detected_categories', 'confidence_scores')
        }),
        ('API Information', {
            'fields': ('is_from_api', 'api_key')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ========================================
# ADMIN REVIEW ADMIN
# ========================================
@admin.register(AdminReview)
class AdminReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'submission', 'admin', 'decision', 'reviewed_at']
    list_filter = ['decision', 'reviewed_at']
    search_fields = ['admin__username', 'comments', 'submission__id']
    readonly_fields = ['reviewed_at']


# ========================================
# API KEY ADMIN
# ========================================
@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'tier', 'requests_today', 'daily_limit', 'is_active', 'created_at']
    list_filter = ['tier', 'is_active', 'created_at']
    search_fields = ['user__username', 'name', 'key']
    readonly_fields = ['key', 'created_at', 'last_used', 'last_reset']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'key', 'tier', 'is_active')
        }),
        ('Rate Limiting', {
            'fields': ('daily_limit', 'requests_today', 'last_reset')
        }),
        ('Webhook Configuration', {
            'fields': ('webhook_url',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_used')
        }),
    )


# ========================================
# NOTIFICATION ADMIN
# ========================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        ('Related Content', {
            'fields': ('related_submission',)
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )


# ========================================
# BILLING RECORD ADMIN
# ========================================
@admin.register(BillingRecord)
class BillingRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'month', 'total_requests', 'free_requests_used', 'paid_requests', 'amount_charged', 'last_updated']
    list_filter = ['year', 'month', 'last_updated']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'last_updated']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'api_key', 'year', 'month')
        }),
        ('Usage Statistics', {
            'fields': ('total_requests', 'free_requests_used', 'paid_requests')
        }),
        ('Financial Information', {
            'fields': ('cost_per_request', 'amount_charged')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated')
        }),
    )
    
    actions = ['recalculate_charges']
    
    def recalculate_charges(self, request, queryset):
        for record in queryset:
            record.calculate_charges()
        self.message_user(request, f"Recalculated charges for {queryset.count()} billing records.")
    recalculate_charges.short_description = "Recalculate charges for selected records"


# ========================================
# PAYMENT ADMIN
# ========================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'api_key', 'payment_type', 'amount', 'status', 'created_at']
    list_filter = ['payment_type', 'status', 'created_at']
    search_fields = ['user__username', 'api_key__name', 'stripe_payment_intent_id', 'stripe_charge_id']
    readonly_fields = ['created_at', 'stripe_payment_intent_id', 'stripe_charge_id']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'api_key', 'payment_type', 'status')
        }),
        ('Payment Details', {
            'fields': ('amount', 'description')
        }),
        ('Stripe Information', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        # Payments should only be created through the payment flow
        return False
