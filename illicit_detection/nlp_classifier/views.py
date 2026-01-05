from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
import json
import tempfile
import os
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import cv2
from django.utils.safestring import mark_safe
import tempfile

from .forms import *
from .models import UserProfile, ContentSubmission, AdminReview, APIKey, Notification, BillingRecord, Payment
from .classifier import classify_text, classify_image, analyze_video
from .twitter_api import fetch_text_from_url


# ========================================
# HELPER FUNCTIONS
# ========================================
def is_admin(user):
    """Check if user is an admin"""
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'admin'


# ========================================
# AUTHENTICATION VIEWS
# ========================================
def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            organization = form.cleaned_data.get('organization', '')
            UserProfile.objects.create(
                user=user,
                role='user',
                organization=organization
            )
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                
                # Redirect admin users to admin panel
                if hasattr(user, 'profile') and user.profile.role == 'admin':
                    return redirect('admin_dashboard')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing_page')


# ========================================
# PUBLIC VIEWS
# ========================================

def landing_page(request):
    """Simple view to render the landing page"""
    return render(request, 'landing_page.html')


@login_required
def dashboard(request):
    """User dashboard with statistics"""
    user_submissions = ContentSubmission.objects.filter(user=request.user)
    
    context = {
        'total_submissions': user_submissions.count(),
        'pending_reviews': user_submissions.filter(status='pending_review').count(),
        'flagged_content': user_submissions.filter(flagged=True).count(),
        'recent_submissions': user_submissions[:5]
    }
    return render(request, 'dashboard.html', context)


@login_required
def text_classification_view(request):
    text_result = {}
    root_words = []
    text_categories = []
    detected_lang = ""
    text_conclusion = ""
    input_text = ""
    error_message = ""

    if request.method == 'POST':
        form = TextInputForm(request.POST)
        if form.is_valid():
            input_text = form.cleaned_data.get('text', '').strip()
            url = form.cleaned_data.get('url', '').strip()

            if url and not input_text:
                try:
                    fetched_text = fetch_text_from_url(url).strip()
                    if not fetched_text or fetched_text.lower().startswith(("error", "something went wrong")):
                        error_message = "No usable content extracted from the URL."
                    else:
                        input_text = fetched_text
                except Exception:
                    error_message = "Failed to fetch or process the URL."

            if input_text and not error_message:
                try:
                    scores, root_words, text_categories, detected_lang, text_conclusion = classify_text(input_text)
                    text_result = scores
                    
                    # Save submission to database
                    submission = ContentSubmission.objects.create(
                        user=request.user,
                        content_type='text',
                        text_content=input_text,
                        content_url=url if url else None,
                        classification_result=scores,
                        detected_categories=text_categories,
                        confidence_scores=scores,
                        flagged=bool(text_categories),
                        status='pending_review' if text_categories else 'auto_approved'
                    )
                    
                    if text_categories:
                        messages.warning(request, 'Content flagged for admin review.')
                    else:
                        messages.success(request, 'Content classified successfully.')
                    
                except Exception as e:
                    error_message = str(e)

    else:
        form = TextInputForm()

    def safe_json(data):
        return mark_safe(json.dumps(data)) if data else mark_safe('{}')

    return render(request, 'text_classification.html', {
        'form': form,
        'text_result': safe_json(text_result),
        'root_words': root_words,
        'text_categories': text_categories,
        'detected_lang': detected_lang,
        'text_conclusion': text_conclusion,
        'input_text': input_text,
        'error_message': error_message,
    })



@login_required
def image_classification_view(request):
    image_result = {}
    image_detections = []
    image_categories = []
    image_conclusion = ""
    error_message = ""

    if request.method == 'POST':
        form = ImageInputForm(request.POST, request.FILES)
        image_input = None
        file_path = None

        if form.is_valid():
            if 'image' in request.FILES:
                try:
                    image_file = request.FILES['image']
                    image_input = Image.open(image_file).convert("RGB")
                    image_input = np.array(image_input)
                    # Save file path for database
                    file_path = f"temp_{image_file.name}"
                except Exception:
                    error_message = "Failed to process uploaded image."
            elif request.POST.get('image_url'):
                try:
                    img_url = request.POST.get('image_url')
                    resp = requests.get(img_url, timeout=10)
                    resp.raise_for_status()
                    image_input = Image.open(BytesIO(resp.content)).convert("RGB")
                    image_input = np.array(image_input)
                    file_path = img_url
                except Exception:
                    error_message = "Failed to fetch or decode image from URL."

            if image_input is not None and not error_message:
                try:
                    img_results, image_categories, image_conclusion = classify_image(image_input)
                    image_result = img_results
                    if "nudenet" in img_results:
                        image_detections = img_results.get("nudenet", {}).get("detections", [])
                    
                    # Save submission to database
                    submission = ContentSubmission.objects.create(
                        user=request.user,
                        content_type='image',
                        file_path=file_path,
                        content_url=request.POST.get('image_url') if request.POST.get('image_url') else None,
                        classification_result=img_results,
                        detected_categories=image_categories,
                        confidence_scores=img_results,
                        flagged=bool(image_categories),
                        status='pending_review' if image_categories else 'auto_approved'
                    )
                    
                    if image_categories:
                        messages.warning(request, 'Content flagged for admin review.')
                    else:
                        messages.success(request, 'Image classified successfully.')
                        
                except Exception as e:
                    error_message = f"Failed to process image. Error: {str(e)}"
    else:
        form = ImageInputForm()

    return render(request, 'image_classification.html', {
        'form': form,
        'image_result': image_result,
        'image_detections': image_detections,
        'image_categories': image_categories,
        'image_conclusion': image_conclusion,
        'error_message': error_message,
    })




@login_required
def video_classification_view(request):
    video_result = {}
    video_categories = []
    video_conclusion = ""
    error_message = ""

    if request.method == 'POST' and 'video' in request.FILES:
        form = ImageInputForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                video_file = request.FILES['video']
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                    for chunk in video_file.chunks():
                        temp_video.write(chunk)
                    temp_video_path = temp_video.name

                analysis_result = analyze_video(temp_video_path, frame_skip=50)
                video_result = analysis_result["video_summary"]
                frame_results = analysis_result.get("frame_results", [])

                video_categories = video_result.get("dominant_categories", [])
                if video_categories:
                    video_conclusion = f"Video likely contains content: {', '.join(video_categories)}"
                else:
                    video_conclusion = "No significant illicit categories detected."

                video_result["frame_details"] = frame_results
                
                # Save submission to database
                submission = ContentSubmission.objects.create(
                    user=request.user,
                    content_type='video',
                    file_path=temp_video_path,
                    classification_result=video_result,
                    detected_categories=video_categories,
                    confidence_scores=video_result.get('category_counts', {}),
                    flagged=bool(video_categories),
                    status='pending_review' if video_categories else 'auto_approved'
                )
                
                if video_categories:
                    messages.warning(request, 'Video flagged for admin review.')
                else:
                    messages.success(request, 'Video classified successfully.')
                
                # Clean up temp file
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)

            except Exception as e:
                error_message = f"Failed to analyze video. Error: {str(e)}"
    else:
        form = ImageInputForm()

    return render(request, 'video_classification.html', {
        'form': form,
        'video_result': video_result,
        'video_categories': video_categories,
        'video_conclusion': video_conclusion,
        'error_message': error_message,
    })


# ========================================
# ADMIN VIEWS
# ========================================
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with content moderation overview"""
    pending_submissions = ContentSubmission.objects.filter(status='pending_review')
    
    # Statistics
    total_pending = pending_submissions.count()
    total_reviewed = AdminReview.objects.count()
    total_approved = ContentSubmission.objects.filter(status='approved').count()
    total_rejected = ContentSubmission.objects.filter(status='rejected').count()
    
    # Recent submissions
    recent_submissions = pending_submissions.order_by('-created_at')[:10]
    
    context = {
        'total_pending': total_pending,
        'total_reviewed': total_reviewed,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'recent_submissions': recent_submissions,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def review_content(request, submission_id):
    """Admin view to review flagged content"""
    submission = get_object_or_404(ContentSubmission, id=submission_id)
    
    # Check if a review already exists
    existing_review = AdminReview.objects.filter(submission=submission).first()
    
    if request.method == 'POST':
        if existing_review:
            # Update existing review
            form = AdminReviewForm(request.POST, instance=existing_review)
        else:
            # Create new review
            form = AdminReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.submission = submission
            review.admin = request.user
            review.save()
            
            if existing_review:
                messages.success(request, f'Review updated. Content marked as {review.decision}.')
            else:
                messages.success(request, f'Review submitted. Content marked as {review.decision}.')
            
            return redirect('admin_dashboard')
    else:
        if existing_review:
            form = AdminReviewForm(instance=existing_review)
        else:
            form = AdminReviewForm()
    
    context = {
        'submission': submission,
        'form': form,
        'existing_review': existing_review,
    }
    return render(request, 'review_content.html', context)


@login_required
@user_passes_test(is_admin)
def all_submissions(request):
    """View all submissions with filtering"""
    status_filter = request.GET.get('status', 'all')
    
    submissions = ContentSubmission.objects.all()
    if status_filter != 'all':
        submissions = submissions.filter(status=status_filter)
    
    submissions = submissions.order_by('-created_at')
    
    context = {
        'submissions': submissions,
        'status_filter': status_filter,
    }
    return render(request, 'all_submissions.html', context)

# def audio_classification_view(request):
#     audio_result = {}
#     audio_categories = []
#     audio_conclusion = ""
#     error_message = ""

#     if request.method == 'POST' and 'audio' in request.FILES:
#         form = AudioInputForm(request.POST, request.FILES)
#         if form.is_valid():
#             audio_file = request.FILES['audio']

#             try:
#                 # Save uploaded audio to a temporary file
#                 suffix = os.path.splitext(audio_file.name)[1] or ".wav"
#                 with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
#                     for chunk in audio_file.chunks():
#                         temp_audio.write(chunk)
#                     temp_audio_path = temp_audio.name

#                 # Run Whisper-based speech classification
#                 audio_result, audio_categories, audio_conclusion = classify_speech(temp_audio_path)

#             except Exception as e:
#                 error_message = f"Failed to analyze audio. Error: {str(e)}"

#             finally:
#                 # Make sure the temporary file is removed
#                 if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
#                     os.remove(temp_audio_path)
#     else:
#         form = AudioInputForm()

#     # Ensure that results are always passed to template
#     context = {
#         'form': form,
#         'audio_result': audio_result or {},
#         'audio_categories': audio_categories or [],
#         'audio_conclusion': audio_conclusion or "",
#         'error_message': error_message
#     }

#     return render(request, 'audio_classification.html', context)



# ========================================
# API KEY MANAGEMENT VIEWS
# ========================================
@login_required
def my_api_keys(request):
    """User's API key management page"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            # Create new API key
            APIKey.objects.create(
                user=request.user,
                name=name,
                tier='free',
                daily_limit=50
            )
            messages.success(request, f'API key "{name}" created successfully!')
            return redirect('my_api_keys')
        else:
            messages.error(request, 'Please provide a name for your API key.')
    
    api_keys = APIKey.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'api_keys': api_keys,
    }
    return render(request, 'my_api_keys.html', context)


@login_required
def delete_api_key(request, key_id):
    """Delete an API key"""
    api_key = get_object_or_404(APIKey, id=key_id, user=request.user)
    key_name = api_key.name
    api_key.delete()
    messages.success(request, f'API key "{key_name}" deleted successfully!')
    return redirect('my_api_keys')


@login_required
def api_documentation_page(request):
    """API documentation page"""
    # Get user's first active API key for examples
    sample_key = APIKey.objects.filter(user=request.user, is_active=True).first()
    context = {
        'sample_key': sample_key.key if sample_key else 'YOUR_API_KEY_HERE',
    }
    return render(request, 'api_documentation.html', context)


# ========================================
# NOTIFICATION VIEWS
# ========================================
@login_required
def notifications_view(request):
    """User notifications page"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark as read if requested
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            notification = get_object_or_404(Notification, id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return redirect('notifications')
    
    # Count unread
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications.html', context)


# ========================================
# ADMIN BILLING VIEWS
# ========================================
@login_required
@user_passes_test(is_admin)
def admin_billing_dashboard(request):
    """Admin dashboard for billing information"""
    from django.db.models import Sum
    from datetime import datetime
    
    # Get current month/year
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    # Get all billing records for current month
    current_month_records = BillingRecord.objects.filter(
        year=current_year,
        month=current_month
    ).select_related('user')
    
    # Calculate totals
    total_revenue = current_month_records.aggregate(Sum('amount_charged'))['amount_charged__sum'] or 0
    total_requests = current_month_records.aggregate(Sum('total_requests'))['total_requests__sum'] or 0
    total_paid_requests = current_month_records.aggregate(Sum('paid_requests'))['paid_requests__sum'] or 0
    
    # Get top users by revenue
    top_users = current_month_records.order_by('-amount_charged')[:10]
    
    # Get all users with API keys
    users_with_keys = User.objects.filter(api_keys__isnull=False).distinct()
    
    context = {
        'current_month': current_month,
        'current_year': current_year,
        'current_month_records': current_month_records,
        'total_revenue': total_revenue,
        'total_requests': total_requests,
        'total_paid_requests': total_paid_requests,
        'top_users': top_users,
        'users_with_keys': users_with_keys,
    }
    return render(request, 'admin_billing_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_billing_detail(request, user_id):
    """Detailed billing information for a specific user"""
    from django.contrib.auth.models import User
    
    target_user = get_object_or_404(User, id=user_id)
    billing_records = BillingRecord.objects.filter(user=target_user).order_by('-year', '-month')
    api_keys = APIKey.objects.filter(user=target_user)
    
    # Calculate totals
    total_all_time = sum(record.amount_charged for record in billing_records)
    total_requests_all_time = sum(record.total_requests for record in billing_records)
    
    context = {
        'target_user': target_user,
        'billing_records': billing_records,
        'api_keys': api_keys,
        'total_all_time': total_all_time,
        'total_requests_all_time': total_requests_all_time,
    }
    return render(request, 'admin_user_billing_detail.html', context)


# ========================================
# PAYMENT & UPGRADE VIEWS
# ========================================
@login_required
def upgrade_api_key(request, key_id):
    """Upgrade API key to a paid tier"""
    from django.conf import settings
    
    api_key = get_object_or_404(APIKey, id=key_id, user=request.user)
    
    if request.method == 'POST':
        tier = request.POST.get('tier')
        
        if tier not in ['basic', 'premium']:
            messages.error(request, 'Invalid tier selected.')
            return redirect('my_api_keys')
        
        # Get tier price
        price = APIKey.TIER_PRICES.get(tier, 0)
        
        # Create payment record with tier in description
        payment = Payment.objects.create(
            user=request.user,
            api_key=api_key,
            amount=price,
            payment_type='upgrade',
            description=f'Upgrade to {tier.title()} Tier|{tier}',  # Store tier for later
            status='pending'
        )
        
        # Redirect to payment page
        return redirect('process_payment', payment_id=payment.id)
    
    # GET request - show upgrade options
    context = {
        'api_key': api_key,
        'tier_prices': APIKey.TIER_PRICES,
        'tier_limits': APIKey.TIER_LIMITS,
    }
    return render(request, 'upgrade_api_key.html', context)


@login_required
def process_payment(request, payment_id):
    """Process payment using Stripe or Test Mode"""
    import stripe
    from django.conf import settings
    from datetime import datetime, timedelta
    
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status == 'completed':
        messages.info(request, 'This payment has already been completed.')
        return redirect('my_api_keys')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'test')
        
        # Check if test mode is enabled in settings
        use_test_mode = getattr(settings, 'STRIPE_TEST_MODE', True)
        
        if payment_method == 'test' or use_test_mode:
            # Test mode - simulate successful payment
            payment.status = 'completed'
            payment.completed_at = datetime.now()
            payment.save()
            
            # Update API key
            if payment.api_key:
                # Extract tier from payment description
                tier = 'basic'
                if '|' in payment.description:
                    tier = payment.description.split('|')[1]
                
                payment.api_key.tier = tier
                payment.api_key.daily_limit = APIKey.TIER_LIMITS[tier]
                payment.api_key.subscription_status = 'active'
                payment.api_key.subscription_start = datetime.now()
                payment.api_key.subscription_end = datetime.now() + timedelta(days=30)
                payment.api_key.requests_today = 0  # Reset requests on upgrade
                payment.api_key.save()
                
                messages.success(request, f'Successfully upgraded to {tier.title()} tier! Your subscription is now active.')
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                title='Payment Successful',
                message=f'Your payment of ${payment.amount} has been processed successfully.',
                notification_type='billing'
            )
            
            return redirect('payment_success', payment_id=payment.id)
        
        # Production mode - use Stripe
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Convert to cents
                currency='usd',
                description=payment.description,
                metadata={'payment_id': payment.id}
            )
            
            payment.stripe_payment_intent_id = intent.id
            payment.save()
            
            context = {
                'payment': payment,
                'client_secret': intent.client_secret,
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            }
            return render(request, 'stripe_payment.html', context)
            
        except Exception as e:
            messages.error(request, f'Payment processing error: {str(e)}')
            return redirect('my_api_keys')
    
    # GET request - show payment form
    use_test_mode = getattr(settings, 'STRIPE_TEST_MODE', True)
    context = {
        'payment': payment,
        'test_mode': use_test_mode,
    }
    return render(request, 'process_payment.html', context)

@login_required
def payment_success(request, payment_id):
    """Payment success page"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    context = {
        'payment': payment,
    }
    return render(request, 'payment_success.html', context)


@login_required
def payment_cancel(request):
    """Payment cancelled page"""
    messages.warning(request, 'Payment was cancelled.')
    return redirect('my_api_keys')


@login_required
def cancel_subscription(request, key_id):
    """Cancel API key subscription"""
    api_key = get_object_or_404(APIKey, id=key_id, user=request.user)
    
    if request.method == 'POST':
        # Downgrade to free tier
        api_key.tier = 'free'
        api_key.daily_limit = 50
        api_key.subscription_status = 'cancelled'
        api_key.save()
        
        # Create notification
        Notification.objects.create(
            user=request.user,
            title='Subscription Cancelled',
            message=f'Your subscription for "{api_key.name}" has been cancelled. You are now on the free tier.',
            notification_type='billing'
        )
        
        messages.success(request, f'Subscription cancelled for "{api_key.name}". Downgraded to free tier.')
    
    return redirect('my_api_keys')


