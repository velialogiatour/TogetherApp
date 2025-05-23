import pandas as pd
import joblib
import re

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# 1. Загрузка и подготовка датасета
df = pd.read_csv("final_augmented_toxicity_dataset.csv")  # Датасет должен содержать 'text' и 'label' (0 — норм, 1 — токсично)

def preprocess(text):
    """Очистка текста: удаление спецсимволов, приведение к нижнему регистру."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text

df["clean_text"] = df["text"].apply(preprocess)

# 2. Разделение на обучающую и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(
    df["clean_text"], df["label"], test_size=0.2, random_state=42
)

# 3. TF-IDF векторизация
vectorizer = TfidfVectorizer(max_features=5000)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# 4. Обучение модели логистической регрессии
model = LogisticRegression()
model.fit(X_train_tfidf, y_train)

# 5. Оценка качества
y_pred = model.predict(X_test_tfidf)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# 6. Сохранение модели и векторизатора
joblib.dump(model, "toxicity_filter_model.joblib")
joblib.dump(vectorizer, "vectorizer.joblib")
