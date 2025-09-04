from django.db import models
import hashlib
import os
from PIL import Image as PILImage
from django.core.files.storage import default_storage
import exifread
from datetime import datetime

# Create your models here.
class UploadedImage(models.Model):
    image = models.ImageField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    prediction = models.CharField(max_length=20, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    is_deepfake = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image {self.id} - {self.prediction}"

class ForensicAnalysis(models.Model):
    # Header / Metadata
    report_id = models.CharField(max_length=20, unique=True, blank=True)
    analysis_date = models.DateTimeField(auto_now_add=True)
    analyst_id = models.CharField(max_length=100, default="System Auto-Detection")
    media_source = models.CharField(max_length=200, default="File Upload")
    media_type = models.CharField(max_length=50, choices=[
        ('image', 'Image'),
        ('video_frame', 'Video Frame'),
        ('screenshot', 'Screenshot')
    ], default='image')
    
    # Media Details
    original_file = models.ImageField(upload_to='forensic_uploads/')
    file_name = models.CharField(max_length=255, blank=True)
    file_hash_sha256 = models.CharField(max_length=64, blank=True)
    file_hash_md5 = models.CharField(max_length=32, blank=True)
    file_size = models.BigIntegerField(default=0)
    resolution = models.CharField(max_length=50, blank=True)
    file_format = models.CharField(max_length=10, blank=True)
    exif_data = models.JSONField(default=dict, blank=True)
    metadata_inconsistencies = models.TextField(blank=True)
    
    # Detection Results
    authenticity_score = models.FloatField(default=0.0)
    classification = models.CharField(max_length=50, choices=[
        ('likely_genuine', 'Likely Genuine'),
        ('suspected_fake', 'Suspected Fake'),
        ('confirmed_fake', 'Confirmed Fake')
    ], default='likely_genuine')
    confidence_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='low')
    
    # Technical Indicators
    detected_artifacts = models.JSONField(default=list, blank=True)
    heatmap_path = models.CharField(max_length=255, blank=True)
    model_ensemble_results = models.JSONField(default=dict, blank=True)
    
    # Adversarial Analysis
    adversarial_detection = models.JSONField(default=dict, blank=True)
    detected_toolkit = models.CharField(max_length=100, blank=True)
    cross_correlation = models.JSONField(default=list, blank=True)
    
    # Summary
    summary = models.TextField(blank=True)
    recommended_action = models.CharField(max_length=100, choices=[
        ('flag_review', 'Flag for Human Review'),
        ('archive', 'Archive as Verified Deepfake'),
        ('alert_units', 'Alert Counter-Disinformation Units'),
        ('correlate', 'Correlate with Investigations')
    ], default='flag_review')
    
    # Internal fields
    raw_prediction_data = models.JSONField(default=dict, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.report_id:
            self.report_id = f"DFR-{datetime.now().strftime('%Y%m%d')}-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:6].upper()}"
        
        if self.original_file:
            self.file_name = self.original_file.name
            self.file_size = self.original_file.size
            self._calculate_hashes()
            self._extract_metadata()
            
        super().save(*args, **kwargs)
    
    def _calculate_hashes(self):
        """Calculate file hashes for integrity verification"""
        try:
            file_path = self.original_file.path
            with open(file_path, 'rb') as f:
                content = f.read()
                self.file_hash_sha256 = hashlib.sha256(content).hexdigest()
                self.file_hash_md5 = hashlib.md5(content).hexdigest()
        except:
            pass
    
    def _extract_metadata(self):
        """Extract EXIF and image metadata"""
        try:
            file_path = self.original_file.path
            self.file_format = os.path.splitext(file_path)[1].lower().replace('.', '')
            
            # Get image resolution
            with PILImage.open(file_path) as img:
                self.resolution = f"{img.width}x{img.height}"
            
            # Extract EXIF data
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                self.exif_data = {
                    str(tag): str(tags[tag]) for tag in tags
                    if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename')
                }
                
            # Check for metadata inconsistencies
            self._check_metadata_inconsistencies()
            
        except Exception as e:
            self.exif_data = {'error': str(e)}
    
    def _check_metadata_inconsistencies(self):
        """Check for metadata red flags"""
        inconsistencies = []
        
        # Check if image has been edited
        software_tags = ['Software', 'Processing Software', 'History']
        for tag in software_tags:
            if tag.lower() in [k.lower() for k in self.exif_data.keys()]:
                inconsistencies.append(f"Editing software detected: {tag}")
        
        # Check for missing basic EXIF
        basic_tags = ['EXIF DateTimeOriginal', 'Image Model', 'Image Make']
        for tag in basic_tags:
            if tag not in self.exif_data:
                inconsistencies.append(f"Missing expected EXIF tag: {tag}")
        
        self.metadata_inconsistencies = "\n".join(inconsistencies)
    
    def __str__(self):
        return f"{self.report_id} - {self.classification}"

class ArtifactDetection(models.Model):
    ARTIFACT_TYPES = [
        ('facial_asymmetry', 'Facial Asymmetry'),
        ('lighting_inconsistency', 'Lighting/Shadow Inconsistencies'),
        ('skin_texture', 'Skin Texture Anomalies'),
        ('eye_reflection', 'Eye Reflection Anomalies'),
        ('background_mismatch', 'Background Mismatch'),
        ('blink_pattern', 'Blink Pattern Anomalies'),
        ('color_inconsistency', 'Color Inconsistency'),
    ]
    
    analysis = models.ForeignKey(ForensicAnalysis, on_delete=models.CASCADE)
    artifact_type = models.CharField(max_length=50, choices=ARTIFACT_TYPES)
    confidence = models.FloatField(default=0.0)
    location = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.artifact_type} - {self.confidence:.2f}"