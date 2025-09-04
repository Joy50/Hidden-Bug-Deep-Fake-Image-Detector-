import torch
import torch.nn as nn
from torchvision.models import resnet50
from torchvision import transforms
from PIL import Image
import numpy as np
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ResNet(nn.Module):
    def __init__(self, model):
        super(ResNet, self).__init__()
        self.model = model

    def forward(self, x):
        return torch.softmax(self.model(x), dim=1)

class DeepFakeDetector:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.transform = self.get_transform()
        self.index_label = {0: "real", 1: "deepfake"}
        self.model = None
        self.load_model()
        
    def load_model(self):
        """Load the pre-trained model"""
        try:
            model_path = os.path.join(settings.BASE_DIR, 'deepimage', 'utils', 'best_model.pth')
            
            if not os.path.exists(model_path):
                logger.warning("Model file not found. Using dummy model for testing.")
                self.create_dummy_model()
                return
            
            logger.info(f"Loading model from: {model_path}")
            
            # Load the checkpoint
            checkpoint = torch.load(model_path, map_location=self.device)
            
            # Initialize model architecture
            resnet = resnet50(weights=None)
            num_ftrs = resnet.fc.in_features
            resnet.fc = nn.Linear(num_ftrs, 2)
            
            # Handle different save formats
            if 'model_state_dict' in checkpoint:
                resnet.load_state_dict(checkpoint['model_state_dict'])
            else:
                # Assume it's a direct state dict
                resnet.load_state_dict(checkpoint)
            
            model = ResNet(resnet)
            model.eval()
            self.model = model.to(self.device)
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.create_dummy_model()
    
    def create_dummy_model(self):
        """Create a dummy model for testing"""
        logger.info("Creating dummy model for testing")
        resnet = resnet50(weights='IMAGENET1K_V2')
        num_ftrs = resnet.fc.in_features
        resnet.fc = nn.Linear(num_ftrs, 2)
        self.model = ResNet(resnet)
        self.model.eval()
        self.model = self.model.to(self.device)
    
    def get_transform(self):
        """Define image transformations"""
        return transforms.Compose([
            transforms.ToPILImage(),
            transforms.ToTensor(),
            transforms.Resize((224, 224)),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def predict(self, image_path):
        """Make prediction on a single image"""
        if self.model is None:
            return {'error': 'Model not loaded'}
        
        try:
            # Load and preprocess image
            img = Image.open(image_path).convert("RGB")
            img = np.array(img)
            img = self.transform(img)
            img = img.unsqueeze(0)  # Add batch dimension
            
            # Move to device
            if torch.cuda.is_available():
                img = img.cuda()
            
            # Predict
            with torch.no_grad():
                output = self.model(img)
            
            # Debug output
            logger.info(f"Model output: {output.cpu().numpy()}")
            
            # Get results
            pred_index = output.argmax(1).item()
            confidence = round(output[0][pred_index].item() * 100, 2)
            label = self.index_label[pred_index]
            
            return {
                'label': label,
                'confidence': confidence,
                'is_deepfake': pred_index == 1,
                'raw_output': output.cpu().numpy().tolist()  # For debugging
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {'error': str(e)}

# Create detector instance
detector = DeepFakeDetector()