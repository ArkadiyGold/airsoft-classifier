import torch
import torchvision.transforms as transforms
from PIL import Image
import requests
from io import BytesIO
import json
import os

class ImageSubcategoryClassifier:
    def __init__(self, model_path: str, mapping_path: str):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        abs_model_path = os.path.normpath(os.path.join(base_dir, model_path))
        abs_mapping_path = os.path.normpath(os.path.join(base_dir, mapping_path))

        with open(abs_mapping_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        self.idx_to_subcategory = {int(k): v for k, v in mapping['idx_to_subcategory'].items()}
        self.subcategories = mapping['subcategories']

        from torchvision import models
        import torch.nn as nn
        self.model = models.resnet50(weights=None)
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, len(self.subcategories))

        if os.path.exists(abs_model_path):
            self.model.load_state_dict(torch.load(abs_model_path, map_location=self.device, weights_only=False))
        else:
            print(f"Warning: Model file not found: {abs_model_path}")
        
        self.model.to(self.device).eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    
    def predict_from_url(self, image_url: str) -> dict:
        try:
            response = requests.get(image_url, timeout=10)
            image = Image.open(BytesIO(response.content)).convert('RGB')
        except Exception as e:
            return {"error": "Failed to load image"}
        
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            output = torch.softmax(self.model(input_tensor), dim=1)
            confidence, predicted = torch.max(output, 1)
        
        subcategory = self.idx_to_subcategory[predicted.item()]

        category_mapping = {
            "Винтовки": "Оружие", "Автоматы": "Оружие", "Пистолеты": "Оружие",
            "Тактические жилеты": "Экипировка", "Разгрузки": "Экипировка",
            "Маски": "Защита", "Очки": "Защита",
            "Магазины": "Аксессуары", "Прицелы": "Аксессуары"
        }
        
        return {
            "category": category_mapping.get(subcategory, "Другое"),
            "subcategory": subcategory,
            "confidence": float(confidence.item())
        }