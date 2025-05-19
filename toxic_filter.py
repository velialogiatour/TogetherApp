import os
import joblib
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


MODEL_PATH = os.path.join("ml_model", "toxicity_filter_model.joblib")

# Загружаем модель один раз при импорте модуля
model = joblib.load(MODEL_PATH)

def is_offensive(text, threshold=0.7):
    """
    Возвращает True, если сообщение токсично (с вероятностью выше threshold).
    """
    if not text.strip():
        return False

    prob = model.predict_proba([text])[0][1]
    return prob >= threshold
