from django.shortcuts import render, redirect
from django.urls import reverse
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
from .classifier import classify_text, classify_image, analyze_video, classify_speech
from .twitter_api import fetch_text_from_url

def landing_page(request):
    """Simple view to render the landing page"""
    return render(request, 'landing_page.html')


def dashboard(request):
    return render(request, 'dashboard.html')


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




def image_classification_view(request):
    image_result = {}
    image_detections = []
    image_categories = []
    image_conclusion = ""
    error_message = ""

    if request.method == 'POST':
        form = ImageInputForm(request.POST, request.FILES)
        image_input = None

        if form.is_valid():
            if 'image' in request.FILES:
                try:
                    image_input = Image.open(request.FILES['image']).convert("RGB")
                    image_input = np.array(image_input)
                except Exception:
                    error_message = "Failed to process uploaded image."
            elif request.POST.get('image_url'):
                try:
                    img_url = request.POST.get('image_url')
                    resp = requests.get(img_url, timeout=10)
                    resp.raise_for_status()
                    image_input = Image.open(BytesIO(resp.content)).convert("RGB")
                    image_input = np.array(image_input)
                except Exception:
                    error_message = "Failed to fetch or decode image from URL."

            if image_input is not None and not error_message:
                try:
                    img_results, image_categories, image_conclusion = classify_image(image_input)
                    image_result = img_results
                    if "nudenet" in img_results:
                        image_detections = img_results.get("nudenet", {}).get("detections", [])
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

def audio_classification_view(request):
    audio_result = {}
    audio_categories = []
    audio_conclusion = ""
    error_message = ""

    if request.method == 'POST' and 'audio' in request.FILES:
        form = AudioInputForm(request.POST, request.FILES)
        if form.is_valid():
            audio_file = request.FILES['audio']

            try:
                # Save uploaded audio to a temporary file
                suffix = os.path.splitext(audio_file.name)[1] or ".wav"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
                    for chunk in audio_file.chunks():
                        temp_audio.write(chunk)
                    temp_audio_path = temp_audio.name

                # Run Whisper-based speech classification
                audio_result, audio_categories, audio_conclusion = classify_speech(temp_audio_path)

            except Exception as e:
                error_message = f"Failed to analyze audio. Error: {str(e)}"

            finally:
                # Make sure the temporary file is removed
                if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
    else:
        form = AudioInputForm()

    # Ensure that results are always passed to template
    context = {
        'form': form,
        'audio_result': audio_result or {},
        'audio_categories': audio_categories or [],
        'audio_conclusion': audio_conclusion or "",
        'error_message': error_message
    }

    return render(request, 'audio_classification.html', context)


