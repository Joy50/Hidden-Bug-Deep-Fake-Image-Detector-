from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from .forms import ImageUploadForm, ForensicUploadForm
from .models import UploadedImage, ForensicAnalysis, ArtifactDetection
from .utils.model_loader import detector
import os
import json
import random
from datetime import datetime

# Add these helper functions to views.py
def get_artifact_display_name(artifact_type):
    """Convert artifact type to display name"""
    artifact_names = {
        'facial_asymmetry': 'Facial Asymmetry',
        'lighting_inconsistency': 'Lighting Inconsistency',
        'skin_texture': 'Skin Texture Anomalies',
        'eye_reflection': 'Eye Reflection Anomalies',
        'background_mismatch': 'Background Mismatch',
        'blink_pattern': 'Blink Pattern Anomalies',
        'color_inconsistency': 'Color Inconsistency',
    }
    return artifact_names.get(artifact_type, artifact_type)

def home(request):
    return render(request, 'index.html')

def upload_image(request):
    if request.method == 'POST':
        form = ForensicUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the analysis record with forensic data
            analysis = form.save()
            
            # Get full path to the image
            image_path = os.path.join(settings.MEDIA_ROOT, analysis.original_file.name)
            
            # Make prediction
            result = detector.predict(image_path)
            
            if 'error' not in result:
                # Enhanced analysis with forensic details
                enhanced_result = enhance_forensic_analysis(analysis, result, image_path)
                
                return render(request, 'forensic_result.html', {
                    'analysis': analysis,
                    'result': enhanced_result
                })
            else:
                return render(request, 'forensic_upload.html', {
                    'form': form,
                    'error': result['error']
                })
    else:
        form = ForensicUploadForm()
    
    return render(request, 'forensic_upload.html', {'form': form})

def api_predict(request):
    """API endpoint for predictions"""
    if request.method == 'POST' and request.FILES.get('image'):
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_image = form.save()
            image_path = os.path.join(settings.MEDIA_ROOT, uploaded_image.image.name)
            
            result = detector.predict(image_path)
            
            if 'error' not in result:
                return JsonResponse({
                    'success': True,
                    'prediction': result['label'],
                    'confidence': result['confidence'],
                    'is_deepfake': result['is_deepfake']
                })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def detect_artifacts(image_path, is_deepfake):
    """Simulate artifact detection - integrate real artifact detection logic"""
    artifact_types = [
        'facial_asymmetry', 'lighting_inconsistency', 'skin_texture',
        'eye_reflection', 'background_mismatch', 'blink_pattern', 'color_inconsistency'
    ]
    
    detected_artifacts = []
    
    # If it's a deepfake, simulate some artifacts
    if is_deepfake:
        # Randomly select 2-4 artifacts
        num_artifacts = random.randint(2, 4)
        selected_artifacts = random.sample(artifact_types, num_artifacts)
        
        for artifact_type in selected_artifacts:
            detected_artifacts.append({
                'type': artifact_type,
                'display_name': get_artifact_display_name(artifact_type),
                'confidence': round(random.uniform(0.6, 0.95), 2),
                'location': 'Various',
                'description': f'Detected {get_artifact_display_name(artifact_type)} anomalies'
            })
    
    return detected_artifacts

def forensic_analysis(request):
    if request.method == 'POST':
        form = ForensicUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the analysis record
            analysis = form.save()
            
            # Get full path to the image
            image_path = os.path.join(settings.MEDIA_ROOT, analysis.original_file.name)
            
            # Make prediction
            result = detector.predict(image_path)
            
            if 'error' not in result:
                # Enhanced analysis with forensic details
                enhanced_result = enhance_forensic_analysis(analysis, result, image_path)
                
                return render(request, 'forensic_result.html', {
                    'analysis': analysis,
                    'result': enhanced_result
                })
            else:
                return render(request, 'forensic_upload.html', {
                    'form': form,
                    'error': result['error']
                })
    else:
        form = ForensicUploadForm()
    
    return render(request, 'forensic_upload.html', {'form': form})

def enhance_forensic_analysis(analysis, basic_result, image_path):
    """Enhance basic prediction with forensic analysis"""
    
    # Calculate authenticity score (invert if deepfake)
    authenticity_score = basic_result['confidence'] 
    if basic_result['is_deepfake']:
        authenticity_score = 100 - basic_result['confidence']
    
    # Determine classification and confidence
    classification, confidence_level = determine_classification(authenticity_score, basic_result['confidence'], basic_result['is_deepfake'])
    
    # Detect artifacts (simulated - you'd integrate real artifact detection)
    detected_artifacts = detect_artifacts(image_path, basic_result['is_deepfake'])
    
    # Generate heatmap path (simulated)
    heatmap_path = generate_heatmap(image_path)
    
    # Detect toolkit signatures (simulated)
    toolkit_signature = detect_toolkit_signature(image_path)
    
    # Prepare enhanced result
    enhanced_result = {
        **basic_result,
        'authenticity_score': round(authenticity_score, 2),
        'classification': classification,
        'confidence_level': confidence_level,
        'detected_artifacts': detected_artifacts,
        'heatmap_path': heatmap_path,
        'toolkit_signature': toolkit_signature,
        'summary': generate_summary(classification, authenticity_score, detected_artifacts),
        'recommended_action': determine_recommended_action(classification, confidence_level)
    }
    
    # Save enhanced results to database
    analysis.authenticity_score = authenticity_score
    analysis.classification = classification
    analysis.confidence_level = confidence_level
    analysis.detected_artifacts = detected_artifacts
    analysis.detected_toolkit = toolkit_signature
    analysis.summary = enhanced_result['summary']
    analysis.recommended_action = enhanced_result['recommended_action']
    analysis.raw_prediction_data = basic_result
    analysis.save()
    
    # Save artifacts to database
    for artifact in detected_artifacts:
        ArtifactDetection.objects.create(
            analysis=analysis,
            artifact_type=artifact['type'],
            confidence=artifact['confidence'],
            location=artifact.get('location', ''),
            description=artifact['description']
        )
    
    return enhanced_result

def determine_classification(authenticity_score, model_confidence, is_deepfake):
    """Determine classification based on scores and actual prediction"""
    if is_deepfake:
        # If model predicts deepfake
        if model_confidence >= 80:
            classification = 'confirmed_fake'
            confidence_level = 'high'
        elif model_confidence >= 60:
            classification = 'suspected_fake'
            confidence_level = 'medium'
        else:
            classification = 'suspected_fake'
            confidence_level = 'low'
    else:
        # If model predicts real
        if model_confidence >= 80:
            classification = 'likely_genuine'
            confidence_level = 'high'
        elif model_confidence >= 60:
            classification = 'likely_genuine'
            confidence_level = 'medium'
        else:
            classification = 'suspected_fake'  # Low confidence real predictions are suspicious
            confidence_level = 'low'
    
    return classification, confidence_level

def generate_heatmap(image_path):
    """Simulate heatmap generation - integrate real heatmap generation"""
    return "/static/detection_app/images/heatmap-placeholder.png"

def detect_toolkit_signature(image_path):
    """Simulate toolkit detection - integrate real signature analysis"""
    toolkits = ['DeepFaceLab', 'StyleGAN', 'FaceSwap', 'DFaker', 'Unknown']
    return random.choice(toolkits) if random.random() > 0.5 else ""

def generate_summary(classification, authenticity_score, artifacts):
    """Generate plain-language summary"""
    if classification == 'likely_genuine':
        return f"This media appears authentic with {authenticity_score:.1f}% confidence. No significant manipulation artifacts detected."
    elif classification == 'suspected_fake':
        return f"This media shows signs of potential manipulation ({authenticity_score:.1f}% authenticity). {len(artifacts)} technical anomalies detected requiring further review."
    else:
        return f"This media is likely synthetic or heavily manipulated ({authenticity_score:.1f}% authenticity). {len(artifacts)} distinct manipulation artifacts identified."

def determine_recommended_action(classification, confidence_level):
    """Determine recommended action based on analysis"""
    if classification == 'confirmed_fake':
        return 'alert_units'
    elif classification == 'suspected_fake' and confidence_level == 'high':
        return 'archive'
    elif classification == 'suspected_fake':
        return 'correlate'
    else:
        return 'flag_review'
    
def debug_classification(request, analysis_id):
    """Debug view to see classification logic"""
    from .models import ForensicAnalysis
    analysis = ForensicAnalysis.objects.get(id=analysis_id)
    
    return JsonResponse({
        'authenticity_score': analysis.authenticity_score,
        'raw_confidence': analysis.raw_prediction_data.get('confidence', 0),
        'is_deepfake': analysis.raw_prediction_data.get('is_deepfake', False),
        'classification': analysis.classification,
        'confidence_level': analysis.confidence_level
    })