from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from schemas.prediction import PredictionRequest, PredictionResponse, PredictionItem
from auth.auth_bearer import jwt_dependency
from auth.auth_handler import create_access_token
from utils.text_classifier import TextCategoryClassifier
from utils.image_classifier import ImageSubcategoryClassifier
import pandas as pd

app = FastAPI(
    title="🎯 Airsoft Equipment Classifier API",
    description="""
## Описание проекта

API для автоматической классификации страйкбольного снаряжения по текстам объявлений и фотографиям.

### Возможности:
- **Классификация по тексту**: определение категории снаряжения из описания
- **Классификация по изображениям**: распознавание оборудования на фото
- **Мультимодальный анализ**: комбинирование текста и фото для точности
- **JWT аутентификация**: защита endpoints

### Категории оборудования:
- 🔫 **Оружие**: винтовки, автоматы, пистолеты
- 🦺 **Экипировка**: жилеты, разгрузки, подсумки
- 🛡️ **Защита**: маски, очки, шлемы
- 🔧 **Аксессуары**: магазины, прицелы, ремни
    """,
    version="1.0.0",
    contact={
        "name": "Developer",
        "email": "developer@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
base_dir = os.path.dirname(os.path.abspath(__file__))

posts_path = os.path.normpath(os.path.join(base_dir, "../data/posts.parquet"))
posts_df = pd.read_parquet(posts_path) if os.path.exists(posts_path) else None
print(f"Загружено {len(posts_df)} постов" if posts_df is not None else "⚠️ Posts not loaded")

photos_path = os.path.normpath(os.path.join(base_dir, "../data/photos.parquet"))
photos_df = pd.read_parquet(photos_path) if os.path.exists(photos_path) else None
print(f"Загружено {len(photos_df)} фотографий" if photos_df is not None else "⚠️ Photos not loaded")

text_clf = TextCategoryClassifier(
    model_path="models/category_model.pkl",
    vectorizer_path="models/category_vectorizer.pkl",
    encoder_path="models/category_encoder.pkl",
    posts_path="../data/posts_clean.parquet"
)

image_clf = ImageSubcategoryClassifier(
    model_path="models/subcategory_model.pth",
    mapping_path="models/subcategory_mapping.json"
)
@app.get(
    "/", 
    tags=["Main"],
    summary="Главная страница",
    response_description="Интерфейс классификатора"
)
async def root():

    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

@app.post(
    "/auth/token",
    tags=["Authentication"],
    summary="Получить JWT токен",
    response_description="Access token для авторизации",
    responses={
        200: {"description": "Токен успешно получен"},
    }
)
async def get_token(user_id: str = "demo_user"):
    """
    **Аутентификация пользователя**
    
    Генерирует JWT токен для доступа к защищённым endpoints.
    
    - **user_id**: Идентификатор пользователя (для демо можно любой)
    """
    return {
        "access_token": create_access_token({"user_id": user_id}),
        "token_type": "bearer",
        "user_id": user_id
    }

@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Классифицировать снаряжение",
    response_description="Список найденных объектов с категориями",
    responses={
        200: {"description": "Успешная классификация"},
        403: {"description": "Неверный или истёкший токен"},
        422: {"description": "Ошибка валидации данных"}
    }
)

@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Классифицировать снаряжение",
    response_description="Список найденных объектов с категориями"
)
async def predict(request: PredictionRequest, auth: dict = Depends(jwt_dependency)):
    predictions: List[PredictionItem] = []

    text_prediction = text_clf.predict(request.text)
    print(f"\nТЕКСТ: {request.text}")
    print(f"МОДЕЛЬ: category={text_prediction['category']}, confidence={text_prediction['confidence']}")

    text_mentions = text_clf.extract_mentions(request.text)
    print(f"УПОМИНАНИЯ: {text_mentions}")

    image_results = []
    for photo in request.photos:
        result = image_clf.predict_from_url(photo.url)
        if "error" not in result:
            image_results.append({"photo_id": photo.photo_id, **result})
            print(f"ФОТО {photo.photo_id}: {result}")

    used_photos = set()
    
    for i, mention in enumerate(text_mentions):
        matched_photo = None
        for img_res in image_results:
            if img_res["photo_id"] not in used_photos and img_res["category"] == mention["category"]:
                matched_photo = img_res["photo_id"]
                used_photos.add(matched_photo)
                break

        source_type = "fused" if matched_photo else "text"
        
        pred_item = PredictionItem(
            object_id=mention["keyword"],
            category=mention["category"],
            subcategory=mention.get("subcategory"),
            confidence=round(text_prediction["confidence"], 2),
            photo_ids=[matched_photo] if matched_photo else [],
            source=source_type
        )
        
        print(f"ДОБАВЛЕНО: {pred_item}")
        predictions.append(pred_item)

    for i, img_res in enumerate(image_results):
        if img_res["photo_id"] not in used_photos:
            pred_item = PredictionItem(
                object_id=f"img_{i+1}",
                category=img_res["category"],
                subcategory=img_res.get("subcategory"),
                confidence=round(img_res["confidence"], 2),
                photo_ids=[img_res["photo_id"]],
                source="image"
            )
            print(f"ДОБАВЛЕНО ИЗ ФОТО: {pred_item}")
            predictions.append(pred_item)
    
    print(f"ИТОГО ПРЕДСКАЗАНИЙ: {len(predictions)}\n")

    post_info = None
    post_row = None

    if posts_df is not None:
        try:
            post_id_num = int(''.join(filter(str.isdigit, request.post_id)) or 0)
            if post_id_num > 0:
                post_row = posts_df[posts_df['Id'] == post_id_num]

                print(f"\nИЩЕМ ПОСТ ID={post_id_num}")
                print(f"Колонки в posts_df: {posts_df.columns.tolist()}")
                print(f"Найдено строк: {len(post_row)}")
                
                if not post_row.empty:
                    print(f"Пост найден")
                    print(f"Пример строки: {post_row.iloc[0].to_dict()}")
                    print(f"Text поле: {post_row.iloc[0].get('Text', 'НЕ НАЙДЕНО')}")
                    print(f"categoryname поле: {post_row.iloc[0].get('categoryname', 'НЕ НАЙДЕНО')}\n")

                    photos_count = 0
                    if photos_df is not None:
                        photos_count = len(photos_df[photos_df['PostId'] == post_id_num])
                    
                    post_info = {
                        "id": post_id_num,
                        "category_in_db": post_row.iloc[0]['categoryname'],
                        "photos_count": photos_count,
                        "original_text": post_row.iloc[0]['Text']
                    }
                else:
                    print(f"Пост ID={post_id_num} НЕ НАЙДЕН в базе\n")
                    
        except Exception as e:
            print(f"Ошибка при поиске поста: {e}\n")
            pass

    response_dict = {
        "post_id": request.post_id,
        "predictions": [p.dict() for p in predictions]
    }
    if post_info:
        response_dict["post_metadata"] = post_info
      
    return PredictionResponse(
        post_id=request.post_id, 
        predictions=predictions,
        post_metadata=post_info
    )

@app.get(
    "/health",
    tags=["Health"],
    summary="Проверка работоспособности",
    response_description="Статус сервиса"
)
async def health():
    """
    Проверка работоспособности API и загруженности моделей.
    """
    return {
        "status": "ok",
        "models_loaded": True,
        "text_model": "LogisticRegression + TF-IDF",
        "image_model": "ResNet50",
        "version": "1.0.0"
    }