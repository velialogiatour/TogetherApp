import pandas as pd
import numpy as np
import joblib
import json
from sklearn.linear_model import LogisticRegression
from pathlib import Path

# === Категориальные признаки ===
categorical_mapping = {
    "gender": {"Мужчина": 0, "Женщина": 1, "Другое": 2},
    "country": {
        "Россия": 0, "Казахстан": 1, "Украина": 2, "Беларусь": 3, "Узбекистан": 4,
        "Киргизия": 5, "Армения": 6, "Грузия": 7, "Азербайджан": 8, "Молдова": 9,
        "Таджикистан": 10, "Другие": 11
    },
    "city": {
        "Москва": 0, "Санкт-Петербург": 1, "Казань": 2, "Новосибирск": 3, "Екатеринбург": 4,
        "Минск": 5, "Алматы": 6, "Бишкек": 7, "Киев": 8, "Харьков": 9, "Ташкент": 10,
        "Ереван": 11, "Баку": 12, "Тбилиси": 13, "Кишинёв": 14, "Астана": 15, "Другой": 99
    },
    "zodiac_sign": {
        "Овен": 0, "Телец": 1, "Близнецы": 2, "Рак": 3, "Лев": 4, "Дева": 5,
        "Весы": 6, "Скорпион": 7, "Стрелец": 8, "Козерог": 9, "Водолей": 10, "Рыбы": 11
    }
}

fields = ['gender', 'country', 'city', 'zodiac_sign', 'age', 'height']

def random_user():
    return {
        "gender": np.random.choice(list(categorical_mapping["gender"].keys())),
        "country": np.random.choice(list(categorical_mapping["country"].keys())),
        "city": np.random.choice(list(categorical_mapping["city"].keys())),
        "zodiac_sign": np.random.choice(list(categorical_mapping["zodiac_sign"].keys())),
        "age": np.random.randint(18, 60),
        "height": np.random.randint(150, 200)
    }

# === Генерация обучающей выборки ===
X_rows = []
y = []

for _ in range(1000):
    u1 = random_user()
    u2 = random_user()
    row = {}

    for f in fields:
        val1 = categorical_mapping[f].get(u1[f], -1) if f in categorical_mapping else u1[f]
        val2 = categorical_mapping[f].get(u2[f], -1) if f in categorical_mapping else u2[f]
        row[f"user1_{f}"] = val1
        row[f"user2_{f}"] = val2

    X_rows.append(row)
    age_diff = abs(u1["age"] - u2["age"])
    match_prob = 1.0 - age_diff / 50.0
    y.append(1 if np.random.rand() < match_prob else 0)

X = pd.DataFrame(X_rows)

# === Обучение ===
model = LogisticRegression(max_iter=1000)
model.fit(X, y)

# === Сохраняем ===
Path("dataset").mkdir(parents=True, exist_ok=True)
Path("ml_model").mkdir(parents=True, exist_ok=True)

X.to_csv("dataset/train_data.csv", index=False)
joblib.dump(model, "ml_model/matching_model.joblib")

with open("ml_model/categorical_mapping.json", "w", encoding="utf-8") as f:
    json.dump(categorical_mapping, f, ensure_ascii=False, indent=2)

print("[✓] Модель обучена. Признаки:", list(model.feature_names_in_))
