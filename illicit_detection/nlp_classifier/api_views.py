from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from PIL import Image
import numpy as np
import tempfile
import os
import requests
from io import BytesIO

from .models import ContentSubmission, APIKey, BillingRecord, Notification
from .serializers import (
    TextClassificationSerializer,
    ImageClassificationSerializer,
    VideoClassificationSerializer,
    ClassificationResponseSerializer,
    ContentSubmissionSerializer
)
from .classifier import classify_text, classify_image, analyze_video


# ========================================
# CUSTOM API KEY AUTHENTICATION
# ========================================
def authenticate_api_key(request):
    """Authenticate using API key from header"""
    api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        return None, {"error": "API key required in X-API-Key header"}
    
    try:
        key_obj = APIKey.objects.get(key=api_key, is_active=True)
        
        if not key_obj.can_make_request():
            return None, {"error": "Daily rate limit exceeded"}
        
        key_obj.increment_usage()
        return key_obj, None
    
    except APIKey.DoesNotExist:
        return None, {"error": "Invalid API key"}


def send_webhook_notification(webhook_url, submission_data):
    """Send webhook notification when content is flagged"""
    if not webhook_url:
        return
    
    try:
        requests.post(
            webhook_url,
            json=submission_data,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        print(f"Webhook notification failed: {str(e)}")


def track_api_usage(api_key_obj):
    """
    Track API usage for billing purposes.
    - First 50 requests per day are free
    - After that, $0.01 per request
    """
    from datetime import datetime
    
    user = api_key_obj.user
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    # Get or create billing record for current month
    billing_record, created = BillingRecord.objects.get_or_create(
        user=user,
        year=current_year,
        month=current_month,
        defaults={
            'api_key': api_key_obj,
            'free_requests_used': 0,
            'paid_requests': 0,
            'total_requests': 0,
            'amount_charged': 0.00
        }
    )
    
    # Increment total requests
    billing_record.total_requests += 1
    
    # Check if this is a free or paid request
    if billing_record.free_requests_used < 50:
        # Still within free tier
        billing_record.free_requests_used += 1
    else:
        # Exceeds free tier - charge for this request
        billing_record.paid_requests += 1
        billing_record.calculate_charges()
        
        # Send notification if first paid request
        if billing_record.paid_requests == 1:
            Notification.objects.create(
                user=user,
                title="Free Tier Limit Reached",
                message=f"You have exceeded your 50 free daily requests. Additional requests will be charged at $0.01 per request.",
                notification_type='billing'
            )
    
    billing_record.save()
    
    return billing_record


# ========================================
# API ENDPOINTS
# ========================================
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@csrf_exempt
def api_classify_text(request):
    """
    API endpoint for text classification
    
    Headers:
        X-API-Key: Your API key
    
    Body:
        {
            "text": "Text to classify",
            "webhook_url": "https://your-webhook.com/endpoint" (optional)
        }
    """
    # Authenticate API key
    api_key_obj, error = authenticate_api_key(request)
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)
    
    # Track API usage for billing
    track_api_usage(api_key_obj)
    
    # Validate input
    serializer = TextClassificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    text = serializer.validated_data['text']
    webhook_url = serializer.validated_data.get('webhook_url')
    
    try:
        # Classify text
        scores, root_words, text_categories, detected_lang, text_conclusion = classify_text(text)
        
        # Save submission
        submission = ContentSubmission.objects.create(
            user=api_key_obj.user,
            content_type='text',
            text_content=text,
            classification_result=scores,
            detected_categories=text_categories,
            confidence_scores=scores,
            flagged=bool(text_categories),
            status='pending_review' if text_categories else 'auto_approved',
            is_from_api=True,
            api_key=api_key_obj
        )
        
        response_data = {
            'submission_id': submission.id,
            'content_type': 'text',
            'status': submission.status,
            'flagged': submission.flagged,
            'detected_categories': text_categories,
            'classification_result': {
                'scores': scores,
                'root_words': root_words,
                'detected_language': detected_lang,
                'conclusion': text_conclusion
            },
            'message': 'Content flagged for review' if text_categories else 'Content approved',
            'created_at': submission.created_at
        }
        
        # Send webhook if content is flagged
        if submission.flagged and webhook_url:
            send_webhook_notification(webhook_url, response_data)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Classification failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@csrf_exempt
def api_classify_image(request):
    """
    API endpoint for image classification
    
    Headers:
        X-API-Key: Your API key
    
    Body (form-data or JSON):
        - image_file: Image file (multipart/form-data)
        OR
        - image_url: URL to image (JSON)
        - webhook_url: Webhook URL (optional)
    """
    # Authenticate API key
    api_key_obj, error = authenticate_api_key(request)
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)
    
    # Track API usage for billing
    track_api_usage(api_key_obj)
    
    # Validate input
    serializer = ImageClassificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    webhook_url = serializer.validated_data.get('webhook_url')
    image_input = None
    file_path = None
    
    try:
        # Load image
        if 'image_file' in request.FILES:
            image_file = request.FILES['image_file']
            image_input = Image.open(image_file).convert("RGB")
            image_input = np.array(image_input)
            file_path = f"api_upload_{image_file.name}"
        elif serializer.validated_data.get('image_url'):
            img_url = serializer.validated_data['image_url']
            resp = requests.get(img_url, timeout=10)
            resp.raise_for_status()
            image_input = Image.open(BytesIO(resp.content)).convert("RGB")
            image_input = np.array(image_input)
            file_path = img_url
        
        # Classify image
        img_results, image_categories, image_conclusion = classify_image(image_input)
        
        # Save submission
        submission = ContentSubmission.objects.create(
            user=api_key_obj.user,
            content_type='image',
            file_path=file_path,
            content_url=serializer.validated_data.get('image_url'),
            classification_result=img_results,
            detected_categories=image_categories,
            confidence_scores=img_results,
            flagged=bool(image_categories),
            status='pending_review' if image_categories else 'auto_approved',
            is_from_api=True,
            api_key=api_key_obj
        )
        
        response_data = {
            'submission_id': submission.id,
            'content_type': 'image',
            'status': submission.status,
            'flagged': submission.flagged,
            'detected_categories': image_categories,
            'classification_result': {
                'results': img_results,
                'conclusion': image_conclusion
            },
            'message': 'Content flagged for review' if image_categories else 'Content approved',
            'created_at': submission.created_at
        }
        
        # Send webhook if content is flagged
        if submission.flagged and webhook_url:
            send_webhook_notification(webhook_url, response_data)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Classification failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@csrf_exempt
def api_classify_video(request):
    """
    API endpoint for video classification
    
    Headers:
        X-API-Key: Your API key
    
    Body (form-data):
        - video_file: Video file
        OR
        - video_url: URL to video
        - frame_skip: Number of frames to skip (default: 50)
        - webhook_url: Webhook URL (optional)
    """
    # Authenticate API key
    api_key_obj, error = authenticate_api_key(request)
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)
    
    # Track API usage for billing
    track_api_usage(api_key_obj)
    
    # Validate input
    serializer = VideoClassificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    webhook_url = serializer.validated_data.get('webhook_url')
    frame_skip = serializer.validated_data.get('frame_skip', 50)
    temp_video_path = None
    
    try:
        # Load video
        if 'video_file' in request.FILES:
            video_file = request.FILES['video_file']
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                for chunk in video_file.chunks():
                    temp_video.write(chunk)
                temp_video_path = temp_video.name
        elif serializer.validated_data.get('video_url'):
            # Download video from URL
            video_url = serializer.validated_data['video_url']
            resp = requests.get(video_url, timeout=30)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                temp_video.write(resp.content)
                temp_video_path = temp_video.name
        
        # Analyze video
        analysis_result = analyze_video(temp_video_path, frame_skip=frame_skip)
        video_summary = analysis_result["video_summary"]
        video_categories = video_summary.get("dominant_categories", [])
        
        # Save submission
        submission = ContentSubmission.objects.create(
            user=api_key_obj.user,
            content_type='video',
            file_path=temp_video_path,
            content_url=serializer.validated_data.get('video_url'),
            classification_result=video_summary,
            detected_categories=video_categories,
            confidence_scores=video_summary.get('category_counts', {}),
            flagged=bool(video_categories),
            status='pending_review' if video_categories else 'auto_approved',
            is_from_api=True,
            api_key=api_key_obj
        )
        
        response_data = {
            'submission_id': submission.id,
            'content_type': 'video',
            'status': submission.status,
            'flagged': submission.flagged,
            'detected_categories': video_categories,
            'classification_result': video_summary,
            'message': 'Content flagged for review' if video_categories else 'Content approved',
            'created_at': submission.created_at
        }
        
        # Send webhook if content is flagged
        if submission.flagged and webhook_url:
            send_webhook_notification(webhook_url, response_data)
        
        # Clean up temp file
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        return Response(
            {'error': f'Classification failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
@csrf_exempt
def api_get_submission(request, submission_id):
    """
    Get submission details by ID
    
    Headers:
        X-API-Key: Your API key
    """
    # Authenticate API key
    api_key_obj, error = authenticate_api_key(request)
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        submission = ContentSubmission.objects.get(
            id=submission_id,
            user=api_key_obj.user
        )
        serializer = ContentSubmissionSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except ContentSubmission.DoesNotExist:
        return Response(
            {'error': 'Submission not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def api_health_check(request):
    """Health check endpoint - no authentication required"""
    return Response({
        'status': 'healthy',
        'service': 'Illicit Content Detection API',
        'version': '1.0.0'
    })
