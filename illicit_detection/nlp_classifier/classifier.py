# ========================================
# IMPORTS
# ========================================
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import ViTForImageClassification, ViTImageProcessor
import torch
from keybert import KeyBERT
from deep_translator import GoogleTranslator
from langdetect import detect
import cv2
import numpy as np
import requests
from nudenet import NudeDetector
from collections import Counter

import os
import tempfile




# ========================================
# TEXT MODEL LOADING
# ========================================
model_name = "unitary/unbiased-toxic-roberta"
tokenizer = AutoTokenizer.from_pretrained(model_name)
text_model = AutoModelForSequenceClassification.from_pretrained(model_name)
kw_model = KeyBERT()

# ========================================
# IMAGE MODEL LOADING (UPDATED)
# ========================================
# 🔹 Single multi-category illicit content classifier
new_image_model_name = "karannnn309/vit-finetuned-illicit-model"  # <--- update if needed
image_model = ViTForImageClassification.from_pretrained(new_image_model_name)
image_processor = ViTImageProcessor.from_pretrained(new_image_model_name)

# ========================================
# TEXT CLASSIFICATION
# ========================================
labels = [
    "toxicity",
    "severe_toxicity",
    "obscene",
    "identity_attack",
    "insult",
    "threat",
    "sexual explicit"
]

def format_label(label):
    return label.replace("_", " ").title()

def classify_text(text):
    detected_lang = detect(text)

    if detected_lang != 'en':
        try:
            text = GoogleTranslator(source='auto', target='en').translate(text)
        except Exception:
            raise ValueError(f"Language '{detected_lang}' not supported or translation failed")

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        logits = text_model(**inputs).logits
    probs = torch.sigmoid(logits)[0].tolist()

    scores = {format_label(label): round(probs[i] * 100, 2) for i, label in enumerate(labels)}

    keywords = kw_model.extract_keywords(
        text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=5
    )
    root_words = [kw for kw, _ in keywords]

    categories = map_detoxify_to_category(scores, text)

    if categories:
        conclusion = f"⚠️ The text contains illicit content related to: {', '.join(categories)}."
    else:
        conclusion = "✅ The text appears clean with no significant illicit content detected."

    return scores, root_words, categories, detected_lang, conclusion

def map_detoxify_to_category(scores, text):
    categories = []

    if scores['Threat'] > 60 or (scores['Toxicity'] > 70 and scores['Severe Toxicity'] > 40):
        categories.append("Violence")

    terrorism_keywords = ["bomb", "jihad", "terror", "attack", "islamic state"]
    if scores['Threat'] > 70 and scores['Identity Attack'] > 40:
        if any(word in text.lower() for word in terrorism_keywords):
            categories.append("Terrorism")

    if (scores['Insult'] > 50 or scores['Identity Attack'] > 50) and (scores['Toxicity'] > 50 and scores['Threat'] > 50):
        categories.append("Harassment")

    if scores['Obscene'] > 30 and scores['Sexual Explicit'] > 20:
        categories.append("Profanity")

    if scores['Identity Attack'] > 50 and scores['Toxicity'] > 60:
        categories.append("Hate Speech")

    if scores['Insult'] > 70 and scores['Toxicity'] > 50:
        categories.append("Cyberbullying")

    return list(set(categories))

# ========================================
# NUDE IMAGE DETECTION
# ========================================
detector = NudeDetector()
THRESHOLD = 0.8
EXPLICIT_CLASSES = {
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "EXPOSED_BUTTOCKS",
}

def detect_nudity(image_input):
    if isinstance(image_input, str) and image_input.startswith(("http://", "https://")):
        resp = requests.get(image_input, stream=True)
        resp.raise_for_status()
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        detections = detector.detect(img)
    else:
        detections = detector.detect(image_input)

    is_explicit = any(
        det["class"] in EXPLICIT_CLASSES and det["score"] >= THRESHOLD for det in detections
    )

    return is_explicit, detections

# ========================================
# IMAGE CLASSIFICATION (UPDATED)
# ========================================
def classify_image(image_input):
    if isinstance(image_input, str) and image_input.startswith(("http://", "https://")):
        resp = requests.get(image_input, stream=True)
        resp.raise_for_status()
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    else:
        img_bgr = image_input

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # ----- NudeNet -----
    is_nude, nude_detections = detect_nudity(image_input)
    nude_score = 0.0
    if is_nude:
        nude_score = max(det["score"] for det in nude_detections if det["class"] in EXPLICIT_CLASSES)

    nude_output = {
        "is_nude": is_nude,
        "detections": nude_detections,
        "score": round(nude_score * 100, 2)
    }

    # ----- Single ViT Illicit Classifier -----
    inputs = image_processor(images=img_rgb, return_tensors="pt")
    with torch.no_grad():
        outputs = image_model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

    pred_idx = int(torch.argmax(probs))
    pred_label = image_model.config.id2label[pred_idx]
    confidence = float(probs[pred_idx])

    all_probs = {image_model.config.id2label[i]: round(float(p) * 100, 2)
                 for i, p in enumerate(probs)}

    illicit_output = {
        "label": pred_label,
        "score": round(confidence * 100, 2),
        "all_probs": all_probs
    }

    result = {
        "nudenet": nude_output,
        "illicit_model": illicit_output
    }

    categories = []
    if nude_output["is_nude"]:
        categories.append("Nudity")
    categories.append(f"Detected Category → {pred_label}")

    conclusion = " | ".join(categories)

    return result, categories, conclusion

# ========================================
# VIDEO ANALYSIS
# ========================================
def analyze_video(video_path, frame_skip=50):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("❌ Could not open the video file.")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_results = []
    all_categories = []
    frame_no = 0
    processed_frames = 0

    print(f"🔍 Processing {frame_count} frames (skipping every {frame_skip})...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_no += 1
        if frame_no % frame_skip != 0:
            continue

        processed_frames += 1
        print(f"🖼️ Analysing frame {frame_no}/{frame_count}")

        try:
            result, categories, conclusion = classify_image(frame)
            frame_results.append({
                "frame_no": frame_no,
                "categories": categories,
                "result": result,
                "conclusion": conclusion
            })
            all_categories.extend(categories)
        except Exception as e:
            print(f"⚠️ Error on frame {frame_no}: {str(e)}")
            continue

    cap.release()

    category_counts = Counter(all_categories)
    dominant_categories = [cat for cat, _ in category_counts.most_common(3)]

    video_summary = {
        "dominant_categories": dominant_categories,
        "category_counts": dict(category_counts),
        "total_frames": frame_count,
        "processed_frames": processed_frames
    }

    print("✅ Video analysis complete.")
    return {
        "frame_results": frame_results,
        "video_summary": video_summary
    }

# ========================================
# AUDIO CLASSIFICATION (UNCHANGED)
# ========================================

# import whisper

# whisper_model = whisper.load_model("base")

# def classify_speech(audio_file_path):
#     results = {}
#     categories = []
#     conclusion = ""

#     try:
#         transcription = whisper_model.transcribe(audio_file_path)
#         transcript = transcription["text"].strip()

#         if not transcript:
#             conclusion = "❌ No speech detected in audio."
#             return results, categories, conclusion

#         scores, root_words, text_categories, detected_lang, text_conclusion = classify_text(transcript)
#         results = scores
#         categories = text_categories
#         print(categories)

#         if categories:
#             conclusion = f"🎤 Audio likely contains content related to: {', '.join(categories)}"
#         else:
#             conclusion = "✅ No illicit content detected in the audio."

#     except Exception as e:
#         conclusion = f"❌ Failed to analyze audio. Error: {str(e)}"

#     return results, categories, conclusion
