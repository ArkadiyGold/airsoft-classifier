# Airsoft Equipment Classifier API

API для автоматической классификации страйкбольного снаряжения с использованием машинного обучения.

## Описание

Проект представляет собой веб-API для анализа объявлений о продаже страйкбольного оборудования и автоматического определения:
- Категории снаряжения (Оружие, Экипировка, Защита, Аксессуары)
- Подкатегории (Винтовки, Тактические жилеты, Шлемы и т.д.)
- Уверенности модели в процентах

Анализ производится по тексту объявления, фотографиям и комбинированному (мультимодальному) анализу.

## Возможности

- Автоматическая классификация текста объявлений
- Распознавание объектов на фотографиях
- JWT аутентификация для защиты API
- Веб-интерфейс для удобной работы
- Интеграция с базой данных
- Публичный доступ через Cloudflare Tunnel
- Swagger документация для разработчиков

## Архитектура

┌─────────────────────────────────────┐
│ Frontend (HTML/CSS/JS)              │
│ Красивый веб-интерфейс              │
└────────────┬────────────────────────┘
│ HTTP/JSON
▼
┌─────────────────────────────────────┐
│ FastAPI Backend                     │
│ ┌──────────────────────────────┐    │
│ │ JWT Authentication           │    │
│ └──────────────────────────────┘    │
│ ┌──────────┐ ┌──────────────┐       │
│ │ Text     │ │ Image        │       │
│ │ Model    │ │ Model        │       │
│ │(sklearn) │ │ (ResNet50)   │       │
│ └──────────┘ └──────────────┘       │
└─────────────────────────────────────┘
│
▼
┌─────────────────────────────────────┐
│ Data Sources                        │
│ • posts.parquet (66,370 записей)    │
│ • photos.parquet (95,100 записей)   │
│ • subcategory_images/               │
└─────────────────────────────────────┘

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/ArkadiyGold/airsoft-classifier.git
cd airsoft_project
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Скачивание моделей и данных

Модели и данные вынесены на Google Drive из-за большого размера:

[Скачать модели и данные (Google Drive)](https://drive.google.com/drive/folders/1_-3PTM7mZpVBRCyajVVNhG2d3sWBc4hz?usp=sharing)

Распакуйте файлы в структуру проекта:
```
airsoft_project/
├── api/models/              # Модели
│   ├── category_model.pkl
│   ├── category_vectorizer.pkl
│   ├── category_encoder.pkl
│   ├── subcategory_model.pth
│   └── subcategory_mapping.json
└── data/                    # Данные
    ├── posts.parquet
    └── photos.parquet
```

### 4. Запуск API

```bash
cd api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Быстрый старт

### Локальный запуск

1. Откройте браузер: http://127.0.0.1:8000
2. Введите текст объявления
3. Нажмите "Классифицировать"
4. Получите результаты с категориями

### Публичный доступ (Cloudflare Tunnel)

```bash
cloudflared tunnel --url http://localhost:8000
```

Публичный URL: [Добавить ссылку](https://YOUR-CLOUDFLARE-URL.trycloudflare.com)

## API Документация

### Аутентификация

**POST** `/auth/token`

Получение JWT токена для доступа к API.

**Запрос:**
```bash
curl -X POST "http://127.0.0.1:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo_user"}'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "demo_user"
}
```

### Классификация

**POST** `/api/v1/predict`

Анализ объявления и определение категорий снаряжения.

**Запрос:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/predict" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": "354",
    "text": "Продаю новую страйкбольную винтовку ASG и тактический жилет",
    "photos": []
  }'
```

**Ответ:**
```json
{
  "post_id": "354",
  "predictions": [
    {
      "object_id": "винтовка",
      "category": "Оружие",
      "subcategory": "Винтовки",
      "confidence": 0.92,
      "photo_ids": [],
      "source": "text"
    },
    {
      "object_id": "жилет",
      "category": "Экипировка",
      "subcategory": "Тактические жилеты",
      "confidence": 0.88,
      "photo_ids": [],
      "source": "text"
    }
  ],
  "post_metadata": {
    "id": 354,
    "category_in_db": "Снаряжение и защита",
    "photos_count": 3,
    "original_text": "Шлем оп скор , ковер и 2 пары очков..."
  }
}
```

### Health Check

**GET** `/health`

Проверка работоспособности API.

```bash
curl http://127.0.0.1:8000/health
```

### Swagger UI

Полная интерактивная документация: http://127.0.0.1:8000/docs

## Примеры использования

### Пример 1: Классификация оружия

**Вход:** "Продам автомат АК-74, состояние идеальное"

**Результат:**
- Категория: Оружие (97%)
- Подкатегория: Автоматы
- Источник: текст

### Пример 2: Классификация экипировки

**Вход:** "Продаю тактический жилет и разгрузку"

**Результат:**
- Экипировка (85%) - Тактические жилеты
- Экипировка (82%) - Разгрузочные системы

## Технологии

| Компонент        | Технология                | Версия  |
|------------------|---------------------------|---------|
| Backend          | FastAPI                   | 0.109.0 |
| ML (текст)       | scikit-learn + TF-IDF     | 1.3.0   |
| ML (изображения) | PyTorch + ResNet50        | 2.1.0   |
| Аутентификация   | JWT (python-jose)         | 3.3.0   |
| Frontend         | HTML5 + CSS3 + Vanilla JS | -       |
| Туннель          | Cloudflare Tunnel         | latest  |
| Данные           | Apache Parquet            | -       |

## Датасет

Проект использует реальные данные с площадок продажи страйкбольного снаряжения:

- **posts.parquet**: 66,370 объявлений
  - Колонки: Id, CategoryId, categoryname, Text
  
- **photos.parquet**: 95,100 фотографий
  - Колонки: Id, Url, DataSource, PostId

## Структура проекта

```
airsoft_project/
├── README.md
├── requirements.txt
├── .gitignore
├── api/
│   ├── main.py
│   ├── static/index.html
│   ├── models/
│   ├── auth/
│   ├── schemas/
│   └── utils/
├── data/
│   ├── posts.parquet
│   └── photos.parquet
└── google_colab/
    ├── 01_eda_and_prep.ipynb
    ├── 02_train_category_model.ipynb
    └── 03_train_subcategory_model.ipynb
```

## Ссылки

- **Модели и данные:** [Google Drive](https://drive.google.com/drive/folders/1_-3PTM7mZpVBRCyajVVNhG2d3sWBc4hz?usp=sharing)
- **Swagger документация:** /docs (после запуска)
- **Публичное демо:** [Cloudflare URL](https://YOUR-URL.trycloudflare.com)

## Автор

**Аркадий Ванишев**  
Студент Dk
Email: [твой@email.com]  
GitHub: [@ArkadiyGold](https://github.com/ArkadiyGold)
