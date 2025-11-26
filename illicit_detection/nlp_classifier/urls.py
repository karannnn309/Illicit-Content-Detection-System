from django.urls import path
from .views import *

urlpatterns = [
    #path('result', classify_view, name='classify'),
    path('', landing_page, name='landing_page'),
    path('dashboard', dashboard, name='dashboard'),
    path('text/', text_classification_view, name='text_classification'),
    path('image/', image_classification_view, name='image_classification'),
    path('video/', video_classification_view, name='video_classification'),
    path('audio/', audio_classification_view, name='audio_classification'),
]