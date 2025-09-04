from django import forms
from .models import UploadedImage, ForensicAnalysis

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedImage
        fields = ['image']
        
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file too large ( > 5MB )")
            if not image.content_type.startswith('image'):
                raise forms.ValidationError("File is not an image")
        return image

class ForensicUploadForm(forms.ModelForm):
    MEDIA_SOURCE_CHOICES = [
        ('file_upload', 'File Upload'),
        ('social_media', 'Social Media'),
        ('intercepted', 'Intercepted Communications'),
        ('evidence', 'Evidence Collection'),
    ]

    media_source = forms.ChoiceField(
        choices=MEDIA_SOURCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    analyst_id = forms.CharField(
        required=False,
        initial="System Auto-Detection",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ForensicAnalysis
        fields = ['original_file', 'media_source', 'analyst_id', 'media_type']
        widgets = {
            'original_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'media_type': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_original_file(self):
        file = self.cleaned_data.get('original_file')
        if file:
            # File size limit (10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 10MB")

            # Allowed formats
            allowed_formats = ['jpg', 'jpeg', 'png', 'webp', 'bmp']
            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_formats:
                raise forms.ValidationError(
                    f"Unsupported file format. Allowed: {', '.join(allowed_formats)}"
                )
        return file
