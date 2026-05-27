from pydantic import BaseModel, Field
from typing import List, Optional

class PhotoInput(BaseModel):
    photo_id: str
    url: str

class PredictionRequest(BaseModel):
    post_id: str
    text: str
    photos: List[PhotoInput] = Field(default_factory=list)

class PredictionItem(BaseModel):
    object_id: str
    category: str
    subcategory: Optional[str] = None
    confidence: float = Field(ge=0, le=1)
    photo_ids: List[str]
    source: str = "text"

class PredictionResponse(BaseModel):
    post_id: str
    predictions: List[PredictionItem]

from pydantic import BaseModel, Field
from typing import List, Optional

class PhotoInput(BaseModel):
    photo_id: str = Field(..., description="Уникальный идентификатор фотографии", example="photo_001")
    url: str = Field(..., description="URL или путь к изображению", example="https://example.com/photo.jpg")

class PredictionRequest(BaseModel):
    post_id: str = Field(..., description="Идентификатор поста/объявления", example="post_12345")
    text: str = Field(..., description="Текст объявления о продаже снаряжения", 
                      example="Продаю новую страйкбольную винтовку ASG и тактический жилет")
    photos: List[PhotoInput] = Field(default_factory=list, description="Список фотографий снаряжения")

class PredictionItem(BaseModel):
    object_id: str = Field(..., description="Уникальный идентификатор объекта", example="obj_1")
    category: str = Field(..., description="Категория снаряжения", example="Оружие")
    subcategory: Optional[str] = Field(None, description="Подкатегория (если определена)", example="Винтовки")
    confidence: float = Field(..., ge=0, le=1, description="Уверенность модели (0-1)", example=0.92)
    photo_ids: List[str] = Field(default_factory=list, description="Связанные фотографии", example=["photo_001"])
    source: str = Field(default="text", description="Источник определения: text, image, или fused", example="text")

class PredictionResponse(BaseModel):
    post_id: str = Field(..., description="Идентификатор обработанного поста")
    predictions: List[PredictionItem] = Field(..., description="Список найденных объектов снаряжения")
    post_metadata: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "post_id": "post_12345",
                "predictions": [
                    {
                        "object_id": "obj_1",
                        "category": "Оружие",
                        "subcategory": "Винтовки",
                        "confidence": 0.95,
                        "photo_ids": ["photo_001"],
                        "source": "fused"
                    }
                ]
            }
        }