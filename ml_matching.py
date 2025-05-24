import joblib
import json
import numpy as np

# Пути к модели и маппингу
MODEL_PATH = "ml_model/matching_model.joblib"
MAPPING_PATH = "ml_model/categorical_mapping.json"

# Загрузка модели и признаков
model = joblib.load(MODEL_PATH)
with open(MAPPING_PATH, "r", encoding="utf-8") as f:
    categorical_mapping = json.load(f)

# Список признаков, по которым модель обучалась
feature_order = model.feature_names_in_

def predict_match(user1, user2):
    """
    user1 и user2 — словари с полями анкеты (age, gender, country и т.п.)
    Возвращает вероятность мэтча от 0.0 до 1.0
    """
    combined = {}

    for side, user in zip(["user1", "user2"], [user1, user2]):
        for field, value in user.items():
            key = f"{side}_{field}"

            if field in categorical_mapping:
                mapped_value = categorical_mapping[field].get(value, -1)
                if mapped_value == -1:
                    print(f"[WARN] Неизвестное значение для '{field}': '{value}'")
                combined[key] = mapped_value
            else:
                try:
                    combined[key] = float(value)
                except (ValueError, TypeError):
                    combined[key] = 0.0

    # Приведение признаков к нужному порядку
    X = np.array([[combined.get(feat, 0) for feat in feature_order]])
    prob = model.predict_proba(X)[0][1]

    return prob
