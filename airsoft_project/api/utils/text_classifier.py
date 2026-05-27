import joblib
import os
import re

class TextCategoryClassifier:
    def __init__(self, model_path: str, vectorizer_path: str, encoder_path: str, posts_path: str = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        abs_model_path = os.path.normpath(os.path.join(base_dir, model_path))
        abs_vectorizer_path = os.path.normpath(os.path.join(base_dir, vectorizer_path))
        abs_encoder_path = os.path.normpath(os.path.join(base_dir, encoder_path))

        self.model = joblib.load(abs_model_path)
        self.vectorizer = joblib.load(abs_vectorizer_path)
        self.encoder = joblib.load(abs_encoder_path)

        self.category_mapping = {}
        if posts_path:
            try:
                abs_posts_path = os.path.normpath(os.path.join(base_dir, posts_path))
                import pandas as pd
                if os.path.exists(abs_posts_path):
                    posts_df = pd.read_parquet(abs_posts_path)
                    for _, row in posts_df.head(1000).iterrows():
                        text = str(row.get('Text', '')).lower()
                        category = row.get('categoryname', '')
                        words = re.findall(r'[а-яёa-z]{4,}', text)
                        for word in words:
                            if word not in self.category_mapping:
                                self.category_mapping[word] = category
                    print(f"Загружен маппинг из {len(self.category_mapping)} слов")
            except Exception as e:
                print(f"Не удалось загрузить данные: {e}")

        self.keywords = {
            "Оружие": {
                "винтовк": "Винтовки", "автомат": "Автоматы", "пистолет": "Пистолеты",
                "дробовик": "Дробовики", "asg": "Винтовки", "cyma": "Винтовки",
                "ak": "Автоматы", "m4": "Винтовки", "akm": "Автоматы", "ak74": "Автоматы"
            },
            "Экипировка": {
                "жилет": "Тактические жилеты", "разгрузк": "Разгрузочные системы",
                "бронежилет": "Бронежилеты", "подсумок": "Подсумки", "подсумк": "Подсумки",
                "рюкзак": "Рюкзаки", "ковер": "Ковры", "коврик": "Ковры", "панцир": "Бронежилеты"
            },
            "Защита": {
                "шлем": "Шлемы", "очк": "Защитные очки", "маск": "Маски",
                "наколенник": "Наколенники", "перчатк": "Перчатки", "броник": "Бронежилеты"
            },
            "Аксессуары": {
                "магазин": "Магазины", "прицел": "Прицелы", "фонар": "Фонари",
                "ремен": "Ремни", "глушител": "Глушители", "ствол": "Стволы",
                "баллист": "Защита", "пакет": "Аксессуары", "креплени": "Крепления"
            }
        }
    
    def extract_mentions(self, text: str) -> list:
        text_lower = text.lower()
        mentions = []
        found_keywords = set()

        for category, subcategories in self.keywords.items():
            for keyword_root, subcategory in subcategories.items():
                if keyword_root in text_lower and keyword_root not in found_keywords:
                    match = re.search(r'\w*' + re.escape(keyword_root) + r'\w*', text_lower)
                    found_word = match.group(0) if match else keyword_root
                    
                    mentions.append({
                        "category": category,
                        "keyword": found_word,
                        "subcategory": subcategory
                    })
                    found_keywords.add(keyword_root)

        if self.category_mapping:
            words = re.findall(r'[а-яёa-z]{4,}', text_lower)
            for word in words:
                if word in self.category_mapping and word not in found_keywords:
                    mentions.append({
                        "category": self.category_mapping[word],
                        "keyword": word,
                        "subcategory": None
                    })
                    found_keywords.add(word)
        
        return mentions

    def predict(self, text: str) -> dict:
        vector = self.vectorizer.transform([text])
        proba = self.model.predict_proba(vector)[0]
        pred_idx = self.model.predict(vector)[0]
        
        return {
            "category": self.encoder.inverse_transform([pred_idx])[0],
            "confidence": float(max(proba)),
            "all_probabilities": {
                cat: float(p) for cat, p in zip(self.encoder.classes_, proba)
            }
        }