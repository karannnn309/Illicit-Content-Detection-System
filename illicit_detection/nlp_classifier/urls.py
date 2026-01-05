from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
from .api_views import *

urlpatterns = [
    # Public pages
    path('', landing_page, name='landing_page'),
    
    # Authentication
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # User dashboard and classification
    path('dashboard/', dashboard, name='dashboard'),
    path('text/', text_classification_view, name='text_classification'),
    path('image/', image_classification_view, name='image_classification'),
    path('video/', video_classification_view, name='video_classification'),
    
    # Admin views
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    path('admin-panel/review/<int:submission_id>/', review_content, name='review_content'),
    path('admin-panel/submissions/', all_submissions, name='all_submissions'),
    path('admin-panel/billing/', admin_billing_dashboard, name='admin_billing_dashboard'),
    path('admin-panel/billing/user/<int:user_id>/', admin_user_billing_detail, name='admin_user_billing_detail'),
    
    # API Key Management
    path('my-api-keys/', my_api_keys, name='my_api_keys'),
    path('my-api-keys/delete/<int:key_id>/', delete_api_key, name='delete_api_key'),
    path('my-api-keys/upgrade/<int:key_id>/', upgrade_api_key, name='upgrade_api_key'),
    path('api-documentation/', api_documentation_page, name='api_documentation'),
    
    # Payment & Subscription
    path('payment/process/<int:payment_id>/', process_payment, name='process_payment'),
    path('payment/success/<int:payment_id>/', payment_success, name='payment_success'),
    path('payment/cancel/', payment_cancel, name='payment_cancel'),
    path('subscription/cancel/<int:key_id>/', cancel_subscription, name='cancel_subscription'),
    
    # Notifications
    path('notifications/', notifications_view, name='notifications'),
    
    # API endpoints
    path('api/v1/health/', api_health_check, name='api_health'),
    path('api/v1/classify/text/', api_classify_text, name='api_classify_text'),
    path('api/v1/classify/image/', api_classify_image, name='api_classify_image'),
    path('api/v1/classify/video/', api_classify_video, name='api_classify_video'),
    path('api/v1/submission/<int:submission_id>/', api_get_submission, name='api_get_submission'),
    
    # JWT token endpoints
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]