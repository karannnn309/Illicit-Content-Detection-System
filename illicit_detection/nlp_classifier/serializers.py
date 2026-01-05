from rest_framework import serializers
from .models import ContentSubmission, APIKey, AdminReview
from django.contrib.auth.models import User


# ========================================
# API REQUEST SERIALIZERS
# ========================================
class TextClassificationSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, allow_blank=False)
    webhook_url = serializers.URLField(required=False, allow_blank=True)


class ImageClassificationSerializer(serializers.Serializer):
    image_url = serializers.URLField(required=False, allow_blank=True)
    image_file = serializers.ImageField(required=False)
    webhook_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate(self, data):
        if not data.get('image_url') and not data.get('image_file'):
            raise serializers.ValidationError("Either image_url or image_file must be provided.")
        return data


class VideoClassificationSerializer(serializers.Serializer):
    video_url = serializers.URLField(required=False, allow_blank=True)
    video_file = serializers.FileField(required=False)
    frame_skip = serializers.IntegerField(default=50, min_value=1)
    webhook_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate(self, data):
        if not data.get('video_url') and not data.get('video_file'):
            raise serializers.ValidationError("Either video_url or video_file must be provided.")
        return data


# ========================================
# API RESPONSE SERIALIZERS
# ========================================
class ClassificationResponseSerializer(serializers.Serializer):
    submission_id = serializers.IntegerField()
    content_type = serializers.CharField()
    status = serializers.CharField()
    flagged = serializers.BooleanField()
    detected_categories = serializers.ListField()
    classification_result = serializers.JSONField()
    message = serializers.CharField()
    created_at = serializers.DateTimeField()


# ========================================
# MODEL SERIALIZERS
# ========================================
class ContentSubmissionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = ContentSubmission
        fields = [
            'id', 'user', 'content_type', 'status', 'text_content',
            'file_path', 'content_url', 'classification_result',
            'detected_categories', 'confidence_scores', 'flagged',
            'is_from_api', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminReviewSerializer(serializers.ModelSerializer):
    admin = serializers.StringRelatedField()
    submission = ContentSubmissionSerializer(read_only=True)
    
    class Meta:
        model = AdminReview
        fields = ['id', 'submission', 'admin', 'decision', 'comments', 'reviewed_at']
        read_only_fields = ['id', 'admin', 'reviewed_at']


class APIKeySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = APIKey
        fields = [
            'id', 'user', 'key', 'name', 'tier', 'daily_limit',
            'requests_today', 'last_reset', 'is_active',
            'created_at', 'last_used', 'webhook_url'
        ]
        read_only_fields = ['id', 'key', 'requests_today', 'last_reset', 'created_at', 'last_used']
        extra_kwargs = {
            'key': {'write_only': False}  # Show in responses but can't be edited
        }
