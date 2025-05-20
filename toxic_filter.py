import os
import joblib
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

MODEL_DIR = "ml_model"

MODEL_PATH = os.path.join(MODEL_DIR, "toxicity_filter_model.joblib")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

def is_offensive(text, threshold=0.7):
    """
    Возвращает True, если сообщение токсично (с вероятностью выше threshold).
    """
    if not text.strip():
        return False

    vector = vectorizer.transform([text])
    prob = model.predict_proba(vector)[0][1]
    return prob >= threshold
