import os
import joblib
import re
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

MODEL_DIR = "ml_model"

MODEL_PATH = os.path.join(MODEL_DIR, "toxicity_filter_model_improved.joblib")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer_improved.joblib")

# Загрузка модели и векторизатора
model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

# Список стоп-слов, которые всегда считаются токсичными
HARDCODED_TOXIC_WORDS = {
    "еблан", "чмошник", "лох", "урод", "уродливая", "скинь нюдсы", "педальный", "мудак", "гандон", "придурками",
    "тупица", "дегенерат", "тварь", "тупая","ублюдок", "долбаеб", "тварь", "сука","иди нахуй", "пошла нахуй", "шлюха",
    "сдохни", "пошел на хуй", "придурок", "мразь", "ебанный", "ебаный","ботан","тупой", "уродливая", "хуевая", "стрёмная"
}

def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^а-яa-z0-9ё\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def contains_explicit_toxicity(text):
    words = text.lower().split()
    return any(word in HARDCODED_TOXIC_WORDS for word in words)

def is_offensive(text, threshold=0.6):
    """
    Возвращает True, если сообщение токсично (по вероятности модели или по словарю).
    """
    if not text.strip():
        return False

    if contains_explicit_toxicity(text):
        return True

    text_clean = preprocess(text)
    vector = vectorizer.transform([text_clean])
    prob = model.predict_proba(vector)[0][1]
    return prob >= threshold
