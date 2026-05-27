import pandas as pd
import os

class DataLoader:
    def __init__(self, posts_path: str = None):
        self.posts = None
        if posts_path and os.path.exists(posts_path):
            self.posts = pd.read_parquet(posts_path)
            print(f"Загружено {len(self.posts)} постов из {posts_path}")
    
    def get_category_mapping(self):
        if self.posts is None:
            return {}

        mapping = {}
        for _, row in self.posts.iterrows():
            text = str(row.get('Text', '')).lower()
            category = row.get('categoryname', '')

            words = text.split()
            for word in words:
                if len(word) > 3:
                    if word not in mapping:
                        mapping[word] = {}
                    if category not in mapping[word]:
                        mapping[word][category] = 0
                    mapping[word][category] += 1

        result = {}
        for word, categories in mapping.items():
            result[word] = max(categories, key=categories.get)
        
        return result
    
    def get_subcategory_examples(self, category: str):
        if self.posts is None:
            return []
        
        category_posts = self.posts[self.posts.get('categoryname') == category]
        return category_posts['Text'].head(10).tolist()